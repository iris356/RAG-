from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rag_app.conversations.store import (
    DEFAULT_SESSION_TITLE,
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    SESSION_TITLE_MAX_LENGTH,
    ConversationStore,
    generate_title_from_first_message,
    get_conversation_database_path,
    initialize_conversation_store,
)
from rag_app.core.exceptions import ConversationStoreError


def test_initialize_conversation_store_creates_database_and_tables(tmp_path: Path) -> None:
    sqlite_dir = tmp_path / "sqlite"

    database_path = initialize_conversation_store(sqlite_dir)

    assert database_path == get_conversation_database_path(sqlite_dir)
    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
    assert "conversation_sessions" in tables
    assert "conversation_messages" in tables


def test_create_session_supports_default_and_explicit_titles(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "session-2"])

    default_session = store.create_session()
    titled_session = store.create_session("  Research notes  ")

    assert default_session.title == DEFAULT_SESSION_TITLE
    assert titled_session.title == "Research notes"
    assert [session.session_id for session in store.list_sessions()] == [
        "session-2",
        "session-1",
    ]


def test_first_user_message_generates_session_title(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1"])
    message = "  How do I use\nmodule six for conversation history and later RAG?  "

    session = store.get_or_create_session_for_first_user_message(message)

    assert session.title == "How do I use module six for conversation"
    assert len(session.title) == SESSION_TITLE_MAX_LENGTH


def test_generate_title_rejects_empty_content() -> None:
    with pytest.raises(ConversationStoreError, match="content"):
        generate_title_from_first_message(" \n\t ")


def test_add_messages_returns_chronological_history(tmp_path: Path) -> None:
    store = make_store(
        tmp_path,
        ids=["session-1", "message-1", "message-2", "message-3"],
    )
    session = store.create_session("Chat")

    user_message = store.add_message(session.session_id, ROLE_USER, " hello ")
    assistant_message = store.add_message(session.session_id, ROLE_ASSISTANT, "Hi there")
    system_message = store.add_message(session.session_id, ROLE_SYSTEM, "Keep concise")

    messages = store.get_messages(session.session_id)

    assert user_message.content == "hello"
    assert [message.message_id for message in messages] == [
        "message-1",
        "message-2",
        "message-3",
    ]
    assert [message.role for message in messages] == [
        ROLE_USER,
        ROLE_ASSISTANT,
        ROLE_SYSTEM,
    ]
    assert messages[1] == assistant_message
    assert store.get_conversation(session.session_id).messages == messages


def test_list_sessions_uses_latest_updated_at(tmp_path: Path) -> None:
    store = make_store(
        tmp_path,
        ids=["session-1", "session-2", "message-1"],
        times=[
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
            datetime(2026, 1, 3, tzinfo=UTC),
        ],
    )
    first = store.create_session("First")
    store.create_session("Second")

    store.add_message(first.session_id, ROLE_USER, "Bring first to the top")

    assert [session.session_id for session in store.list_sessions()] == [
        "session-1",
        "session-2",
    ]
    updated_first = store.get_session(first.session_id)
    assert updated_first is not None
    assert updated_first.updated_at == "2026-01-03T00:00:00+00:00"


def test_rename_session_updates_title_and_updated_at(tmp_path: Path) -> None:
    store = make_store(
        tmp_path,
        ids=["session-1"],
        times=[
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        ],
    )
    session = store.create_session("Before")

    renamed = store.rename_session(session.session_id, "  After rename  ")

    assert renamed.title == "After rename"
    assert renamed.updated_at == "2026-01-02T00:00:00+00:00"


def test_empty_title_is_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1"])
    session = store.create_session("Valid")

    with pytest.raises(ConversationStoreError, match="title"):
        store.rename_session(session.session_id, "  ")


def test_delete_session_removes_session_and_messages_only_from_sqlite(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1", "message-2"])
    session = store.create_session("Delete me")
    store.add_message(session.session_id, ROLE_USER, "Question")
    store.add_message(session.session_id, ROLE_ASSISTANT, "Answer")

    deleted_messages = store.delete_session(session.session_id)

    assert deleted_messages == 2
    assert store.get_session(session.session_id) is None
    with pytest.raises(ConversationStoreError, match="Conversation not found"):
        store.get_messages(session.session_id)


def test_missing_session_operations_raise_clear_errors(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    with pytest.raises(ConversationStoreError, match="Conversation not found"):
        store.get_messages("missing")
    with pytest.raises(ConversationStoreError, match="Conversation not found"):
        store.add_message("missing", ROLE_USER, "hello")
    with pytest.raises(ConversationStoreError, match="Conversation not found"):
        store.rename_session("missing", "title")
    with pytest.raises(ConversationStoreError, match="Conversation not found"):
        store.delete_session("missing")


def test_invalid_role_and_empty_content_are_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1"])
    session = store.create_session("Chat")

    with pytest.raises(ConversationStoreError, match="Unsupported"):
        store.add_message(session.session_id, "tool", "hello")
    with pytest.raises(ConversationStoreError, match="content"):
        store.add_message(session.session_id, ROLE_USER, "  ")


def make_store(
    tmp_path: Path,
    *,
    ids: list[str] | None = None,
    times: list[datetime] | None = None,
) -> ConversationStore:
    id_values = list(ids or ["session-1"])
    time_values = list(times or [datetime(2026, 1, 1, tzinfo=UTC)])

    def next_id() -> str:
        if len(id_values) == 1:
            return id_values[0]
        return id_values.pop(0)

    def next_time() -> datetime:
        if len(time_values) == 1:
            current = time_values[0]
            time_values[0] = current + timedelta(seconds=1)
            return current
        return time_values.pop(0)

    return ConversationStore(
        sqlite_dir=tmp_path / "sqlite",
        id_factory=next_id,
        now_factory=next_time,
    )
