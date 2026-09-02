"""Shared test fixtures."""

from pathlib import Path

import pytest

from study_reader.config import Settings


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Return isolated, validated application settings."""

    return Settings(environment="test", published_content_dir=tmp_path)
