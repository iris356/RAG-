from __future__ import annotations

import threading
import time
from pathlib import Path

from rag_app.models.config import EmbeddingModelConfig, EmbeddingProvider, ModelConfig, RetrievalConfig
from rag_app.vectors.store import (
    COLLECTION_CONVERSATION_MEMORY,
    COLLECTION_KNOWLEDGE_CHUNKS,
    VectorRecord,
    VectorStore,
)


def test_initialize_collections_creates_required_collections(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    store.initialize_collections()

    collection_names = {collection.name for collection in store._get_client().list_collections()}
    assert collection_names == {COLLECTION_KNOWLEDGE_CHUNKS, COLLECTION_CONVERSATION_MEMORY}


def test_batch_size_controls_embedding_batches(tmp_path: Path) -> None:
    embedding = FakeEmbedding()
    store = make_store(tmp_path, embedding=embedding, batch_size=2)

    result = store.add_knowledge_chunks(make_knowledge_records(5, document_id="doc-1"))

    assert result.ok is True
    assert result.total_batches == 3
    assert result.processed_batches == 3
    assert result.processed_texts == 5
    assert embedding.batch_sizes == [2, 2, 1]


def test_local_embedding_provider_forces_single_concurrency(tmp_path: Path) -> None:
    embedding = FakeEmbedding(delay_seconds=0.01)
    store = make_store(
        tmp_path,
        embedding=embedding,
        provider=EmbeddingProvider.LOCAL_HUGGINGFACE,
        batch_size=1,
        max_concurrency=4,
    )

    result = store.add_conversation_memories(make_memory_records(4, session_id="session-1"))

    assert result.ok is True
    assert store.effective_max_concurrency == 1
    assert embedding.max_active_calls == 1


def test_similarity_search_returns_results_with_metadata_and_default_top_k(tmp_path: Path) -> None:
    store = make_store(tmp_path, top_k=1)
    records = [
        VectorRecord("chunk-1", "alpha", {"document_id": "doc-1", "file_md5": "f1", "text_md5": "t1"}),
        VectorRecord("chunk-2", "alphabet", {"document_id": "doc-2", "file_md5": "f2", "text_md5": "t2"}),
    ]
    assert store.add_knowledge_chunks(records).ok is True

    default_results = store.similarity_search(COLLECTION_KNOWLEDGE_CHUNKS, "alpha")
    explicit_results = store.similarity_search(COLLECTION_KNOWLEDGE_CHUNKS, "alpha", top_k=2)

    assert len(default_results) == 1
    assert len(explicit_results) == 2
    assert explicit_results[0].id
    assert explicit_results[0].text
    assert "document_id" in explicit_results[0].metadata
    assert explicit_results[0].score is not None


def test_duplicate_document_id_is_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    first_result = store.add_knowledge_chunks(make_knowledge_records(2, document_id="doc-1"))
    duplicate_result = store.add_knowledge_chunks(make_knowledge_records(1, document_id="doc-1"))

    assert first_result.ok is True
    assert duplicate_result.ok is False
    assert duplicate_result.processed_texts == 0
    assert "document_id=doc-1" in duplicate_result.message


def test_delete_by_document_id_only_deletes_target_document(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.add_knowledge_chunks(make_knowledge_records(2, document_id="doc-1"))
    store.add_knowledge_chunks(make_knowledge_records(1, document_id="doc-2", start=10))

    deleted = store.delete_by_document_id("doc-1")
    remaining = store.similarity_search(COLLECTION_KNOWLEDGE_CHUNKS, "text", top_k=5)

    assert deleted == 2
    assert {result.metadata["document_id"] for result in remaining} == {"doc-2"}


def test_delete_by_session_id_only_deletes_target_memory(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.add_conversation_memories(make_memory_records(2, session_id="session-1"))
    store.add_conversation_memories(make_memory_records(1, session_id="session-2", start=10))

    deleted = store.delete_by_session_id("session-1")
    remaining = store.similarity_search(COLLECTION_CONVERSATION_MEMORY, "memory", top_k=5)

    assert deleted == 2
    assert {result.metadata["session_id"] for result in remaining} == {"session-2"}


def test_batch_failure_returns_clear_progress(tmp_path: Path) -> None:
    embedding = FakeEmbedding(fail_on_call=2)
    store = make_store(tmp_path, embedding=embedding, batch_size=2)

    result = store.add_knowledge_chunks(make_knowledge_records(5, document_id="doc-1"))

    assert result.ok is False
    assert result.total_batches == 3
    assert result.processed_batches == 1
    assert result.processed_texts == 2
    assert result.failed_batch_index == 2
    assert "Vector batch 2 failed" in result.message


class FakeEmbedding:
    def __init__(self, *, fail_on_call: int | None = None, delay_seconds: float = 0) -> None:
        self.batch_sizes: list[int] = []
        self.fail_on_call = fail_on_call
        self.delay_seconds = delay_seconds
        self.calls = 0
        self.active_calls = 0
        self.max_active_calls = 0
        self._lock = threading.Lock()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            self.calls += 1
            call_number = self.calls
            self.batch_sizes.append(len(texts))
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)

        try:
            if self.delay_seconds:
                time.sleep(self.delay_seconds)
            if self.fail_on_call == call_number:
                raise RuntimeError("embedding failed")
            return [self._embed_text(text) for text in texts]
        finally:
            with self._lock:
                self.active_calls -= 1

    def embed_query(self, text: str) -> list[float]:
        return self._embed_text(text)

    def _embed_text(self, text: str) -> list[float]:
        return [
            float(len(text)),
            float(sum(ord(char) for char in text) % 997),
            float(text.count("a")),
        ]


def make_store(
    tmp_path: Path,
    *,
    embedding: FakeEmbedding | None = None,
    provider: EmbeddingProvider = EmbeddingProvider.OPENAI_COMPATIBLE,
    batch_size: int = 8,
    max_concurrency: int = 1,
    top_k: int = 5,
) -> VectorStore:
    return VectorStore(
        chroma_dir=tmp_path / "chroma",
        model_config=ModelConfig(
            embedding=EmbeddingModelConfig(
                provider=provider,
                base_url="https://embedding.example.test/v1",
                api_key="key",
                model="embed",
                batch_size=batch_size,
                max_concurrency=max_concurrency,
            ),
            retrieval=RetrievalConfig(top_k=top_k),
        ),
        embedding_model=embedding or FakeEmbedding(),
    )


def make_knowledge_records(
    count: int,
    *,
    document_id: str,
    start: int = 0,
) -> list[VectorRecord]:
    return [
        VectorRecord(
            id=f"{document_id}-chunk-{index}",
            text=f"text {index}",
            metadata={
                "document_id": document_id,
                "file_md5": f"file-{document_id}",
                "text_md5": f"text-{document_id}",
            },
        )
        for index in range(start, start + count)
    ]


def make_memory_records(
    count: int,
    *,
    session_id: str,
    start: int = 0,
) -> list[VectorRecord]:
    return [
        VectorRecord(
            id=f"{session_id}-memory-{index}",
            text=f"memory {index}",
            metadata={
                "session_id": session_id,
                "message_id": f"message-{index}",
                "role": "user",
                "created_at": "2026-06-21T00:00:00",
            },
        )
        for index in range(start, start + count)
    ]
