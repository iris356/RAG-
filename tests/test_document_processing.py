from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rag_app.core.exceptions import DocumentProcessingError
from rag_app.documents.processing import (
    DocumentProcessor,
    calculate_text_md5,
    normalize_text,
)
from rag_app.documents.store import (
    INDEX_STATUS_FAILED,
    INDEX_STATUS_INDEXED,
    INDEX_STATUS_NOT_INDEXED,
    PARSE_STATUS_FAILED,
    PARSE_STATUS_PARSED,
    STATUS_DUPLICATE,
    DocumentStore,
)
from rag_app.vectors.store import VectorRecord, VectorWriteResult


def test_normalize_text_and_text_md5_are_stable() -> None:
    first = normalize_text("  Alpha\r\n\r\n beta\t gamma  ")
    second = normalize_text("Alpha beta\n gamma")

    assert first == "Alpha beta gamma"
    assert first == second
    assert calculate_text_md5(first) == calculate_text_md5(second)


def test_txt_document_is_split_and_indexed_with_required_metadata(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    upload = store.upload_document("notes.txt", b"alpha beta gamma delta")
    assert upload.document is not None
    vector_store = FakeVectorStore()
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument("alpha beta gamma delta", {"page": 2, "source": "notes.txt"})],
        chunks=["alpha beta", "gamma delta"],
    )

    result = processor.process_document("doc-1")

    assert result.ok is True
    assert result.chunk_count == 2
    assert result.document is not None
    assert result.document.parse_status == PARSE_STATUS_PARSED
    assert result.document.index_status == INDEX_STATUS_INDEXED
    assert result.document.chunk_count == 2
    assert vector_store.added_records is not None
    assert [record.id for record in vector_store.added_records] == [
        "doc-1:chunk:0",
        "doc-1:chunk:1",
    ]
    first_metadata = vector_store.added_records[0].metadata
    assert first_metadata["document_id"] == "doc-1"
    assert first_metadata["original_filename"] == "notes.txt"
    assert first_metadata["file_type"] == "txt"
    assert first_metadata["file_md5"] == upload.document.file_md5
    assert first_metadata["text_md5"] == result.text_md5
    assert first_metadata["chunk_index"] == 0
    assert first_metadata["page"] == 2
    assert first_metadata["source"] == "notes.txt"


@pytest.mark.parametrize(
    ("filename", "file_type"),
    [
        ("paper.pdf", "pdf"),
        ("report.docx", "word"),
        ("guide.md", "markdown"),
    ],
)
def test_processor_selects_loader_by_document_type(
    tmp_path: Path,
    filename: str,
    file_type: str,
) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document(filename, b"content")
    vector_store = FakeVectorStore()
    loader_calls: list[str] = []

    processor = DocumentProcessor(
        document_store=store,
        vector_store=vector_store,
        loader_factories={
            file_type: lambda path: loader_calls.append(path.suffix.lower())
            or FakeLoader([FakeLoadedDocument("body text")]),
        },
        text_splitter_factory=lambda: FakeSplitter(["body text"]),
    )

    result = processor.process_document("doc-1")

    assert result.ok is True
    assert loader_calls == [Path(filename).suffix.lower()]
    assert vector_store.added_records is not None


def test_same_normalized_text_is_marked_duplicate_and_not_indexed(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1", "doc-2"])
    first = store.upload_document("first.txt", b"first raw")
    second = store.upload_document("second.txt", b"second raw")
    assert first.document is not None
    assert second.document is not None
    text_md5 = calculate_text_md5(normalize_text("same body"))
    store.update_text_fingerprint("doc-1", text_md5)
    vector_store = FakeVectorStore()
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument(" same   body ")],
        chunks=["same body"],
    )

    result = processor.process_document("doc-2")

    assert result.ok is True
    assert result.duplicate_of_document_id == "doc-1"
    assert result.document is not None
    assert result.document.status == STATUS_DUPLICATE
    assert result.document.parse_status == PARSE_STATUS_PARSED
    assert result.document.index_status == INDEX_STATUS_NOT_INDEXED
    assert result.document.chunk_count == 0
    assert vector_store.added_records is None


def test_reindex_duplicate_text_deletes_existing_vectors_without_rewriting(
    tmp_path: Path,
) -> None:
    store = make_store(tmp_path, ids=["doc-1", "doc-2"])
    store.upload_document("original.txt", b"first raw")
    store.upload_document("duplicate.txt", b"second raw")
    text_md5 = calculate_text_md5(normalize_text("same body"))
    store.update_text_fingerprint("doc-1", text_md5)
    vector_store = FakeVectorStore()
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument("same body")],
        chunks=["same body"],
    )

    result = processor.process_document("doc-2", reindex=True)

    assert result.ok is True
    assert result.deleted_vectors == 2
    assert vector_store.deleted_document_ids == ["doc-2"]
    assert vector_store.added_records is None


