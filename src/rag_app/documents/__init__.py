"""Document management services."""

from rag_app.documents.processing import (
    DocumentProcessResult,
    DocumentProcessor,
    calculate_text_md5,
    normalize_text,
)
from rag_app.documents.store import (
    DocumentDeleteResult,
    DocumentRecord,
    DocumentStore,
    DocumentUploadResult,
    initialize_document_store,
)

__all__ = [
    "DocumentDeleteResult",
    "DocumentProcessResult",
    "DocumentProcessor",
    "DocumentRecord",
    "DocumentStore",
    "DocumentUploadResult",
    "calculate_text_md5",
    "initialize_document_store",
    "normalize_text",
]
