"""SQLite-backed document metadata and raw file management."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from rag_app.core.exceptions import DocumentStoreError, UnsupportedDocumentTypeError

DATABASE_FILENAME = "rag_app.sqlite3"

STATUS_UPLOADED = "uploaded"
STATUS_DUPLICATE = "duplicate"

PARSE_STATUS_PENDING = "pending"
PARSE_STATUS_PARSED = "parsed"
PARSE_STATUS_FAILED = "failed"

INDEX_STATUS_NOT_INDEXED = "not_indexed"
INDEX_STATUS_PENDING = "pending"
INDEX_STATUS_INDEXED = "indexed"
INDEX_STATUS_FAILED = "failed"

SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".docx": "word",
    ".md": "markdown",
    ".markdown": "markdown",
    ".txt": "txt",
}


@dataclass(frozen=True)
class DocumentRecord:
    """Stored document metadata."""

    document_id: str
    original_filename: str
    stored_filename: str
    file_path: Path
    file_type: str
    file_size: int
    file_md5: str
    text_md5: str | None
    duplicate_of_document_id: str | None
    status: str
    parse_status: str
    index_status: str
    chunk_count: int
    created_at: str
    updated_at: str

    @property
    def is_duplicate(self) -> bool:
        """Return whether this document is marked as duplicate content."""

        return bool(self.duplicate_of_document_id)


@dataclass(frozen=True)
class DocumentUploadResult:
    """Result returned after attempting to upload a document."""

    ok: bool
    message: str
    document: DocumentRecord | None
    duplicate_document: DocumentRecord | None = None


@dataclass(frozen=True)
class DocumentDeleteResult:
    """Result returned after deleting a document."""

    ok: bool
    message: str
    document_id: str
    deleted_vectors: int


class DocumentStore:
    """Manage raw document files and SQLite metadata."""

    def __init__(
        self,
        *,
        sqlite_dir: Path,
        raw_dir: Path,
        now_factory: Callable[[], datetime] | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.sqlite_dir = sqlite_dir
        self.raw_dir = raw_dir
        self.database_path = get_document_database_path(sqlite_dir)
        self._now_factory = now_factory or (lambda: datetime.now(UTC))
        self._id_factory = id_factory or (lambda: uuid.uuid4().hex)

    def initialize(self) -> Path:
        """Create storage directories and the document metadata table."""

        try:
            self.sqlite_dir.mkdir(parents=True, exist_ok=True)
            self.raw_dir.mkdir(parents=True, exist_ok=True)
            with self._connect() as connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT PRIMARY KEY,
                        original_filename TEXT NOT NULL,
                        stored_filename TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        file_type TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        file_md5 TEXT NOT NULL UNIQUE,
                        text_md5 TEXT,
                        duplicate_of_document_id TEXT,
                        status TEXT NOT NULL,
                        parse_status TEXT NOT NULL,
                        index_status TEXT NOT NULL,
                        chunk_count INTEGER NOT NULL DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                connection.execute(
                    "CREATE INDEX IF NOT EXISTS idx_documents_text_md5 ON documents(text_md5)"
                )
                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_documents_duplicate_of
                    ON documents(duplicate_of_document_id)
                    """
                )
        except OSError as exc:
            raise DocumentStoreError(f"Failed to initialize document directories: {exc}") from exc
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to initialize document database: {exc}") from exc

        return self.database_path

    def upload_document(self, filename: str, content_bytes: bytes) -> DocumentUploadResult:
        """Save a raw document and create metadata unless the file already exists."""

        extension = _normalized_extension(filename)
        file_type = _file_type_from_extension(extension)
        file_md5 = _md5(content_bytes)
        self.initialize()

        duplicate = self.get_document_by_file_md5(file_md5)
        if duplicate:
            return DocumentUploadResult(
                ok=False,
                message=(
                    "Document already exists; the uploaded file was not saved again. "
                    f"Existing document_id={duplicate.document_id}."
                ),
                document=None,
                duplicate_document=duplicate,
            )

        document_id = self._id_factory()
        stored_filename = f"{document_id}{extension}"
        file_path = (self.raw_dir / stored_filename).resolve()
        now = self._now()

        try:
            file_path.write_bytes(content_bytes)
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO documents (
                        document_id,
                        original_filename,
                        stored_filename,
                        file_path,
                        file_type,
                        file_size,
                        file_md5,
                        text_md5,
                        duplicate_of_document_id,
                        status,
                        parse_status,
                        index_status,
                        chunk_count,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, 0, ?, ?)
                    """,
                    (
                        document_id,
                        Path(filename).name,
                        stored_filename,
                        str(file_path),
                        file_type,
                        len(content_bytes),
                        file_md5,
                        STATUS_UPLOADED,
                        PARSE_STATUS_PENDING,
                        INDEX_STATUS_NOT_INDEXED,
                        now,
                        now,
                    ),
                )
        except OSError as exc:
            raise DocumentStoreError(f"Failed to save raw document: {exc}") from exc
        except sqlite3.Error as exc:
            if file_path.exists():
                file_path.unlink(missing_ok=True)
            raise DocumentStoreError(f"Failed to save document metadata: {exc}") from exc

        document = self.get_document(document_id)
        if document is None:
            raise DocumentStoreError("Document metadata was not found after upload.")
        return DocumentUploadResult(
            ok=True,
            message=f"Document uploaded: {document.original_filename}.",
            document=document,
        )

    def list_documents(self) -> list[DocumentRecord]:
        """Return all document records, newest first."""

        self.initialize()
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT * FROM documents
                    ORDER BY created_at DESC, document_id DESC
                    """
                ).fetchall()
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to list documents: {exc}") from exc
        return [_record_from_row(row) for row in rows]

    def get_document(self, document_id: str) -> DocumentRecord | None:
        """Return one document by ID."""

        self.initialize()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM documents WHERE document_id = ?",
                    (document_id,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to get document: {exc}") from exc
        return _record_from_row(row) if row else None

    def get_document_by_file_md5(self, file_md5: str) -> DocumentRecord | None:
        """Return the document with the matching raw file fingerprint."""

        self.initialize()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    "SELECT * FROM documents WHERE file_md5 = ?",
                    (file_md5,),
                ).fetchone()
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to check duplicate document: {exc}") from exc
        return _record_from_row(row) if row else None

    def delete_document(self, document_id: str, vector_store) -> DocumentDeleteResult:
        """Delete one document, its raw file, and its knowledge vectors."""

        self.initialize()
        document = self.get_document(document_id)
        if document is None:
            raise DocumentStoreError(f"Document not found: {document_id}")

        deleted_vectors = vector_store.delete_by_document_id(document_id)
        try:
            document.file_path.unlink(missing_ok=True)
            with self._connect() as connection:
                connection.execute(
                    "DELETE FROM documents WHERE document_id = ?",
                    (document_id,),
                )
        except OSError as exc:
            raise DocumentStoreError(f"Failed to delete raw document: {exc}") from exc
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to delete document metadata: {exc}") from exc

        return DocumentDeleteResult(
            ok=True,
            message=f"Deleted document {document_id}.",
            document_id=document_id,
            deleted_vectors=deleted_vectors,
        )

    def mark_reindex_requested(self, document_id: str) -> DocumentRecord:
        """Mark one document for future parse and indexing work."""

        document = self.get_document(document_id)
        if document is None:
            raise DocumentStoreError(f"Document not found: {document_id}")
        if document.duplicate_of_document_id:
            raise DocumentStoreError(
                "Duplicate documents are not re-indexed by default. "
                f"Original document_id={document.duplicate_of_document_id}."
            )

        return self.update_processing_status(
            document_id,
            parse_status=PARSE_STATUS_PENDING,
            index_status=INDEX_STATUS_PENDING,
        )

    def update_text_fingerprint(
        self,
        document_id: str,
        text_md5: str,
        duplicate_of_document_id: str | None = None,
    ) -> DocumentRecord:
        """Write the parsed text fingerprint and optional duplicate link."""

        status = STATUS_DUPLICATE if duplicate_of_document_id else STATUS_UPLOADED
        return self._update_document(
            document_id,
            {
                "text_md5": text_md5,
                "duplicate_of_document_id": duplicate_of_document_id,
                "status": status,
            },
        )

    def update_processing_status(
        self,
        document_id: str,
        *,
        parse_status: str | None = None,
        index_status: str | None = None,
        status: str | None = None,
        chunk_count: int | None = None,
    ) -> DocumentRecord:
        """Update parse/index status fields for later modules."""

        updates: dict[str, str | int | None] = {}
        if parse_status is not None:
            updates["parse_status"] = parse_status
        if index_status is not None:
            updates["index_status"] = index_status
        if status is not None:
            updates["status"] = status
        if chunk_count is not None:
            if chunk_count < 0:
                raise DocumentStoreError("chunk_count must not be negative.")
            updates["chunk_count"] = chunk_count
        if not updates:
            document = self.get_document(document_id)
            if document is None:
                raise DocumentStoreError(f"Document not found: {document_id}")
            return document
        return self._update_document(document_id, updates)

    def _update_document(
        self,
        document_id: str,
        updates: dict[str, str | int | None],
    ) -> DocumentRecord:
        self.initialize()
        if self.get_document(document_id) is None:
            raise DocumentStoreError(f"Document not found: {document_id}")

        assignments = [f"{column} = ?" for column in updates]
        values = list(updates.values())
        assignments.append("updated_at = ?")
        values.append(self._now())
        values.append(document_id)

        try:
            with self._connect() as connection:
                connection.execute(
                    f"UPDATE documents SET {', '.join(assignments)} WHERE document_id = ?",
                    values,
                )
        except sqlite3.Error as exc:
            raise DocumentStoreError(f"Failed to update document metadata: {exc}") from exc

        document = self.get_document(document_id)
        if document is None:
            raise DocumentStoreError(f"Document not found after update: {document_id}")
        return document

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _now(self) -> str:
        return self._now_factory().astimezone(UTC).replace(microsecond=0).isoformat()


