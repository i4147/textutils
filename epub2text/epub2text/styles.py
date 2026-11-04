from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from typing import Any

from .diagnostics import Diagnostic
from .inline_spans import InlineSpan, build_inline_spans
from .structured import SourceDocument, TextBlock


@dataclass(frozen=True)
class _Rule:
    selector: str
    declarations: tuple[tuple[str, str, bool], ...]
    specificity: tuple[int, int, int]
    order: int


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _declarations(body: str) -> tuple[tuple[str, str, bool], ...]:
    result: list[tuple[str, str, bool]] = []
    for item in body.split(";"):
        if ":" not in item:
            continue
        name, value = item.split(":", 1)
        name = name.strip().lower()
        value = value.strip()
        important = bool(re.search(r"\s*!important\s*$", value, re.I))
        value = re.sub(r"\s*!important\s*$", "", value, flags=re.I).strip().lower()
        if name in {"font-style", "font-weight"}:
            result.append((name, value, important))
    return tuple(result)


def _specificity(selector: str) -> tuple[int, int, int]:
    return (
        len(re.findall(r"#[\w-]+", selector)),
        len(re.findall(r"\.[\w-]+|\[[^\]]+\]|:[\w-]+", selector)),
        len(re.findall(r"(?<![#.:\w])[\w*-]+", selector)),
    )


def _simple_matches(simple: str, tag: str, attrs: dict[str, str]) -> bool:
    simple = simple.strip()
    if not simple:
        return True
    name = re.match(r"^[\w*-]+", simple)
    if name and name.group(0) not in {"*", tag}:
        return False
    for value in re.findall(r"#([\w-]+)", simple):
        if attrs.get("id") != value:
            return False
    classes = set(attrs.get("class", "").split())
    for value in re.findall(r"\.([\w-]+)", simple):
        if value not in classes:
            return False
    for name_value, value in re.findall(
        r"\[\s*([\w:-]+)\s*(?:=\s*[\"']?([^\"'\]]+)[\"']?)?\s*\]", simple
    ):
        if name_value.lower() not in attrs:
            return False
        if value and attrs.get(name_value.lower()) != value:
            return False
    return True


def _matches(
    selector: str,
    tag: str,
    attrs: dict[str, str],
    ancestors: list[tuple[str, dict[str, str]]],
) -> bool:
    parts = selector.strip().split()
    if not parts or not _simple_matches(parts[-1], tag, attrs):
        return False
    ancestor_index = len(ancestors) - 1
    for part in reversed(parts[:-1]):
        found = False
        while ancestor_index >= 0:
            if _simple_matches(
                part, ancestors[ancestor_index][0], ancestors[ancestor_index][1]
            ):
                found = True
                ancestor_index -= 1
                break
            ancestor_index -= 1
        if not found:
            return False
    return True


def _parse_rules(
    css: str, diagnostics: list[Diagnostic], href: str | None
) -> list[_Rule]:
    css = _strip_comments(css)
    rules: list[_Rule] = []
    order = 0
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css, re.S):
        selector_text, body = match.group(1).strip(), match.group(2)
        if selector_text.startswith("@"):
            continue
        declarations = _declarations(body)
        if not declarations:
            continue
        for selector in selector_text.split(","):
            selector = selector.strip()
            if not selector or any(ch in selector for ch in "+>~"):
                diagnostics.append(
                    Diagnostic(
                        "info",
                        "css_unsupported_selector",
                        f"Skipped unsupported CSS selector {selector!r}.",
                        href,
                    )
                )
                continue
            rules.append(_Rule(selector, declarations, _specificity(selector), order))
            order += 1
    if "{" in css and len(rules) == 0:
        diagnostics.append(
            Diagnostic(
                "warning", "css_malformed", "No usable CSS rules were found.", href
            )
        )
    return rules