def test_reindex_deletes_existing_vectors_before_rewriting(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("reindex.txt", b"content")
    vector_store = FakeVectorStore()
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument("fresh body")],
        chunks=["fresh body"],
    )

    result = processor.process_document("doc-1", reindex=True)

    assert result.ok is True
    assert result.deleted_vectors == 2
    assert vector_store.deleted_document_ids == ["doc-1"]
    assert vector_store.added_records is not None


def test_vector_write_failure_marks_index_failed(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("fail-index.txt", b"content")
    vector_store = FakeVectorStore(ok=False)
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument("body text")],
        chunks=["body text"],
    )

    result = processor.process_document("doc-1")

    assert result.ok is False
    assert result.document is not None
    assert result.document.parse_status == PARSE_STATUS_PARSED
    assert result.document.index_status == INDEX_STATUS_FAILED
    assert result.vector_write_result is not None
    assert "Vector batch 1 failed" in result.message


def test_empty_parsed_text_marks_parse_failed_and_does_not_index(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("empty.txt", b"content")
    vector_store = FakeVectorStore()
    processor = make_processor(
        store,
        vector_store,
        loaded=[FakeLoadedDocument("   \n\t   ")],
        chunks=[],
    )

    result = processor.process_document("doc-1")

    assert result.ok is False
    assert result.document is not None
    assert result.document.parse_status == PARSE_STATUS_FAILED
    assert result.document.index_status == INDEX_STATUS_NOT_INDEXED
    assert vector_store.added_records is None


def test_duplicate_document_is_rejected_by_default(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("duplicate.txt", b"content")
    store.update_text_fingerprint("doc-1", "text-md5", duplicate_of_document_id="doc-0")
    processor = make_processor(
        store,
        FakeVectorStore(),
        loaded=[FakeLoadedDocument("body")],
        chunks=["body"],
    )

    with pytest.raises(DocumentProcessingError, match="Duplicate documents are not indexed"):
        processor.process_document("doc-1")


@dataclass(frozen=True)
class FakeLoadedDocument:
    page_content: str
    metadata: dict | None = None


class FakeLoader:
    def __init__(self, loaded: list[FakeLoadedDocument]) -> None:
        self.loaded = loaded

    def load(self) -> list[FakeLoadedDocument]:
        return self.loaded


class FakeSplitter:
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks
        self.seen_texts: list[str] = []

    def split_text(self, text: str) -> list[str]:
        self.seen_texts.append(text)
        return self.chunks


class FakeVectorStore:
    def __init__(self, *, ok: bool = True) -> None:
        self.ok = ok
        self.added_records: list[VectorRecord] | None = None
        self.deleted_document_ids: list[str] = []

    def add_knowledge_chunks(self, records: list[VectorRecord]) -> VectorWriteResult:
        self.added_records = list(records)
        if not self.ok:
            return VectorWriteResult(
                ok=False,
                message="Vector batch 1 failed: embedding failed",
                total_texts=len(records),
                processed_texts=0,
                total_batches=1,
                processed_batches=0,
                failed_batch_index=1,
            )
        return VectorWriteResult(
            ok=True,
            message=f"Wrote {len(records)} vectors to knowledge_chunks.",
            total_texts=len(records),
            processed_texts=len(records),
            total_batches=1 if records else 0,
            processed_batches=1 if records else 0,
            failed_batch_index=None,
        )

    def delete_by_document_id(self, document_id: str) -> int:
        self.deleted_document_ids.append(document_id)
        return 2


def make_processor(
    store: DocumentStore,
    vector_store: FakeVectorStore,
    *,
    loaded: list[FakeLoadedDocument],
    chunks: list[str],
) -> DocumentProcessor:
    return DocumentProcessor(
        document_store=store,
        vector_store=vector_store,
        loader_factories={
            "txt": lambda _path: FakeLoader(loaded),
            "markdown": lambda _path: FakeLoader(loaded),
            "pdf": lambda _path: FakeLoader(loaded),
            "word": lambda _path: FakeLoader(loaded),
        },
        text_splitter_factory=lambda: FakeSplitter(chunks),
    )


def make_store(
    tmp_path: Path,
    *,
    ids: list[str] | None = None,
    times: list[datetime] | None = None,
) -> DocumentStore:
    id_values = list(ids or ["doc-1"])
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

    return DocumentStore(
        sqlite_dir=tmp_path / "sqlite",
        raw_dir=tmp_path / "raw",
        id_factory=next_id,
        now_factory=next_time,
    )