def initialize_document_store(sqlite_dir: Path) -> Path:
    """Initialize the document SQLite database and return its path."""

    database_path = get_document_database_path(sqlite_dir)
    sqlite_dir.mkdir(parents=True, exist_ok=True)
    store = DocumentStore(sqlite_dir=sqlite_dir, raw_dir=sqlite_dir.parent / "raw")
    return store.initialize() if store.database_path == database_path else database_path


def get_document_database_path(sqlite_dir: Path) -> Path:
    """Return the resolved SQLite database path for document metadata."""

    return sqlite_dir.expanduser().resolve() / DATABASE_FILENAME


def _record_from_row(row: sqlite3.Row) -> DocumentRecord:
    return DocumentRecord(
        document_id=row["document_id"],
        original_filename=row["original_filename"],
        stored_filename=row["stored_filename"],
        file_path=Path(row["file_path"]),
        file_type=row["file_type"],
        file_size=row["file_size"],
        file_md5=row["file_md5"],
        text_md5=row["text_md5"],
        duplicate_of_document_id=row["duplicate_of_document_id"],
        status=row["status"],
        parse_status=row["parse_status"],
        index_status=row["index_status"],
        chunk_count=row["chunk_count"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _normalized_extension(filename: str) -> str:
    extension = Path(filename).suffix.lower()
    if not extension:
        raise UnsupportedDocumentTypeError("Uploaded document has no file extension.")
    return extension


def _file_type_from_extension(extension: str) -> str:
    try:
        return SUPPORTED_EXTENSIONS[extension]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise UnsupportedDocumentTypeError(
            f"Unsupported document type: {extension}. Supported extensions: {supported}."
        ) from exc


def _md5(content_bytes: bytes) -> str:
    return hashlib.md5(content_bytes).hexdigest()
