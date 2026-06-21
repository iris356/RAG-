from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from rag_app.conversations.memory import ConversationMemoryResult
from rag_app.conversations.store import ROLE_ASSISTANT, ROLE_USER, ConversationStore
from rag_app.core.exceptions import ConfigurationError, RagAnswerError, VectorStoreError
from rag_app.models.config import ModelConfig
from rag_app.qa.service import RagAnswerService, build_rag_prompt
from rag_app.vectors.store import (
    COLLECTION_CONVERSATION_MEMORY,
    COLLECTION_KNOWLEDGE_CHUNKS,
    VectorSearchResult,
)


@dataclass
class FakeChatResponse:
    content: str


class FakeChatModel:
    def __init__(self, answer: str = "This is the answer.") -> None:
        self.answer = answer
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> FakeChatResponse:
        self.prompts.append(prompt)
        return FakeChatResponse(self.answer)


class FakeVectorStore:
    def __init__(
        self,
        *,
        knowledge_results: list[VectorSearchResult] | None = None,
        memory_results: list[VectorSearchResult] | None = None,
        fail_collection: str | None = None,
    ) -> None:
        self.knowledge_results = knowledge_results or []
        self.memory_results = memory_results or []
        self.fail_collection = fail_collection
        self.calls: list[tuple[str, str, dict | None]] = []

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        *,
        where: dict | None = None,
    ) -> list[VectorSearchResult]:
        self.calls.append((collection_name, query, where))
        if self.fail_collection == collection_name:
            raise VectorStoreError(f"{collection_name} failed")
        if collection_name == COLLECTION_KNOWLEDGE_CHUNKS:
            return self.knowledge_results
        if collection_name == COLLECTION_CONVERSATION_MEMORY:
            return self.memory_results
        raise AssertionError(f"Unexpected collection: {collection_name}")


class FakeMemoryService:
    def __init__(self, *, fail_after: int | None = None) -> None:
        self.fail_after = fail_after
        self.messages = []

    def write_message_memory(self, message):
        self.messages.append(message)
        ok = self.fail_after is None or len(self.messages) <= self.fail_after
        return ConversationMemoryResult(
            ok=ok,
            message="memory ok" if ok else "memory failed",
            session_id=message.session_id,
            total_messages=1,
            written_messages=1 if ok else 0,
        )


