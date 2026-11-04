from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

from .diagnostics import Diagnostic
from .structured import (
    ExtractionPolicy,
    NavigationEntry,
    StructuredEpubExtraction,
    TextBlock,
)


@dataclass(frozen=True)
class ChapterMarkdownOptions:
    flavor: Literal["commonmark", "gfm"] = "commonmark"
    include_title: bool = False
    title_level: int = 1
    minimum_body_heading_level: int = 2
    deduplicate_source_title: bool = True
    preserve_emphasis: bool = True
    preserve_strong: bool = True
    link_mode: Literal["preserve", "unwrap"] = "preserve"
    code_mode: Literal["preserve", "unwrap"] = "preserve"
    resolve_css_emphasis: bool = True
    preserve_scene_breaks: bool = True


@dataclass(frozen=True)
class ChapterDocument:
    id: str
    href: str | None
    title: str
    parent_id: str | None
    level: int
    text: str
    markdown_body: str
    char_count: int
    source_block_ids: tuple[str, ...]
    diagnostics: tuple[Diagnostic, ...]

    def to_markdown(self, *, include_title: bool = True, title_level: int = 1) -> str:
        body = self.markdown_body.rstrip("\n")
        if not include_title:
            return f"{body}\n" if body else ""
        level = max(1, min(6, title_level))
        heading = f"{'#' * level} {_escape_heading(self.title)}".rstrip()
        return f"{heading}\n\n{body}\n" if body else f"{heading}\n"


def _escape_heading(value: str) -> str:
    return re.sub(r"([\\\x60*_{}\[\]<>|~])", r"\\\1", value.strip())


def _visible_normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"[\s\u00a0]+", " ", value).strip().casefold()
    return "".join(ch for ch in value if not unicodedata.category(ch).startswith("P"))


def _attrs(block: TextBlock) -> dict[str, str]:
    return {name.lower(): value for name, value in block.attrs}


def _is_heading(block: TextBlock) -> bool:
    attrs = _attrs(block)
    if block.tag_name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        return True
    if attrs.get("role", "").lower() == "heading":
        return attrs.get("aria-level", "").isdigit()
    epub_type = attrs.get("epub:type", "").lower().split()
    return any(token in {"heading", "title", "chapter", "part"} for token in epub_type)


def _source_heading_level(block: TextBlock) -> int:
    if block.tag_name.startswith("h") and block.tag_name[1:].isdigit():
        return int(block.tag_name[1:])
    attrs = _attrs(block)
    try:
        return int(attrs.get("aria-level", "1"))
    except ValueError:
        return 1


def _inline_markdown(block: TextBlock) -> str:
    fragment = block.markdown_fragment
    return (fragment.markdown if fragment is not None else block.text).strip()


def _effective_policy(
    options: ChapterMarkdownOptions, policy: ExtractionPolicy | None
) -> ExtractionPolicy:
    from dataclasses import replace

    base = policy or ExtractionPolicy()
    return replace(
        base,
        markdown_flavor=options.flavor,
        markdown_emphasis="preserve" if options.preserve_emphasis else "unwrap",
        markdown_strong="preserve" if options.preserve_strong else "unwrap",
        markdown_links=options.link_mode,
        markdown_code=options.code_mode,
        resolve_css_emphasis=options.resolve_css_emphasis,
    )


def _render_block(
    block: TextBlock,
    options: ChapterMarkdownOptions,
    heading_base: int | None,
    diagnostics: list[Diagnostic],
) -> str:
    tag = block.tag_name
    inline = _inline_markdown(block)
    if tag == "hr":
        return "---" if options.preserve_scene_breaks else ""
    if _is_heading(block):
        source_level = _source_heading_level(block)
        if heading_base is None:
            heading_base = source_level
        level = options.minimum_body_heading_level + source_level - heading_base
        if source_level > heading_base + 1:
            diagnostics.append(
                Diagnostic(
                    "info",
                    "chapter_heading_level_normalized",
                    (
                        f"Normalized heading level jump from h{heading_base} "
                        f"to h{source_level}."
                    ),
                    block.document_href,
                    block.outer_char_start,
                    block.outer_char_end,
                )
            )
        level = max(1, min(6, level))
        return f"{'#' * level} {inline}".rstrip()
    if tag == "blockquote":
        return "\n".join(f"> {line}".rstrip() for line in inline.splitlines())
    if tag == "li":
        return f"- {inline}".rstrip()
    if tag == "dd":
        return "\n".join(f"    {line}".rstrip() for line in inline.splitlines())
    if tag == "dt":
        return inline
    if tag in {"p", "figcaption", "caption", "td", "th"}:
        return inline
    diagnostics.append(
        Diagnostic(
            "warning",
            "chapter_unknown_block",
            f"Rendered unknown text-bearing block as a paragraph: {tag}",
            block.document_href,
            block.outer_char_start,
            block.outer_char_end,
        )
    )
    return inline


