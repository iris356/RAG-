from __future__ import annotations

from pathlib import Path

from rag_app.app import (
    _conversation_select_index,
    _conversation_table_row,
    _document_table_row,
    _format_conversation_option,
    _format_document_option,
    _format_duplicate_document,
    _selected_session_id,
)
from rag_app.conversations.store import ROLE_USER, ConversationSession, ConversationStore
from rag_app.documents.store import (
    INDEX_STATUS_INDEXED,
    PARSE_STATUS_PARSED,
    STATUS_DUPLICATE,
    STATUS_UPLOADED,
    DocumentRecord,
)


def test_selected_session_falls_back_to_first_session() -> None:
    sessions = [
        make_session("session-1", "First"),
        make_session("session-2", "Second"),
    ]

    assert _selected_session_id(sessions, "session-2") == "session-2"
    assert _selected_session_id(sessions, "missing") == "session-1"
    assert _selected_session_id(sessions, None) == "session-1"
    assert _selected_session_id([], "session-1") is None


def test_conversation_select_index_uses_selected_session_or_first() -> None:
    sessions = [
        make_session("session-1", "First"),
        make_session("session-2", "Second"),
    ]

    assert _conversation_select_index(sessions, "session-2") == 1
    assert _conversation_select_index(sessions, "missing") == 0
    assert _conversation_select_index([], "missing") == 0


def test_conversation_option_formatting() -> None:
    sessions = [make_session("session-1", "Research")]

    assert _format_conversation_option("session-1", sessions) == "Research (session-1)"
    assert _format_conversation_option("missing", sessions) == "missing"


def test_conversation_table_row_includes_message_count(tmp_path: Path) -> None:
    store = ConversationStore(
        sqlite_dir=tmp_path,
        id_factory=next_value(["session-1", "message-1", "message-2"]),
    )
    session = store.create_session("Research")
    store.add_message(session.session_id, ROLE_USER, "First")
    store.add_message(session.session_id, ROLE_USER, "Second")

    row = _conversation_table_row(store, session)

    assert row["Session ID"] == "session-1"
    assert row["Title"] == "Research"
    assert row["Messages"] == 2


def test_document_option_and_duplicate_formatting() -> None:
    original = make_document("doc-1", "original.txt")
    duplicate = make_document(
        "doc-2",
        "copy.txt",
        status=STATUS_DUPLICATE,
        duplicate_of_document_id="doc-1",
    )
    documents = [duplicate, original]

    assert _format_document_option("doc-1", documents) == "original.txt (doc-1)"
    assert _format_document_option("missing", documents) == "missing"
    assert _format_duplicate_document(original, documents) == "No"
    assert _format_duplicate_document(duplicate, documents) == "Yes: original.txt (doc-1)"


def test_document_table_row_shows_duplicate_source() -> None:
    original = make_document("doc-1", "original.txt")
    duplicate = make_document(
        "doc-2",
        "copy.txt",
        status=STATUS_DUPLICATE,
        duplicate_of_document_id="doc-1",
    )

    row = _document_table_row(duplicate, [duplicate, original])

    assert row["Document ID"] == "doc-2"
    assert row["Status"] == STATUS_DUPLICATE
    assert row["Duplicate"] == "Yes: original.txt (doc-1)"


def make_session(session_id: str, title: str) -> ConversationSession:
    return ConversationSession(
        session_id=session_id,
        title=title,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def make_document(
    document_id: str,
    filename: str,
    *,
    status: str = STATUS_UPLOADED,
    duplicate_of_document_id: str | None = None,
) -> DocumentRecord:
    return DocumentRecord(
        document_id=document_id,
        original_filename=filename,
        stored_filename=f"{document_id}.txt",
        file_path=Path(f"/tmp/{document_id}.txt"),
        file_type="txt",
        file_size=10,
        file_md5=f"{document_id}-file-md5",
        text_md5=f"{document_id}-text-md5",
        duplicate_of_document_id=duplicate_of_document_id,
        status=status,
        parse_status=PARSE_STATUS_PARSED,
        index_status=INDEX_STATUS_INDEXED,
        chunk_count=2,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )


def next_value(values: list[str]):
    remaining = list(values)

    def _next_value() -> str:
        if len(remaining) == 1:
            return remaining[0]
        return remaining.pop(0)

    return _next_value
