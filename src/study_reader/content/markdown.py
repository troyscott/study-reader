"""Render authored Markdown as sanitized HTML with stable block anchors."""

import html
import re
from collections import defaultdict
from collections.abc import Sequence
from urllib.parse import urlparse

import nh3
from markdown_it import MarkdownIt
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict

BLOCK_MARKER = re.compile(r"^\s*<!--\s*block-id:\s*([a-z0-9][a-z0-9-]*)\s*-->\s*$")
BLOCK_TYPES = {
    "heading_open": "heading",
    "paragraph_open": "paragraph",
    "bullet_list_open": "list",
    "ordered_list_open": "list",
    "table_open": "table",
    "fence": "code",
}
ALLOWED_TAGS = {
    "a",
    "blockquote",
    "code",
    "del",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "li",
    "ol",
    "p",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "th",
    "thead",
    "tr",
    "ul",
}
ALLOWED_ATTRIBUTES = {
    "*": {"id"},
    "a": {"href", "target", "rel", "title", "data-external-host"},
    "code": {"class"},
}


def slugify(value: str) -> str:
    """Create a stable lowercase identifier suitable for an HTML id."""

    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "section"


def extract_markers(markdown: str) -> tuple[str, list[tuple[int, str]]]:
    """Remove explicit block markers while preserving source line positions."""

    markers: list[tuple[int, str]] = []
    cleaned_lines: list[str] = []
    for line_number, line in enumerate(markdown.splitlines()):
        marker = BLOCK_MARKER.fullmatch(line)
        if marker:
            markers.append((line_number, marker.group(1)))
            cleaned_lines.append("")
        else:
            cleaned_lines.append(line)
    return "\n".join(cleaned_lines), markers


def inline_text(tokens: Sequence[Token], start_index: int) -> str:
    """Return the inline content immediately following a heading token."""

    for token in tokens[start_index + 1 :]:
        if token.type == "inline":
            return token.content
        if token.type == "heading_close":
            break
    return "section"


def assign_block_ids(tokens: list[Token], markers: list[tuple[int, str]]) -> None:
    """Attach deterministic or explicit IDs to rendered block tokens."""

    marker_index = 0
    pending_marker: str | None = None
    current_section = "opening"
    counters: defaultdict[tuple[str, str], int] = defaultdict(int)
    used_ids: set[str] = set()

    for index, token in enumerate(tokens):
        if token.type not in BLOCK_TYPES or token.level != 0:
            continue

        start_line = token.map[0] if token.map else -1
        while marker_index < len(markers) and markers[marker_index][0] < start_line:
            pending_marker = markers[marker_index][1]
            marker_index += 1

        block_type = BLOCK_TYPES[token.type]
        if pending_marker:
            block_id = pending_marker
            pending_marker = None
        elif block_type == "heading":
            block_id = slugify(inline_text(tokens, index))
            current_section = block_id
        else:
            counters[(current_section, block_type)] += 1
            block_id = (
                f"{current_section}-{block_type}-"
                f"{counters[(current_section, block_type)]}"
            )

        unique_id = block_id
        duplicate_index = 2
        while unique_id in used_ids:
            unique_id = f"{block_id}-{duplicate_index}"
            duplicate_index += 1
        token.attrSet("id", unique_id)
        used_ids.add(unique_id)


def render_link_open(
    renderer: RendererHTML,
    tokens: Sequence[Token],
    index: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Make external link behavior explicit, safe, and understandable."""

    token = tokens[index]
    href = str(token.attrGet("href") or "")
    destination = urlparse(href)
    if destination.scheme in {"http", "https"} and destination.hostname:
        hostname = destination.hostname.lower()
        token.attrSet("target", "_blank")
        token.attrSet("rel", "noopener noreferrer")
        token.attrSet("data-external-host", hostname)
        token.attrSet("title", f"Opens {hostname} in a new tab")
    return renderer.renderToken(tokens, index, options, env)


def render_fence(
    renderer: RendererHTML,
    tokens: Sequence[Token],
    index: int,
    options: OptionsDict,
    env: EnvType,
) -> str:
    """Render fenced code with an anchor on the scrollable outer block."""

    del renderer, options, env
    token = tokens[index]
    block_id = html.escape(str(token.attrGet("id") or "code"))
    language = (
        slugify(token.info.strip().split(maxsplit=1)[0]) if token.info else "text"
    )
    code = html.escape(token.content)
    return (
        f'<pre id="{block_id}"><code class="language-{language}">{code}</code></pre>\n'
    )


def markdown_parser() -> MarkdownIt:
    """Build the documented CommonMark parser with only required extensions."""

    parser = MarkdownIt("commonmark", {"html": False, "linkify": False})
    parser.enable("table")
    parser.add_render_rule("link_open", render_link_open)
    parser.add_render_rule("fence", render_fence)
    return parser


def render_markdown(markdown: str) -> str:
    """Render Markdown and enforce the final HTML security allowlist."""

    cleaned_markdown, markers = extract_markers(markdown)
    parser = markdown_parser()
    tokens = parser.parse(cleaned_markdown)
    assign_block_ids(tokens, markers)
    rendered = parser.renderer.render(tokens, parser.options, {})
    return nh3.clean(
        rendered,
        tags=ALLOWED_TAGS,
        clean_content_tags={"script", "style"},
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto"},
        link_rel=None,
        strip_comments=True,
    )
