"""Safe, stable Markdown rendering tests."""

from pathlib import Path

from study_reader.content.markdown import render_markdown

FIXTURE = Path("tests/content/fixtures/representative.md")


def test_renderer_assigns_deterministic_ids_to_reflowable_blocks() -> None:
    rendered = render_markdown(FIXTURE.read_text())

    assert 'id="orientation"' in rendered
    assert 'id="key-idea"' in rendered
    assert 'id="orientation-list-1"' in rendered
    assert 'id="orientation-table-1"' in rendered
    assert 'id="orientation-code-1"' in rendered
    assert rendered == render_markdown(FIXTURE.read_text())


def test_explicit_block_id_survives_ordinary_text_edits() -> None:
    before = "<!-- block-id: durable -->\nA short explanation."
    after = "<!-- block-id: durable -->\nA clearer and longer explanation."

    assert 'id="durable"' in render_markdown(before)
    assert 'id="durable"' in render_markdown(after)


def test_renderer_removes_raw_html_scripts_and_unsafe_urls() -> None:
    rendered = render_markdown(
        '<script>alert("x")</script>\n\n'
        '<img src=x onerror="alert(1)">\n\n'
        "[unsafe](javascript:alert(1))"
    )

    assert "<script" not in rendered
    assert "<img" not in rendered
    assert 'href="javascript:' not in rendered
    assert "&lt;img src=x onerror=" in rendered


def test_external_links_explain_destination_and_open_safely() -> None:
    rendered = render_markdown(
        "Read [Microsoft Learn](https://learn.microsoft.com/fabric)."
    )

    assert 'target="_blank"' in rendered
    assert 'rel="noopener noreferrer"' in rendered
    assert 'data-external-host="learn.microsoft.com"' in rendered
    assert 'title="Opens learn.microsoft.com in a new tab"' in rendered


def test_representative_chapter_matches_golden_html() -> None:
    expected = Path("tests/content/fixtures/representative.html").read_text().strip()

    assert render_markdown(FIXTURE.read_text()).strip() == expected
