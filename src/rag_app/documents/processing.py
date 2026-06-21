"""Document parsing, text deduplication, splitting, and indexing."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rag_app.core.exceptions import DocumentProcessingError
from rag_app.documents.store import (
    INDEX_STATUS_FAILED,
    INDEX_STATUS_INDEXED,
    INDEX_STATUS_NOT_INDEXED,
    INDEX_STATUS_PENDING,
    PARSE_STATUS_FAILED,
    PARSE_STATUS_PARSED,
    PARSE_STATUS_PENDING,
    STATUS_UPLOADED,
    DocumentRecord,
    DocumentStore,
)
from rag_app.vectors.store import VectorRecord, VectorStore, VectorWriteResult

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class ParsedDocument:
    """Text and metadata extracted from one loaded document segment."""

    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class DocumentProcessResult:
    """Result returned after parsing and optionally indexing one document."""

    ok: bool
    message: str
    document: DocumentRecord | None
    text_md5: str | None = None
    duplicate_of_document_id: str | None = None
    chunk_count: int = 0
    vector_write_result: VectorWriteResult | None = None
    deleted_vectors: int = 0


LoaderFactory = Callable[[Path], Any]
TextSplitterFactory = Callable[[], Any]


class DocumentProcessor:
    """Process stored documents into Chroma knowledge chunk vectors."""

    def __init__(
        self,
        *,
        document_store: DocumentStore,
        vector_store: VectorStore,
        loader_factories: dict[str, LoaderFactory] | None = None,
        text_splitter_factory: TextSplitterFactory | None = None,
    ) -> None:
        self.document_store = document_store
        self.vector_store = vector_store
        self.loader_factories = loader_factories or _default_loader_factories()
        self.text_splitter_factory = text_splitter_factory or _default_text_splitter

    def process_document(self, document_id: str, *, reindex: bool = False) -> DocumentProcessResult:
        """Parse, deduplicate, split, and index one stored document."""

        document = self.document_store.get_document(document_id)
        if document is None:
            raise DocumentProcessingError(f"Document not found: {document_id}")
        if document.duplicate_of_document_id:
            raise DocumentProcessingError(
                "Duplicate documents are not indexed by default. "
                f"Original document_id={document.duplicate_of_document_id}."
            )

        self.document_store.update_processing_status(
            document_id,
            parse_status=PARSE_STATUS_PENDING,
            index_status=INDEX_STATUS_PENDING,
        )

        try:
            parsed_documents = self._load_document(document)
            normalized_text = normalize_text(
                "\n".join(parsed.text for parsed in parsed_documents if parsed.text)
            )
            if not normalized_text:
                raise DocumentProcessingError("Parsed document text is empty.")
            text_md5 = calculate_text_md5(normalized_text)
        except Exception as exc:  # noqa: BLE001 - persist parse failure status.
            updated = self.document_store.update_processing_status(
                document_id,
                parse_status=PARSE_STATUS_FAILED,
                index_status=INDEX_STATUS_NOT_INDEXED,
                chunk_count=0,
            )
            return DocumentProcessResult(
                ok=False,
                message=f"Document parsing failed: {exc}",
                document=updated,
            )

        duplicate = self._find_text_duplicate(document_id, text_md5)
        if duplicate is not None:
            deleted_vectors = 0
            if reindex:
                deleted_vectors = self.vector_store.delete_by_document_id(document_id)
            fingerprinted = self.document_store.update_text_fingerprint(
                document_id,
                text_md5,
                duplicate_of_document_id=duplicate.document_id,
            )
            updated = self.document_store.update_processing_status(
                document_id,
                parse_status=PARSE_STATUS_PARSED,
                index_status=INDEX_STATUS_NOT_INDEXED,
                chunk_count=0,
            )
            return DocumentProcessResult(
                ok=True,
                message=(
                    "Document text duplicates an existing document; "
                    f"skipped indexing. Original document_id={duplicate.document_id}."
                ),
                document=updated,
                text_md5=fingerprinted.text_md5,
                duplicate_of_document_id=duplicate.document_id,
                deleted_vectors=deleted_vectors,
            )

        self.document_store.update_text_fingerprint(document_id, text_md5)

        try:
            records = self._build_vector_records(document, parsed_documents, text_md5)
            if not records:
                raise DocumentProcessingError("Document splitting produced no chunks.")
        except Exception as exc:  # noqa: BLE001 - persist split failure status.
            updated = self.document_store.update_processing_status(
                document_id,
                parse_status=PARSE_STATUS_PARSED,
                index_status=INDEX_STATUS_FAILED,
                chunk_count=0,
            )
            return DocumentProcessResult(
                ok=False,
                message=f"Document splitting failed: {exc}",
                document=updated,
                text_md5=text_md5,
            )

        deleted_vectors = 0
        if reindex:
            deleted_vectors = self.vector_store.delete_by_document_id(document_id)

        write_result = self.vector_store.add_knowledge_chunks(records)
        if not write_result.ok:
            updated = self.document_store.update_processing_status(
                document_id,
                parse_status=PARSE_STATUS_PARSED,
                index_status=INDEX_STATUS_FAILED,
                chunk_count=0,
            )
            return DocumentProcessResult(
                ok=False,
                message=write_result.message,
                document=updated,
                text_md5=text_md5,
                chunk_count=len(records),
                vector_write_result=write_result,
                deleted_vectors=deleted_vectors,
            )

        updated = self.document_store.update_processing_status(
            document_id,
            parse_status=PARSE_STATUS_PARSED,
            index_status=INDEX_STATUS_INDEXED,
            status=STATUS_UPLOADED,
            chunk_count=len(records),
        )
        return DocumentProcessResult(
            ok=True,
            message=write_result.message,
            document=updated,
            text_md5=text_md5,
            chunk_count=len(records),
            vector_write_result=write_result,
            deleted_vectors=deleted_vectors,
        )

    def _load_document(self, document: DocumentRecord) -> list[ParsedDocument]:
        try:
            loader_factory = self.loader_factories[document.file_type]
        except KeyError as exc:
            raise DocumentProcessingError(
                f"Unsupported document type for parsing: {document.file_type}"
            ) from exc

        if not document.file_path.exists():
            raise DocumentProcessingError(f"Raw document file is missing: {document.file_path}")

        loader = loader_factory(document.file_path)
        loaded_documents = loader.load()
        return [
            ParsedDocument(
                text=getattr(loaded, "page_content", "") or "",
                metadata=dict(getattr(loaded, "metadata", {}) or {}),
            )
            for loaded in loaded_documents
        ]

    def _find_text_duplicate(
        self,
        document_id: str,
        text_md5: str,
    ) -> DocumentRecord | None:
        for existing in self.document_store.list_documents():
            if existing.document_id == document_id:
                continue
            if existing.text_md5 != text_md5:
                continue
            if existing.duplicate_of_document_id:
                continue
            return existing
        return None

    def _build_vector_records(
        self,
        document: DocumentRecord,
        parsed_documents: Sequence[ParsedDocument],
        text_md5: str,
    ) -> list[VectorRecord]:
        splitter = self.text_splitter_factory()
        records: list[VectorRecord] = []

        for parsed in parsed_documents:
            normalized_segment = normalize_text(parsed.text)
            if not normalized_segment:
                continue
            chunks = splitter.split_text(normalized_segment)
            for chunk in chunks:
                chunk_text = chunk.strip()
                if not chunk_text:
                    continue
                chunk_index = len(records)
                records.append(
                    VectorRecord(
                        id=f"{document.document_id}:chunk:{chunk_index}",
                        text=chunk_text,
                        metadata=_build_chunk_metadata(
                            document,
                            parsed.metadata,
                            text_md5,
                            chunk_index,
                        ),
                    )
                )

        return records


def normalize_text(text: str) -> str:
    """Normalize parsed body text before fingerprinting or splitting."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    return re.sub(r"\s+", " ", normalized)