def _stylesheet_texts(
    parser: Any, document: SourceDocument, diagnostics: list[Diagnostic]
) -> list[tuple[str, str]]:
    texts: list[tuple[str, str]] = []
    manifest: dict[str, Any] = {}
    for item in parser.book.get_items():
        name = item.get_name()
        media = str(getattr(item, "media_type", "") or "")
        if name.lower().endswith(".css") or media == "text/css":
            manifest[name] = item
    seen: set[str] = set()
    total_bytes = [0]

    def load(href: str, text: str, depth: int) -> None:
        if href in seen:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "css_import_cycle",
                    f"Skipped cyclic stylesheet import {href!r}.",
                    document.href,
                )
            )
            return
        if depth > 4:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "css_import_depth",
                    f"Skipped stylesheet import beyond the depth limit: {href!r}.",
                    document.href,
                )
            )
            return
        seen.add(href)
        total_bytes[0] += len(text.encode("utf-8", errors="replace"))
        if total_bytes[0] > 4 * 1024 * 1024:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "css_size_limit",
                    "Combined stylesheet size exceeded the limit.",
                    document.href,
                )
            )
            return
        for match in re.finditer(
            r"@import\s+(?:url\(\s*)?[\"']?([^\"'\s\)]+)",
            text,
            re.I,
        ):
            imported = match.group(1)
            parsed = urllib.parse.urlsplit(imported)
            if parsed.scheme or imported.startswith("//"):
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "css_remote_import",
                        f"Skipped remote stylesheet import {imported!r}.",
                        href,
                    )
                )
                continue
            imported_href = urllib.parse.urljoin(href, imported)
            item = manifest.get(imported_href)
            if item is None:
                item = next(
                    (
                        value
                        for name, value in manifest.items()
                        if name.endswith(imported_href)
                    ),
                    None,
                )
            if item is None:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "css_missing_stylesheet",
                        f"Stylesheet {imported_href!r} was not found.",
                        href,
                    )
                )
                continue
            try:
                raw = item.get_content()
                if len(raw) > 2 * 1024 * 1024:
                    diagnostics.append(
                        Diagnostic(
                            "warning",
                            "css_size_limit",
                            f"Stylesheet {imported_href!r} exceeded the size limit.",
                            href,
                        )
                    )
                    continue
                load(imported_href, raw.decode("utf-8", errors="replace"), depth + 1)
            except Exception as exc:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "css_stylesheet_error",
                        f"Could not read stylesheet {imported_href!r}: {exc}",
                        href,
                    )
                )
        texts.append((href, text))

    for match in re.finditer(
        r"<style\b[^>]*>(.*?)</style\s*>", document.text, re.I | re.S
    ):
        load(document.href, match.group(1), 0)
    linked: list[str] = []
    for match in re.finditer(r"<link\b([^>]*)>", document.text, re.I | re.S):
        attrs = dict(re.findall(r"([\w:-]+)\s*=\s*[\"']([^\"']*)[\"']", match.group(1)))
        if "stylesheet" in attrs.get("rel", "").lower().split():
            linked.append(urllib.parse.urljoin(document.href, attrs.get("href", "")))
    for href in linked:
        item = manifest.get(href)
        if item is None:
            item = next(
                (value for name, value in manifest.items() if name.endswith(href)), None
            )
        if item is None:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "css_missing_stylesheet",
                    f"Stylesheet {href!r} was not found.",
                    document.href,
                )
            )
            continue
        try:
            raw = item.get_content()
            if len(raw) > 2 * 1024 * 1024:
                diagnostics.append(
                    Diagnostic(
                        "warning",
                        "css_size_limit",
                        f"Stylesheet {href!r} exceeded the size limit.",
                        document.href,
                    )
                )
                continue
            load(href, raw.decode("utf-8", errors="replace"), 0)
        except Exception as exc:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "css_stylesheet_error",
                    f"Could not read stylesheet {href!r}: {exc}",
                    document.href,
                )
            )
    return texts


def _inline_declarations(attrs: dict[str, str]) -> tuple[tuple[str, str, bool], ...]:
    return _declarations(attrs.get("style", ""))


def _computed(
    rules: list[_Rule],
    tag: str,
    attrs: dict[str, str],
    ancestors: list[tuple[str, dict[str, str]]],
    inherited: tuple[bool, bool],
    semantic: tuple[bool, bool],
) -> tuple[bool, bool, bool, bool]:
    chosen: dict[str, tuple[str, bool, tuple[int, int, int], int]] = {}
    for rule in rules:
        if _matches(rule.selector, tag, attrs, ancestors):
            for name, value, important in rule.declarations:
                key = (1 if important else 0, rule.specificity, rule.order)
                old = chosen.get(name)
                if old is None:
                    chosen[name] = (value, important, rule.specificity, rule.order)
                elif key > (1 if old[1] else 0, old[2], old[3]):
                    chosen[name] = (value, important, rule.specificity, rule.order)
    for name, value, important in _inline_declarations(attrs):
        key = (1 if important else 0, (10**3, 0, 0), 10**6)
        old = chosen.get(name)
        if old is None or key >= (
            1 if old[1] else 0,
            old[2],
            old[3],
        ):
            chosen[name] = (value, important, key[1], key[2])
    italic = inherited[0] or semantic[0]
    bold = inherited[1] or semantic[1]
    cancel_italic = False
    cancel_bold = False
    if "font-style" in chosen:
        value = chosen["font-style"][0]
        if value in {"italic", "oblique"}:
            italic = True
        elif value == "normal":
            cancel_italic = inherited[0] or semantic[0]
            italic = False
    if "font-weight" in chosen:
        value = chosen["font-weight"][0]
        if value in {"bold", "bolder"} or value.isdigit() and int(value) >= 600:
            bold = True
        elif value == "normal":
            cancel_bold = inherited[1] or semantic[1]
            bold = False
    return italic, bold, cancel_italic, cancel_bold


def resolve_block_styles(
    parser: Any,
    document: SourceDocument,
    block: TextBlock,
) -> tuple[
    tuple[bool, bool],
    tuple[tuple[int, int, bool, bool, bool, bool], ...],
    list[Diagnostic],
]:
    diagnostics: list[Diagnostic] = []
    css: list[_Rule] = []
    for href, text in _stylesheet_texts(parser, document, diagnostics):
        css.extend(_parse_rules(text, diagnostics, href))
    block_attrs = {name.lower(): value for name, value in block.attrs}
    root = _computed(
        css, block.tag_name, block_attrs, [], (False, False), (False, False)
    )
    spans, _ = build_inline_spans(block)
    spans.sort(key=lambda span: (span.start, -(span.end or len(block.text))))
    computed: list[tuple[int, int, bool, bool, bool, bool]] = []
    stack: list[tuple[InlineSpan, tuple[bool, bool]]] = []
    for span in spans:
        if span.empty:
            continue
        while stack and span.start >= (stack[-1][0].end or len(block.text)):
            stack.pop()
        ancestors = [(item.tag, dict(item.attrs)) for item, _ in stack]
        inherited = stack[-1][1] if stack else root[:2]
        semantic = (span.tag in {"em", "i", "dfn", "cite"}, span.tag in {"strong", "b"})
        style = _computed(
            css, span.tag, dict(span.attrs), ancestors, inherited, semantic
        )
        end = span.end if span.end is not None else len(block.text)
        computed.append((span.start, end, *style))
        stack.append((span, style[:2]))
    return root[:2], tuple(computed), diagnostics
