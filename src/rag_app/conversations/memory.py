"""Conversation long-term memory synchronization with Chroma."""

from __future__ import annotations

from dataclasses import dataclass

from rag_app.conversations.store import ConversationMessage, ConversationStore
from rag_app.core.exceptions import (
    ConversationMemoryError,
    ConversationStoreError,
    VectorStoreError,
)
from rag_app.vectors.store import (
    COLLECTION_CONVERSATION_MEMORY,
    VectorRecord,
    VectorStore,
    VectorWriteResult,
)


@dataclass(frozen=True)
class ConversationMemoryResult:
    """Result returned after syncing conversation messages with memory vectors."""

    ok: bool
    message: str
    session_id: str
    total_messages: int = 0
    written_messages: int = 0
    deleted_vectors: int = 0
    deleted_sqlite_messages: int = 0
    vector_write_result: VectorWriteResult | None = None


class ConversationMemoryService:
    """Coordinate SQLite conversation history with Chroma memory vectors."""

    def __init__(
        self,
        *,
        conversation_store: ConversationStore,
        vector_store: VectorStore,
    ) -> None:
        self.conversation_store = conversation_store
        self.vector_store = vector_store

    def write_message_memory(
        self,
        message: ConversationMessage,
    ) -> ConversationMemoryResult:
        """Write one saved conversation message to long-term memory."""

        self._require_session(message.session_id)
        record = build_conversation_memory_record(message)

        try:
            self.vector_store.delete_by_ids(
                COLLECTION_CONVERSATION_MEMORY,
                [record.id],
            )
            write_result = self.vector_store.add_conversation_memories([record])
        except VectorStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to write conversation memory: {exc}"
            ) from exc

        if not write_result.ok:
            return ConversationMemoryResult(
                ok=False,
                message=write_result.message,
                session_id=message.session_id,
                total_messages=1,
                written_messages=write_result.processed_texts,
                vector_write_result=write_result,
            )

        return ConversationMemoryResult(
            ok=True,
            message=write_result.message,
            session_id=message.session_id,
            total_messages=1,
            written_messages=1,
            vector_write_result=write_result,
        )

    def rebuild_session_memories(self, session_id: str) -> ConversationMemoryResult:
        """Rebuild all memory vectors for one existing conversation session."""

        try:
            conversation = self.conversation_store.get_conversation(session_id)
            deleted_vectors = self.vector_store.delete_by_session_id(session_id)
        except ConversationStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to load conversation for memory rebuild: {exc}"
            ) from exc
        except VectorStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to clear conversation memories before rebuild: {exc}"
            ) from exc

        records = [
            build_conversation_memory_record(message)
            for message in conversation.messages
        ]
        if not records:
            return ConversationMemoryResult(
                ok=True,
                message="No conversation messages to write.",
                session_id=session_id,
                total_messages=0,
                deleted_vectors=deleted_vectors,
            )

        try:
            write_result = self.vector_store.add_conversation_memories(records)
        except VectorStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to rebuild conversation memories: {exc}"
            ) from exc

        if not write_result.ok:
            return ConversationMemoryResult(
                ok=False,
                message=write_result.message,
                session_id=session_id,
                total_messages=len(records),
                written_messages=write_result.processed_texts,
                deleted_vectors=deleted_vectors,
                vector_write_result=write_result,
            )

        return ConversationMemoryResult(
            ok=True,
            message=write_result.message,
            session_id=session_id,
            total_messages=len(records),
            written_messages=len(records),
            deleted_vectors=deleted_vectors,
            vector_write_result=write_result,
        )

    def delete_session_memories(self, session_id: str) -> ConversationMemoryResult:
        """Delete only Chroma memory vectors for one existing conversation."""

        self._require_session(session_id)
        try:
            deleted_vectors = self.vector_store.delete_by_session_id(session_id)
        except VectorStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to delete conversation memories: {exc}"
            ) from exc

        return ConversationMemoryResult(
            ok=True,
            message=f"Deleted {deleted_vectors} conversation memory vectors.",
            session_id=session_id,
            deleted_vectors=deleted_vectors,
        )

    def delete_session_with_memories(self, session_id: str) -> ConversationMemoryResult:
        """Delete Chroma memories first, then delete the SQLite conversation."""

        try:
            messages = self.conversation_store.get_messages(session_id)
            deleted_vectors = self.vector_store.delete_by_session_id(session_id)
        except ConversationStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to load conversation before delete: {exc}"
            ) from exc
        except VectorStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to delete conversation memories: {exc}"
            ) from exc

        try:
            deleted_messages = self.conversation_store.delete_session(session_id)
        except ConversationStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to delete conversation after memory cleanup: {exc}"
            ) from exc

        return ConversationMemoryResult(
            ok=True,
            message=(
                "Conversation deleted. "
                f"Deleted SQLite messages: {deleted_messages}. "
                f"Deleted memory vectors: {deleted_vectors}."
            ),
            session_id=session_id,
            total_messages=len(messages),
            deleted_vectors=deleted_vectors,
            deleted_sqlite_messages=deleted_messages,
        )

    def _require_session(self, session_id: str) -> None:
        try:
            session = self.conversation_store.get_session(session_id)
        except ConversationStoreError as exc:
            raise ConversationMemoryError(
                f"Failed to load conversation: {exc}"
            ) from exc
        if session is None:
            raise ConversationMemoryError(f"Conversation not found: {session_id}")


def build_conversation_memory_record(message: ConversationMessage) -> VectorRecord:
    """Convert a saved SQLite message into a Chroma memory vector payload."""

    return VectorRecord(
        id=build_conversation_memory_vector_id(message),
        text=message.content,
        metadata={
            "session_id": message.session_id,
            "message_id": message.message_id,
            "role": message.role,
            "created_at": message.created_at,
        },
    )


def build_conversation_memory_vector_id(message: ConversationMessage) -> str:
    """Return the stable vector ID for one conversation message."""

    return f"conversation:{message.session_id}:message:{message.message_id}"