def calculate_text_md5(text: str) -> str:
    """Return the MD5 of normalized body text."""

    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _build_chunk_metadata(
    document: DocumentRecord,
    source_metadata: dict[str, Any],
    text_md5: str,
    chunk_index: int,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "document_id": document.document_id,
        "original_filename": document.original_filename,
        "file_type": document.file_type,
        "file_md5": document.file_md5,
        "text_md5": text_md5,
        "chunk_index": chunk_index,
    }
    for key in ("page", "source"):
        value = source_metadata.get(key)
        if value is not None:
            metadata[key] = value
    return metadata


def _default_loader_factories() -> dict[str, LoaderFactory]:
    return {
        "pdf": _pypdf_loader,
        "word": _docx_loader,
        "markdown": _text_loader,
        "txt": _text_loader,
    }


def _pypdf_loader(path: Path):
    try:
        from langchain_community.document_loaders import PyPDFLoader
    except ImportError as exc:
        raise DocumentProcessingError("Missing dependency for PDF parsing: pypdf") from exc
    return PyPDFLoader(str(path))


def _docx_loader(path: Path):
    try:
        from langchain_community.document_loaders import Docx2txtLoader
    except ImportError as exc:
        raise DocumentProcessingError("Missing dependency for DOCX parsing: docx2txt") from exc
    return Docx2txtLoader(str(path))


def _text_loader(path: Path):
    from langchain_community.document_loaders import TextLoader

    return TextLoader(str(path), encoding="utf-8", autodetect_encoding=True)


def _default_text_splitter():
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
