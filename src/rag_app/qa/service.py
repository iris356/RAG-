"""RAG question answering service."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from rag_app.conversations.memory import (
    ConversationMemoryResult,
    ConversationMemoryService,
)
from rag_app.conversations.store import (
    ROLE_ASSISTANT,
    ROLE_USER,
    ConversationMessage,
    ConversationStore,
)
from rag_app.core.exceptions import (
    ConfigurationError,
    ConversationMemoryError,
    ConversationStoreError,
    RagAnswerError,
    VectorStoreError,
)
from rag_app.models.config import ModelConfig
from rag_app.models.service import build_chat_model
from rag_app.vectors.store import (
    COLLECTION_CONVERSATION_MEMORY,
    COLLECTION_KNOWLEDGE_CHUNKS,
    VectorSearchResult,
    VectorStore,
)


@dataclass(frozen=True)
class RagAnswerResult:
    """Result returned after answering one RAG question."""

    ok: bool
    message: str
    session_id: str
    answer: str
    user_message: ConversationMessage | None
    assistant_message: ConversationMessage | None
    knowledge_result_count: int
    memory_result_count: int
    user_memory_result: ConversationMemoryResult | None = None
    assistant_memory_result: ConversationMemoryResult | None = None


class RagAnswerService:
    """Coordinate retrieval, chat generation, history, and memory writes."""

    def __init__(
        self,
        *,
        conversation_store: ConversationStore,
        memory_service: ConversationMemoryService,
        vector_store: VectorStore,
        model_config: ModelConfig,
        chat_model_factory: Callable[[ModelConfig], Any] = build_chat_model,
    ) -> None:
        self.conversation_store = conversation_store
        self.memory_service = memory_service
        self.vector_store = vector_store
        self.model_config = model_config
        self._chat_model_factory = chat_model_factory

    def answer_question(
        self,
        question: str,
        *,
        session_id: str | None = None,
    ) -> RagAnswerResult:
        """Answer one user question and persist the resulting conversation turn."""

        clean_question = question.strip()
        if not clean_question:
            raise RagAnswerError("Question must not be empty.")

        try:
            session = self.conversation_store.get_or_create_session_for_first_user_message(
                clean_question,
                session_id=session_id,
            )
        except ConversationStoreError as exc:
            raise RagAnswerError(f"Failed to load conversation: {exc}") from exc

        knowledge_results = self._search_knowledge(clean_question)
        memory_results = self._search_memories(clean_question, session.session_id)
        prompt = build_rag_prompt(
            question=clean_question,
            knowledge_results=knowledge_results,
            memory_results=memory_results,
        )
        answer = self._invoke_chat_model(prompt)

        try:
            user_message = self.conversation_store.add_message(
                session.session_id,
                ROLE_USER,
                clean_question,
            )
            assistant_message = self.conversation_store.add_message(
                session.session_id,
                ROLE_ASSISTANT,
                answer,
            )
        except ConversationStoreError as exc:
            raise RagAnswerError(f"Failed to save conversation messages: {exc}") from exc

        user_memory_result = self._write_memory(user_message)
        assistant_memory_result = self._write_memory(assistant_message)
        memory_ok = user_memory_result.ok and assistant_memory_result.ok

        if not memory_ok:
            return RagAnswerResult(
                ok=False,
                message=(
                    "Answer saved, but one or more conversation memories failed to write. "
                    "Use rebuild memory to repair this conversation."
                ),
                session_id=session.session_id,
                answer=answer,
                user_message=user_message,
                assistant_message=assistant_message,
                knowledge_result_count=len(knowledge_results),
                memory_result_count=len(memory_results),
                user_memory_result=user_memory_result,
                assistant_memory_result=assistant_memory_result,
            )

        return RagAnswerResult(
            ok=True,
            message="Answer generated and saved.",
            session_id=session.session_id,
            answer=answer,
            user_message=user_message,
            assistant_message=assistant_message,
            knowledge_result_count=len(knowledge_results),
            memory_result_count=len(memory_results),
            user_memory_result=user_memory_result,
            assistant_memory_result=assistant_memory_result,
        )

    def _search_knowledge(self, question: str) -> list[VectorSearchResult]:
        try:
            return self.vector_store.similarity_search(
                COLLECTION_KNOWLEDGE_CHUNKS,
                question,
            )
        except VectorStoreError as exc:
            raise RagAnswerError(f"Knowledge retrieval failed: {exc}") from exc

    def _search_memories(
        self,
        question: str,
        session_id: str,
    ) -> list[VectorSearchResult]:
        try:
            return self.vector_store.similarity_search(
                COLLECTION_CONVERSATION_MEMORY,
                question,
                where={"session_id": session_id},
            )
        except VectorStoreError as exc:
            raise RagAnswerError(f"Conversation memory retrieval failed: {exc}") from exc

    def _invoke_chat_model(self, prompt: str) -> str:
        try:
            chat_model = self._chat_model_factory(self.model_config)
            response = chat_model.invoke(prompt)
        except ConfigurationError as exc:
            raise RagAnswerError(f"Chat model configuration is invalid: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - provider-specific failures vary.
            raise RagAnswerError(f"Chat model invocation failed: {exc}") from exc

        content = getattr(response, "content", response)
        answer = str(content).strip()
        if not answer:
            raise RagAnswerError("Chat model returned an empty answer.")
        return answer

    def _write_memory(
        self,
        message: ConversationMessage,
    ) -> ConversationMemoryResult:
        try:
            return self.memory_service.write_message_memory(message)
        except ConversationMemoryError as exc:
            raise RagAnswerError(f"Failed to write conversation memory: {exc}") from exc


def build_rag_prompt(
    *,
    question: str,
    knowledge_results: Sequence[VectorSearchResult],
    memory_results: Sequence[VectorSearchResult],
) -> str:
    """Build the first-version RAG prompt."""

    knowledge_context = _format_search_results(knowledge_results)
    memory_context = _format_search_results(memory_results)
    missing_context_notes: list[str] = []
    if not knowledge_results:
        missing_context_notes.append("No relevant knowledge base context was retrieved.")
    if not memory_results:
        missing_context_notes.append(
            "No relevant long-term memory context was retrieved for this conversation."
        )

    missing_context = "\n".join(missing_context_notes) or "Relevant context is available."
    return (
        "You are a careful RAG knowledge-base assistant.\n"
        "Answer in the same language as the user's question when practical.\n"
        "Use the knowledge base context and current-conversation memory when they help.\n"
        "If relevant context is missing, clearly say so and then answer from the available "
        "conversation context or general model knowledge.\n"
        "Do not fabricate source labels or citation numbers.\n\n"
        f"Context status:\n{missing_context}\n\n"
        f"Knowledge base context:\n{knowledge_context}\n\n"
        f"Current conversation memory:\n{memory_context}\n\n"
        f"User question:\n{question}\n\n"
        "Direct answer:"
    )


def _format_search_results(results: Sequence[VectorSearchResult]) -> str:
    if not results:
        return "(none)"

    formatted: list[str] = []
    for index, result in enumerate(results, start=1):
        metadata = _format_metadata(result.metadata)
        if metadata:
            formatted.append(f"[{index}] {result.text}\nMetadata: {metadata}")
        else:
            formatted.append(f"[{index}] {result.text}")
    return "\n\n".join(formatted)


def _format_metadata(metadata: dict[str, Any]) -> str:
    if not metadata:
        return ""

    visible_keys = (
        "document_id",
        "original_filename",
        "file_type",
        "chunk_index",
        "session_id",
        "message_id",
        "role",
        "created_at",
    )
    parts = [
        f"{key}={metadata[key]}"
        for key in visible_keys
        if key in metadata and metadata[key] not in (None, "")
    ]
    return ", ".join(parts)