def _chapter_document(
    entry: NavigationEntry | None,
    blocks: list[TextBlock],
    options: ChapterMarkdownOptions,
    *,
    synthetic_id: str | None = None,
    synthetic_title: str | None = None,
) -> ChapterDocument:
    diagnostics: list[Diagnostic] = []
    selected = list(blocks)
    title = entry.title if entry is not None else (synthetic_title or "Document")
    if options.deduplicate_source_title and entry is not None:
        first = next((block for block in selected if block.text.strip()), None)
        if (
            first is not None
            and _is_heading(first)
            and _visible_normalized(first.text) == _visible_normalized(title)
        ):
            selected.remove(first)
            diagnostics.append(
                Diagnostic(
                    "info",
                    "chapter_source_title_omitted",
                    (
                        "Omitted a semantic source heading duplicated by the "
                        "navigation title."
                    ),
                    first.document_href,
                    first.outer_char_start,
                    first.outer_char_end,
                )
            )

    heading_base = None
    source_headings = [block for block in selected if _is_heading(block)]
    if source_headings:
        heading_base = _source_heading_level(source_headings[0])
    rendered: list[str] = []
    visible: list[str] = []
    source_ids: list[str] = []
    for block in selected:
        source_ids.append(block.id)
        if block.text.strip():
            visible.append(block.text.strip())
        rendered_block = _render_block(block, options, heading_base, diagnostics)
        if rendered_block:
            rendered.append(rendered_block)
    text = "\n\n".join(visible)
    markdown_body = "\n\n".join(rendered)
    if markdown_body:
        markdown_body += "\n"
    return ChapterDocument(
        id=entry.id if entry is not None else (synthetic_id or "synthetic:chapter"),
        href=entry.href if entry is not None else None,
        title=title,
        parent_id=entry.parent_id if entry is not None else None,
        level=entry.level if entry is not None else 1,
        text=text,
        markdown_body=markdown_body,
        char_count=len(text),
        source_block_ids=tuple(source_ids),
        diagnostics=tuple(diagnostics),
    )


def assemble_chapter_documents(
    extraction: StructuredEpubExtraction,
    *,
    options: ChapterMarkdownOptions,
) -> list[ChapterDocument]:
    entries = [
        entry
        for entry in extraction.navigation
        if entry.source != "fallback" and not (entry.href or "").startswith("internal:")
    ]
    grouped: dict[str, list[TextBlock]] = {entry.id: [] for entry in entries}
    unassigned: list[TextBlock] = []
    blocks = sorted(
        extraction.blocks,
        key=lambda block: (
            block.spine_index if block.spine_index is not None else 10**9,
            block.block_index,
            block.outer_char_start,
        ),
    )
    for block in blocks:
        if block.chapter_id in grouped:
            grouped[block.chapter_id].append(block)
        else:
            unassigned.append(block)

    documents: list[ChapterDocument] = []
    if not entries:
        by_document: dict[str, list[TextBlock]] = {}
        for block in unassigned:
            by_document.setdefault(block.document_id, []).append(block)
        for index, (document_id, document_blocks) in enumerate(by_document.items()):
            href = document_blocks[0].document_href if document_blocks else None
            documents.append(
                _chapter_document(
                    None,
                    document_blocks,
                    options,
                    synthetic_id=f"synthetic:spine:{document_id}",
                    synthetic_title=href or f"Document {index + 1}",
                )
            )
        return documents

    first_assigned = next(
        (block for block in blocks if block.chapter_id in grouped), None
    )
    if first_assigned is not None:
        prefix = [
            block
            for block in unassigned
            if (block.spine_index, block.outer_char_start)
            < (first_assigned.spine_index, first_assigned.outer_char_start)
        ]
    else:
        prefix = unassigned
    if prefix:
        documents.append(
            _chapter_document(
                None,
                prefix,
                options,
                synthetic_id="synthetic:prefix",
                synthetic_title="Introduction",
            )
        )
    for entry in sorted(entries, key=lambda item: item.order):
        documents.append(_chapter_document(entry, grouped[entry.id], options))
    return documents


def extract_epub_chapters(
    filepath: str,
    *,
    options: ChapterMarkdownOptions | None = None,
    policy: ExtractionPolicy | None = None,
) -> list[ChapterDocument]:
    from .parser import EPUBParser

    return EPUBParser(filepath).get_chapter_documents(options=options, policy=policy)
