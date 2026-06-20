from __future__ import annotations

from rag_app.core.exceptions import ConfigurationError, DataDirectoryError, RagAppError


def test_project_exceptions_can_be_instantiated() -> None:
    assert isinstance(ConfigurationError("bad config"), RagAppError)
    assert isinstance(DataDirectoryError("bad directory"), RagAppError)
