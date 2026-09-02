"""Reader vertical-slice integration tests."""

from pathlib import Path

from fastapi.testclient import TestClient

from study_reader.config import Settings
from study_reader.reader.app import create_app


def reader_client() -> TestClient:
    settings = Settings(
        environment="test",
        published_content_dir=Path("content/published"),
    )
    return TestClient(create_app(settings))


def test_home_opens_the_first_dp700_chapter() -> None:
    with reader_client() as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/books/dp700/chapters/workspace-settings"


def test_chapter_page_contains_mobile_reader_landmarks() -> None:
    with reader_client() as client:
        response = client.get("/books/dp700/chapters/workspace-settings")

    assert response.status_code == 200
    assert (
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        in response.text
    )
    assert 'class="reader-layout"' in response.text
    assert 'class="toc-details" open' in response.text
    assert 'aria-label="DP-700 table of contents"' in response.text
    assert 'id="appearance-button"' in response.text
    assert 'id="appearance-dialog"' in response.text
    assert 'id="chapter-progress-value"' in response.text
    assert 'id="book-progress-value"' in response.text
    assert 'id="chapter-complete-button"' in response.text
    assert "Configure Microsoft Fabric workspace settings" in response.text
    assert "Open official DP-700 study guide" in response.text
    assert "Copy Markdown" not in response.text


def test_unknown_book_and_chapter_return_not_found() -> None:
    with reader_client() as client:
        assert client.get("/books/missing/chapters/anything").status_code == 404
        assert client.get("/books/dp700/chapters/missing").status_code == 404
