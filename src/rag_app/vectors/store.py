"""Chroma-backed vector storage and throttled embedding writes."""

from __future__ import annotations

import math
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_app.core.exceptions import VectorStoreError
from rag_app.models.config import EmbeddingProvider, ModelConfig
from rag_app.models.service import build_embedding_model

COLLECTION_KNOWLEDGE_CHUNKS = "knowledge_chunks"
COLLECTION_CONVERSATION_MEMORY = "conversation_memory"
_SUPPORTED_COLLECTIONS = {
    COLLECTION_KNOWLEDGE_CHUNKS,
    COLLECTION_CONVERSATION_MEMORY,
}


@dataclass(frozen=True)
class VectorRecord:
    """A single text and metadata payload to persist in Chroma."""

    id: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class VectorSearchResult:
    """A single vector search result."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float | None


@dataclass(frozen=True)
class VectorWriteResult:
    """Progress and status from a batched vector write."""

    ok: bool
    message: str
    total_texts: int
    processed_texts: int
    total_batches: int
    processed_batches: int
    failed_batch_index: int | None


class VectorStore:
    """Persist and query application vectors in local Chroma collections."""

    def __init__(
        self,
        *,
        chroma_dir: Path,
        model_config: ModelConfig,
        embedding_model: Any | None = None,
        client_factory: Callable[[str], Any] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.chroma_dir = chroma_dir
        self.model_config = model_config
        self._embedding_model = embedding_model
        self._client_factory = client_factory or _build_persistent_client
        self._sleep = sleep
        self._client: Any | None = None

    def initialize_collections(self) -> None:
        """Create the required Chroma collections if they do not exist."""

        for collection_name in _SUPPORTED_COLLECTIONS:
            self._get_collection(collection_name)

    def add_knowledge_chunks(self, records: Sequence[VectorRecord]) -> VectorWriteResult:
        """Embed and persist knowledge chunk records."""

        duplicate_document_id = self._first_existing_document_id(records)
        if duplicate_document_id:
            return VectorWriteResult(
                ok=False,
                message=(
                    "Knowledge vectors already exist for "
                    f"document_id={duplicate_document_id}. Delete them before re-indexing."
                ),
                total_texts=len(records),
                processed_texts=0,
                total_batches=_total_batches(len(records), self.model_config.embedding.batch_size),
                processed_batches=0,
                failed_batch_index=None,
            )

        return self._add_records(COLLECTION_KNOWLEDGE_CHUNKS, records)

    def add_conversation_memories(self, records: Sequence[VectorRecord]) -> VectorWriteResult:
        """Embed and persist conversation memory records."""

        return self._add_records(COLLECTION_CONVERSATION_MEMORY, records)

    def similarity_search(
        self,
        collection_name: str,
        query: str,
        *,
        top_k: int | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Search a Chroma collection with the configured embedding model."""

        collection = self._get_collection(collection_name)
        limit = top_k or self.model_config.retrieval.top_k

        try:
            query_embedding = self._get_embedding_model().embed_query(query)
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:  # noqa: BLE001 - wrap Chroma and provider failures.
            raise VectorStoreError(f"Vector search failed: {exc}") from exc

        ids = _first_result_list(result.get("ids"))
        documents = _first_result_list(result.get("documents"))
        metadatas = _first_result_list(result.get("metadatas"))
        distances = _first_result_list(result.get("distances"))

        search_results: list[VectorSearchResult] = []
        for index, record_id in enumerate(ids):
            distance = distances[index] if index < len(distances) else None
            search_results.append(
                VectorSearchResult(
                    id=record_id,
                    text=documents[index] if index < len(documents) else "",
                    metadata=metadatas[index] if index < len(metadatas) and metadatas[index] else {},
                    score=distance,
                )
            )
        return search_results

    def delete_by_ids(self, collection_name: str, ids: Sequence[str]) -> int:
        """Delete vectors by IDs and return the number of requested IDs."""

        if not ids:
            return 0

        collection = self._get_collection(collection_name)
        try:
            collection.delete(ids=list(ids))
        except Exception as exc:  # noqa: BLE001 - wrap Chroma failures.
            raise VectorStoreError(f"Vector delete by IDs failed: {exc}") from exc
        return len(ids)

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete knowledge chunk vectors for one document."""

        return self._delete_by_where(
            COLLECTION_KNOWLEDGE_CHUNKS,
            {"document_id": document_id},
        )

    def delete_by_session_id(self, session_id: str) -> int:
        """Delete conversation memory vectors for one session."""

        return self._delete_by_where(
            COLLECTION_CONVERSATION_MEMORY,
            {"session_id": session_id},
        )

    def _add_records(
        self,
        collection_name: str,
        records: Sequence[VectorRecord],
    ) -> VectorWriteResult:
        if not records:
            return VectorWriteResult(
                ok=True,
                message="No vectors to write.",
                total_texts=0,
                processed_texts=0,
                total_batches=0,
                processed_batches=0,
                failed_batch_index=None,
            )

        collection = self._get_collection(collection_name)
        batch_size = self.model_config.embedding.batch_size
        batches = list(_batched(records, batch_size))
        processed_texts = 0
        processed_batches = 0

        max_workers = min(self.effective_max_concurrency, len(batches))
        pending: dict[Future[list[list[float]]], tuple[int, list[VectorRecord]]] = {}
        next_batch_index = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            while next_batch_index < len(batches) or pending:
                while next_batch_index < len(batches) and len(pending) < max_workers:
                    batch = batches[next_batch_index]
                    batch_index = next_batch_index + 1
                    future = executor.submit(
                        self._get_embedding_model().embed_documents,
                        [record.text for record in batch],
                    )
                    pending[future] = (batch_index, batch)
                    next_batch_index += 1

                    if (
                        next_batch_index < len(batches)
                        and self.model_config.embedding.batch_interval_seconds
                    ):
                        self._sleep(self.model_config.embedding.batch_interval_seconds)

                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in sorted(done, key=lambda item: pending[item][0]):
                    batch_index, batch = pending.pop(future)
                    try:
                        embeddings = future.result()
                        collection.add(
                            ids=[record.id for record in batch],
                            documents=[record.text for record in batch],
                            metadatas=[record.metadata for record in batch],
                            embeddings=embeddings,
                        )
                    except Exception as exc:  # noqa: BLE001 - return UI-displayable failure.
                        for unfinished in pending:
                            unfinished.cancel()
                        return VectorWriteResult(
                            ok=False,
                            message=f"Vector batch {batch_index} failed: {exc}",
                            total_texts=len(records),
                            processed_texts=processed_texts,
                            total_batches=len(batches),
                            processed_batches=processed_batches,
                            failed_batch_index=batch_index,
                        )

                    processed_batches += 1
                    processed_texts += len(batch)

        return VectorWriteResult(
            ok=True,
            message=f"Wrote {processed_texts} vectors to {collection_name}.",
            total_texts=len(records),
            processed_texts=processed_texts,
            total_batches=len(batches),
            processed_batches=processed_batches,
            failed_batch_index=None,
        )

    def _delete_by_where(self, collection_name: str, where: dict[str, Any]) -> int:
        collection = self._get_collection(collection_name)
        try:
            existing = collection.get(where=where, include=[])
            ids = existing.get("ids", [])
            if ids:
                collection.delete(where=where)
        except Exception as exc:  # noqa: BLE001 - wrap Chroma failures.
            raise VectorStoreError(f"Vector delete failed: {exc}") from exc
        return len(ids)

    def _first_existing_document_id(self, records: Sequence[VectorRecord]) -> str | None:
        document_ids = {
            record.metadata.get("document_id")
            for record in records
            if record.metadata.get("document_id")
        }
        collection = self._get_collection(COLLECTION_KNOWLEDGE_CHUNKS)

        for document_id in sorted(document_ids):
            try:
                existing = collection.get(
                    where={"document_id": document_id},
                    limit=1,
                    include=[],
                )
            except Exception as exc:  # noqa: BLE001 - wrap Chroma failures.
                raise VectorStoreError(f"Duplicate document check failed: {exc}") from exc
            if existing.get("ids"):
                return str(document_id)
        return None

    def _get_collection(self, collection_name: str):
        if collection_name not in _SUPPORTED_COLLECTIONS:
            raise VectorStoreError(f"Unsupported vector collection: {collection_name}")

        try:
            return self._get_client().get_or_create_collection(name=collection_name)
        except Exception as exc:  # noqa: BLE001 - wrap Chroma failures.
            raise VectorStoreError(f"Failed to initialize Chroma collection: {exc}") from exc

    def _get_client(self):
        if self._client is None:
            try:
                self.chroma_dir.mkdir(parents=True, exist_ok=True)
                self._client = self._client_factory(str(self.chroma_dir))
            except Exception as exc:  # noqa: BLE001 - wrap Chroma failures.
                raise VectorStoreError(f"Failed to initialize Chroma client: {exc}") from exc
        return self._client

    def _get_embedding_model(self):
        if self._embedding_model is None:
            try:
                self._embedding_model = build_embedding_model(self.model_config)
            except Exception as exc:  # noqa: BLE001 - wrap provider failures.
                raise VectorStoreError(f"Failed to initialize embedding model: {exc}") from exc
        return self._embedding_model

    @property
    def effective_max_concurrency(self) -> int:
        """Return the actual embedding concurrency limit for this store."""

        if self.model_config.embedding.provider == EmbeddingProvider.LOCAL_HUGGINGFACE:
            return 1
        return self.model_config.embedding.max_concurrency


def _build_persistent_client(path: str):
    try:
        import chromadb
    except ImportError as exc:
        raise VectorStoreError("Missing dependency: chromadb") from exc

    return chromadb.PersistentClient(path=path)


def _batched(records: Sequence[VectorRecord], batch_size: int) -> list[list[VectorRecord]]:
    return [
        list(records[start : start + batch_size])
        for start in range(0, len(records), batch_size)
    ]


def _total_batches(total_records: int, batch_size: int) -> int:
    if total_records == 0:
        return 0
    return math.ceil(total_records / batch_size)


def _first_result_list(value: Any) -> list[Any]:
    if not value:
        return []
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    if isinstance(value, list):
        return value
    return []
