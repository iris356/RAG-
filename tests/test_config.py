from __future__ import annotations

from pathlib import Path

from rag_app.core.config import AppSettings, default_data_dir


def test_default_data_dir_points_to_project_data() -> None:
    assert default_data_dir().name == "data"


def test_settings_accept_environment_overrides(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("APP_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("APP_LOG_LEVEL", "DEBUG")

    settings = AppSettings()

    assert settings.data_dir == tmp_path
    assert settings.log_level == "DEBUG"
