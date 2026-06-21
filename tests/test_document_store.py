from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from rag_app.core.exceptions import DocumentStoreError, UnsupportedDocumentTypeError
from rag_app.documents.store import (
    INDEX_STATUS_INDEXED,
    INDEX_STATUS_NOT_INDEXED,
    INDEX_STATUS_PENDING,
    PARSE_STATUS_PARSED,
    PARSE_STATUS_PENDING,
    STATUS_DUPLICATE,
    STATUS_UPLOADED,
    DocumentStore,
    get_document_database_path,
    initialize_document_store,
)


def test_initialize_document_store_creates_database_and_table(tmp_path: Path) -> None:
    sqlite_dir = tmp_path / "sqlite"

    database_path = initialize_document_store(sqlite_dir)

    assert database_path == get_document_database_path(sqlite_dir)
    with sqlite3.connect(database_path) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'documents'"
        ).fetchone()
    assert table is not None


@pytest.mark.parametrize(
    ("filename", "file_type"),
    [
        ("paper.pdf", "pdf"),
        ("notes.docx", "word"),
        ("readme.md", "markdown"),
        ("manual.markdown", "markdown"),
        ("plain.txt", "txt"),
    ],
)
def test_supported_document_types_upload_successfully(
    tmp_path: Path,
    filename: str,
    file_type: str,
) -> None:
    store = make_store(tmp_path)

    result = store.upload_document(filename, b"document content")

    assert result.ok is True
    assert result.document is not None
    assert result.document.original_filename == filename
    assert result.document.file_type == file_type
    assert result.document.file_path.exists()
    assert result.document.file_path.parent == (tmp_path / "raw").resolve()
    assert result.document.status == STATUS_UPLOADED
    assert result.document.parse_status == PARSE_STATUS_PENDING
    assert result.document.index_status == INDEX_STATUS_NOT_INDEXED
    assert result.document.chunk_count == 0


def test_unsupported_document_type_is_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    with pytest.raises(UnsupportedDocumentTypeError):
        store.upload_document("archive.zip", b"content")


def test_duplicate_file_md5_is_not_saved_or_inserted(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1", "doc-2"])
    first = store.upload_document("first.txt", b"same content")

    duplicate = store.upload_document("second.txt", b"same content")

    assert first.ok is True
    assert duplicate.ok is False
    assert duplicate.document is None
    assert duplicate.duplicate_document == first.document
    assert "already exists" in duplicate.message
    assert len(store.list_documents()) == 1
    assert not (tmp_path / "raw" / "doc-2.txt").exists()


def test_documents_are_listed_newest_first(tmp_path: Path) -> None:
    store = make_store(
        tmp_path,
        ids=["doc-1", "doc-2"],
        times=[
            datetime(2026, 1, 1, tzinfo=UTC),
            datetime(2026, 1, 2, tzinfo=UTC),
        ],
    )
    store.upload_document("first.txt", b"first")
    store.upload_document("second.txt", b"second")

    documents = store.list_documents()

    assert [document.document_id for document in documents] == ["doc-2", "doc-1"]


def test_delete_document_removes_raw_file_metadata_and_vectors(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    upload = store.upload_document("delete-me.txt", b"content")
    assert upload.document is not None
    vector_store = FakeVectorStore()

    result = store.delete_document("doc-1", vector_store)

    assert result.ok is True
    assert result.deleted_vectors == 3
    assert vector_store.deleted_document_ids == ["doc-1"]
    assert not upload.document.file_path.exists()
    assert store.get_document("doc-1") is None


def test_delete_missing_document_raises_clear_error(tmp_path: Path) -> None:
    store = make_store(tmp_path)

    with pytest.raises(DocumentStoreError, match="Document not found"):
        store.delete_document("missing", FakeVectorStore())


def test_mark_reindex_requested_only_updates_status(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("reindex.txt", b"content")

    updated = store.mark_reindex_requested("doc-1")

    assert updated.parse_status == PARSE_STATUS_PENDING
    assert updated.index_status == INDEX_STATUS_PENDING
    assert updated.chunk_count == 0


def test_duplicate_document_is_not_reindexed_by_default(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("duplicate.txt", b"content")
    store.update_text_fingerprint("doc-1", "text-md5", duplicate_of_document_id="original-doc")

    with pytest.raises(DocumentStoreError, match="Duplicate documents are not re-indexed"):
        store.mark_reindex_requested("doc-1")


def test_module_five_can_update_text_fingerprint_status_and_chunk_count(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("future.txt", b"content")

    fingerprinted = store.update_text_fingerprint("doc-1", "text-md5")
    updated = store.update_processing_status(
        "doc-1",
        parse_status=PARSE_STATUS_PARSED,
        index_status=INDEX_STATUS_INDEXED,
        status=STATUS_UPLOADED,
        chunk_count=12,
    )

    assert fingerprinted.text_md5 == "text-md5"
    assert fingerprinted.duplicate_of_document_id is None
    assert updated.parse_status == PARSE_STATUS_PARSED
    assert updated.index_status == INDEX_STATUS_INDEXED
    assert updated.status == STATUS_UPLOADED
    assert updated.chunk_count == 12


def test_module_five_can_mark_text_duplicate(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("duplicate-body.txt", b"content")

    updated = store.update_text_fingerprint(
        "doc-1",
        "text-md5",
        duplicate_of_document_id="original-doc",
    )

    assert updated.text_md5 == "text-md5"
    assert updated.duplicate_of_document_id == "original-doc"
    assert updated.status == STATUS_DUPLICATE
    assert updated.is_duplicate is True


def test_negative_chunk_count_is_rejected(tmp_path: Path) -> None:
    store = make_store(tmp_path, ids=["doc-1"])
    store.upload_document("bad-count.txt", b"content")

    with pytest.raises(DocumentStoreError, match="chunk_count"):
        store.update_processing_status("doc-1", chunk_count=-1)


class FakeVectorStore:
    def __init__(self) -> None:
        self.deleted_document_ids: list[str] = []

    def delete_by_document_id(self, document_id: str) -> int:
        self.deleted_document_ids.append(document_id)
        return 3


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
