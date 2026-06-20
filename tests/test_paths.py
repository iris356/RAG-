from __future__ import annotations

from pathlib import Path

from rag_app.core.paths import ensure_data_directories, get_data_directories


def test_get_data_directories_returns_expected_paths(tmp_path: Path) -> None:
    directories = get_data_directories(tmp_path)

    assert directories.root == tmp_path.resolve()
    assert directories.raw == tmp_path.resolve() / "raw"
    assert directories.chroma == tmp_path.resolve() / "chroma"
    assert directories.sqlite == tmp_path.resolve() / "sqlite"
    assert directories.tmp == tmp_path.resolve() / "tmp"


def test_ensure_data_directories_creates_directories(tmp_path: Path) -> None:
    directories = ensure_data_directories(tmp_path)

    assert directories.raw.is_dir()
    assert directories.chroma.is_dir()
    assert directories.sqlite.is_dir()
    assert directories.tmp.is_dir()
