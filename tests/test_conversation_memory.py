from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rag_app.conversations.memory import (
    ConversationMemoryService,
    build_conversation_memory_record,
    build_conversation_memory_vector_id,
)
from rag_app.conversations.store import (
    ROLE_ASSISTANT,
    ROLE_SYSTEM,
    ROLE_USER,
    ConversationStore,
)
from rag_app.core.exceptions import ConversationMemoryError, VectorStoreError
from rag_app.vectors.store import COLLECTION_CONVERSATION_MEMORY, VectorWriteResult


def test_build_conversation_memory_record_uses_stable_id_and_metadata(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1"])
    session = store.create_session("Chat")
    message = store.add_message(session.session_id, ROLE_USER, "Remember this")

    record = build_conversation_memory_record(message)

    assert record.id == "conversation:session-1:message:message-1"
    assert build_conversation_memory_vector_id(message) == record.id
    assert record.text == "Remember this"
    assert record.metadata == {
        "session_id": "session-1",
        "message_id": "message-1",
        "role": ROLE_USER,
        "created_at": "2026-01-01T00:00:01+00:00",
    }


def test_write_message_memory_uses_vector_store_entrypoint(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1"])
    session = store.create_session("Chat")
    message = store.add_message(session.session_id, ROLE_USER, "Question")
    vector_store = FakeVectorStore()
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=vector_store,
    )

    result = service.write_message_memory(message)

    assert result.ok is True
    assert result.total_messages == 1
    assert result.written_messages == 1
    assert vector_store.calls == [
        ("delete_by_ids", ["conversation:session-1:message:message-1"]),
        ("add_conversation_memories", ["conversation:session-1:message:message-1"]),
    ]
    assert vector_store.added_records[0].metadata["session_id"] == session.session_id
    assert vector_store.added_records[0].metadata["message_id"] == message.message_id


def test_write_message_memory_returns_vector_write_failure(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1"])
    session = store.create_session("Chat")
    message = store.add_message(session.session_id, ROLE_ASSISTANT, "Answer")
    failed_write = VectorWriteResult(
        ok=False,
        message="Vector batch 1 failed: embedding failed",
        total_texts=1,
        processed_texts=0,
        total_batches=1,
        processed_batches=0,
        failed_batch_index=1,
    )
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=FakeVectorStore(write_result=failed_write),
    )

    result = service.write_message_memory(message)

    assert result.ok is False
    assert result.message == failed_write.message
    assert result.vector_write_result == failed_write
    assert result.written_messages == 0


def test_rebuild_session_memories_replaces_existing_vectors(tmp_path: Path) -> None:
    store = make_store(
        tmp_path,
        ids=["session-1", "message-1", "message-2", "message-3"],
    )
    session = store.create_session("Chat")
    store.add_message(session.session_id, ROLE_USER, "Question")
    store.add_message(session.session_id, ROLE_ASSISTANT, "Answer")
    store.add_message(session.session_id, ROLE_SYSTEM, "Keep concise")
    vector_store = FakeVectorStore(deleted_vectors=7)
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=vector_store,
    )

    result = service.rebuild_session_memories(session.session_id)

    assert result.ok is True
    assert result.total_messages == 3
    assert result.written_messages == 3
    assert result.deleted_vectors == 7
    assert vector_store.calls == [
        ("delete_by_session_id", ["session-1"]),
        (
            "add_conversation_memories",
            [
                "conversation:session-1:message:message-1",
                "conversation:session-1:message:message-2",
                "conversation:session-1:message:message-3",
            ],
        ),
    ]
    assert [record.metadata["role"] for record in vector_store.added_records] == [
        ROLE_USER,
        ROLE_ASSISTANT,
        ROLE_SYSTEM,
    ]


def test_rebuild_empty_session_deletes_old_vectors_without_writing(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1"])
    session = store.create_session("Empty")
    vector_store = FakeVectorStore(deleted_vectors=2)
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=vector_store,
    )

    result = service.rebuild_session_memories(session.session_id)

    assert result.ok is True
    assert result.total_messages == 0
    assert result.deleted_vectors == 2
    assert result.vector_write_result is None
    assert vector_store.calls == [("delete_by_session_id", ["session-1"])]


def test_delete_session_with_memories_deletes_vectors_before_sqlite(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1", "message-2"])
    session = store.create_session("Delete me")
    store.add_message(session.session_id, ROLE_USER, "Question")
    store.add_message(session.session_id, ROLE_ASSISTANT, "Answer")
    vector_store = FakeVectorStore(deleted_vectors=2)
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=vector_store,
    )

    result = service.delete_session_with_memories(session.session_id)

    assert result.ok is True
    assert result.deleted_vectors == 2
    assert result.deleted_sqlite_messages == 2
    assert store.get_session(session.session_id) is None
    assert vector_store.calls == [("delete_by_session_id", ["session-1"])]


def test_delete_session_keeps_sqlite_when_memory_delete_fails(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["session-1", "message-1"])
    session = store.create_session("Keep me")
    store.add_message(session.session_id, ROLE_USER, "Question")
    vector_store = FakeVectorStore(fail_delete_session=True)
    service = ConversationMemoryService(
        conversation_store=store,
        vector_store=vector_store,
    )

    with pytest.raises(ConversationMemoryError, match="Failed to delete conversation memories"):
        service.delete_session_with_memories(session.session_id)

    assert store.get_session(session.session_id) is not None
    assert len(store.get_messages(session.session_id)) == 1


def test_missing_session_memory_operations_raise_clear_error(tmp_path: Path) -> None:
    service = ConversationMemoryService(
        conversation_store=make_store(tmp_path),
        vector_store=FakeVectorStore(),
    )

    with pytest.raises(ConversationMemoryError, match="Conversation not found"):
        service.delete_session_memories("missing")


class FakeVectorStore:
    def __init__(
        self,
        *,
        write_result: VectorWriteResult | None = None,
        deleted_vectors: int = 0,
        fail_delete_session: bool = False,
    ) -> None:
        self.write_result = write_result
        self.deleted_vectors = deleted_vectors
        self.fail_delete_session = fail_delete_session
        self.added_records = []
        self.calls: list[tuple[str, list[str]]] = []

    def add_conversation_memories(self, records):
        ids = [record.id for record in records]
        self.calls.append(("add_conversation_memories", ids))
        self.added_records.extend(records)
        if self.write_result is not None:
            return self.write_result
        return VectorWriteResult(
            ok=True,
            message=f"Wrote {len(records)} vectors to conversation_memory.",
            total_texts=len(records),
            processed_texts=len(records),
            total_batches=1 if records else 0,
            processed_batches=1 if records else 0,
            failed_batch_index=None,
        )

    def delete_by_ids(self, collection_name: str, ids: list[str]) -> int:
        assert collection_name == COLLECTION_CONVERSATION_MEMORY
        self.calls.append(("delete_by_ids", list(ids)))
        return len(ids)

    def delete_by_session_id(self, session_id: str) -> int:
        self.calls.append(("delete_by_session_id", [session_id]))
        if self.fail_delete_session:
            raise VectorStoreError("Vector delete failed")
        return self.deleted_vectors


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
