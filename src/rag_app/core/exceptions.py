"""Project-level exceptions."""

from __future__ import annotations


class RagAppError(Exception):
    """Base exception for expected application errors."""


class ConfigurationError(RagAppError):
    """Raised when application configuration is invalid."""


class DataDirectoryError(RagAppError):
    """Raised when data directories cannot be created or accessed."""


class VectorStoreError(RagAppError):
    """Raised when vector storage or retrieval fails."""


class DocumentStoreError(RagAppError):
    """Raised when document metadata or file storage fails."""


class UnsupportedDocumentTypeError(DocumentStoreError):
    """Raised when an uploaded document type is not supported."""


class DuplicateDocumentError(DocumentStoreError):
    """Raised when a document duplicates an existing stored document."""
