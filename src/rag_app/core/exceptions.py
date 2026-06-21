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