def test_answer_without_session_creates_conversation_and_saves_turn(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    vector_store = FakeVectorStore(
        knowledge_results=[_result("knowledge-1", "Knowledge context")],
        memory_results=[_result("memory-1", "Memory context", {"session_id": "session-1"})],
    )
    memory_service = FakeMemoryService()
    chat_model = FakeChatModel("Final answer")

    service = RagAnswerService(
        conversation_store=store,
        memory_service=memory_service,  # type: ignore[arg-type]
        vector_store=vector_store,  # type: ignore[arg-type]
        model_config=ModelConfig(),
        chat_model_factory=lambda _config: chat_model,
    )

    result = service.answer_question(" How does module eight work? ")

    assert result.ok is True
    assert result.answer == "Final answer"
    assert result.knowledge_result_count == 1
    assert result.memory_result_count == 1
    assert result.user_message is not None
    assert result.assistant_message is not None
    assert result.user_message.content == "How does module eight work?"
    assert result.assistant_message.content == "Final answer"
    assert [message.role for message in store.get_messages(result.session_id)] == [
        ROLE_USER,
        ROLE_ASSISTANT,
    ]
    assert [message.message_id for message in memory_service.messages] == [
        result.user_message.message_id,
        result.assistant_message.message_id,
    ]
    assert vector_store.calls[0] == (
        COLLECTION_KNOWLEDGE_CHUNKS,
        "How does module eight work?",
        None,
    )
    assert vector_store.calls[1] == (
        COLLECTION_CONVERSATION_MEMORY,
        "How does module eight work?",
        {"session_id": result.session_id},
    )
    assert "Knowledge context" in chat_model.prompts[0]
    assert "Memory context" in chat_model.prompts[0]


def test_answer_reuses_existing_session(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    session = store.create_session("Existing")
    service = _service(store)

    result = service.answer_question("Follow up", session_id=session.session_id)

    assert result.session_id == session.session_id
    assert [message.content for message in store.get_messages(session.session_id)] == [
        "Follow up",
        "This is the answer.",
    ]


def test_empty_context_still_calls_chat_model(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    chat_model = FakeChatModel("Answer without context")
    service = _service(store, chat_model=chat_model)

    result = service.answer_question("Question without indexed data")

    assert result.ok is True
    assert result.knowledge_result_count == 0
    assert result.memory_result_count == 0
    assert "No relevant knowledge base context was retrieved." in chat_model.prompts[0]
    assert "No relevant long-term memory context was retrieved" in chat_model.prompts[0]


def test_empty_question_is_rejected(tmp_path: Path) -> None:
    service = _service(ConversationStore(sqlite_dir=tmp_path))

    with pytest.raises(RagAnswerError, match="Question must not be empty"):
        service.answer_question("   ")


def test_retrieval_failure_does_not_save_messages(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    session = store.create_session("Existing")
    service = _service(
        store,
        vector_store=FakeVectorStore(fail_collection=COLLECTION_KNOWLEDGE_CHUNKS),
    )

    with pytest.raises(RagAnswerError, match="Knowledge retrieval failed"):
        service.answer_question("Will retrieval fail?", session_id=session.session_id)

    assert store.get_messages(session.session_id) == []


def test_chat_configuration_failure_does_not_save_messages(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    session = store.create_session("Existing")
    service = RagAnswerService(
        conversation_store=store,
        memory_service=FakeMemoryService(),  # type: ignore[arg-type]
        vector_store=FakeVectorStore(),  # type: ignore[arg-type]
        model_config=ModelConfig(),
        chat_model_factory=lambda _config: (_raise(ConfigurationError("missing chat"))),
    )

    with pytest.raises(RagAnswerError, match="Chat model configuration is invalid"):
        service.answer_question("Will chat fail?", session_id=session.session_id)

    assert store.get_messages(session.session_id) == []


def test_empty_chat_answer_is_rejected_before_saving(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    session = store.create_session("Existing")
    service = _service(store, chat_model=FakeChatModel("   "))

    with pytest.raises(RagAnswerError, match="empty answer"):
        service.answer_question("Will empty answer save?", session_id=session.session_id)

    assert store.get_messages(session.session_id) == []


def test_memory_write_failure_returns_warning_after_saving_messages(tmp_path: Path) -> None:
    store = ConversationStore(sqlite_dir=tmp_path)
    memory_service = FakeMemoryService(fail_after=1)
    service = _service(store, memory_service=memory_service)

    result = service.answer_question("Persist even if memory warning happens")

    assert result.ok is False
    assert "Answer saved" in result.message
    assert result.user_memory_result is not None
    assert result.assistant_memory_result is not None
    assert result.user_memory_result.ok is True
    assert result.assistant_memory_result.ok is False
    assert [message.role for message in store.get_messages(result.session_id)] == [
        ROLE_USER,
        ROLE_ASSISTANT,
    ]


def test_prompt_does_not_create_fake_source_policy() -> None:
    prompt = build_rag_prompt(
        question="What happened?",
        knowledge_results=[],
        memory_results=[],
    )

    assert "Do not fabricate source labels or citation numbers." in prompt
    assert "Direct answer:" in prompt


def _service(
    store: ConversationStore,
    *,
    vector_store: FakeVectorStore | None = None,
    memory_service: FakeMemoryService | None = None,
    chat_model: FakeChatModel | None = None,
) -> RagAnswerService:
    chat_model = chat_model or FakeChatModel()
    return RagAnswerService(
        conversation_store=store,
        memory_service=memory_service or FakeMemoryService(),  # type: ignore[arg-type]
        vector_store=vector_store or FakeVectorStore(),  # type: ignore[arg-type]
        model_config=ModelConfig(),
        chat_model_factory=lambda _config: chat_model,
    )


def _result(
    result_id: str,
    text: str,
    metadata: dict | None = None,
) -> VectorSearchResult:
    return VectorSearchResult(
        id=result_id,
        text=text,
        metadata=metadata or {},
        score=0.1,
    )


def _raise(exc: Exception):
    raise exc
