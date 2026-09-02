"""Configuration contract tests."""

from pathlib import Path

from pytest import MonkeyPatch

from study_reader.config import Settings


def test_settings_use_environment_prefix(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("STUDY_READER_ENVIRONMENT", "test")
    monkeypatch.setenv("STUDY_READER_PUBLISHED_CONTENT_DIR", "/tmp/published")

    settings = Settings(_env_file=None)

    assert settings.environment == "test"
    assert settings.published_content_dir == Path("/tmp/published")
