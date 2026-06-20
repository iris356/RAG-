"""Data directory helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rag_app.core.exceptions import DataDirectoryError


@dataclass(frozen=True)
class DataDirectories:
    """Resolved application data directories."""

    root: Path
    raw: Path
    chroma: Path
    sqlite: Path
    tmp: Path


def get_data_directories(data_root: Path) -> DataDirectories:
    """Build the application data directory set."""

    root = data_root.expanduser().resolve()
    return DataDirectories(
        root=root,
        raw=root / "raw",
        chroma=root / "chroma",
        sqlite=root / "sqlite",
        tmp=root / "tmp",
    )


def ensure_data_directories(data_root: Path) -> DataDirectories:
    """Ensure all required data directories exist."""

    directories = get_data_directories(data_root)
    try:
        for path in (
            directories.root,
            directories.raw,
            directories.chroma,
            directories.sqlite,
            directories.tmp,
        ):
            path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise DataDirectoryError(f"Failed to create data directory: {exc}") from exc

    return directories
