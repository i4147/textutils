# -*- coding: utf-8 -*-
import re

import lxml
import lxml.etree
from lxml.html.clean import Cleaner


NEWLINE_TAGS = frozenset([
    "article",
    "aside",
    "br",
    "dd",
    "details",
    "div",
    "dt",
    "fieldset",
    "figcaption",
    "footer",
    "form",
    "header",
    "hr",
    "legend",
    "li",
    "main",
    "nav",
    "table",
    "tr",
])
DOUBLE_NEWLINE_TAGS = frozenset([
    "blockquote",
    "dl",
    "figure",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "ol",
    "p",
    "pre",
    "title",
    "ul",
])

cleaner = Cleaner(
    scripts=True,
    javascript=False,
    comments=True,
    style=True,
    links=True,
    meta=True,
    page_structure=False,
    processing_instructions=True,
    embedded=True,
    frames=True,
    forms=False,
    annoying_tags=False,
    remove_unknown_tags=False,
    safe_attrs_only=False,
)


def _cleaned_html_tree(html):
    if isinstance(html, lxml.html.HtmlElement):
        tree = html
    else:
        tree = parse_html(html)

    try:
        cleaned = cleaner.clean_html(tree)
    except AssertionError:
        cleaned = tree

    return cleaned


def parse_html(html):
    body = html.strip().replace("\x00", "").encode("utf8") or b"<html/>"
    parser = lxml.html.HTMLParser(recover=True, encoding="utf8")
    root = lxml.etree.fromstring(body, parser=parser)
    if root is None:
        root = lxml.etree.fromstring(b"<html/>", parser=parser)
    return root


_whitespace = re.compile(r"\s+")
_has_trailing_whitespace = re.compile(r"\s$").search
_has_punct_after = re.compile(r'^[,:;.!?")]').search
_has_open_bracket_before = re.compile(r"\($").search


def _normalize_whitespace(text):
    return _whitespace.sub(" ", text.strip())


def etree_to_text(
    tree, guess_punct_space=True, guess_layout=True, newline_tags=NEWLINE_TAGS, double_newline_tags=DOUBLE_NEWLINE_TAGS
):
    chunks = []

    _NEWLINE = object()
    _DOUBLE_NEWLINE = object()
    prev = _DOUBLE_NEWLINE

    def should_add_space(text):
        if prev in {_NEWLINE, _DOUBLE_NEWLINE}:
            return False
        if not guess_punct_space:
            return True
        if not _has_trailing_whitespace(prev):
            if _has_punct_after(text) or _has_open_bracket_before(prev):
                return False
        return True

    def get_space_between(text):
        if not text:
            return " "
        return " " if should_add_space(text) else ""

    def add_newlines(tag):
        nonlocal prev
        if not guess_layout:
            return
        if prev is _DOUBLE_NEWLINE:
            return
        if tag in double_newline_tags:
            chunks.append("\n" if prev is _NEWLINE else "\n\n")
            prev = _DOUBLE_NEWLINE
        elif tag in newline_tags:
            if prev is not _NEWLINE:
                chunks.append("\n")
            prev = _NEWLINE

    def add_text(text_content):
        nonlocal prev
        text = _normalize_whitespace(text_content) if text_content else ""
        if not text:
            return
        space = get_space_between(text)
        chunks.extend([space, text])
        prev = text_content

    for event, el in lxml.etree.iterwalk(tree, events=("start", "end")):
        if event == "start":
            add_newlines(el.tag)
            add_text(el.text)
        elif event == "end":
            add_newlines(el.tag)
            if el is not tree:
                add_text(el.tail)

    return "".join(chunks).strip()


def selector_to_text(sel, guess_punct_space=True, guess_layout=True):
    import parsel

    if isinstance(sel, parsel.SelectorList):
        text = []
        for s in sel:
            extracted = etree_to_text(s.root, guess_punct_space=guess_punct_space, guess_layout=guess_layout)
            if extracted:
                text.append(extracted)
        return " ".join(text)
    else:
        return etree_to_text(sel.root, guess_punct_space=guess_punct_space, guess_layout=guess_layout)


def cleaned_selector(html):
    import parsel

    try:
        tree = _cleaned_html_tree(html)
        sel = parsel.Selector(root=tree, type="html")
    except (lxml.etree.XMLSyntaxError, lxml.etree.ParseError, lxml.etree.ParserError, UnicodeEncodeError):
        sel = parsel.Selector(html)
    return sel


def extract_text(
    html, guess_punct_space=True, guess_layout=True, newline_tags=NEWLINE_TAGS, double_newline_tags=DOUBLE_NEWLINE_TAGS
):
    if html is None:
        return ""
    no_content_nodes = (lxml.html.HtmlComment, lxml.html.HtmlProcessingInstruction)
    if isinstance(html, no_content_nodes):
        return ""
    cleaned = _cleaned_html_tree(html)
    return etree_to_text(
        cleaned,
        guess_punct_space=guess_punct_space,
        guess_layout=guess_layout,
        newline_tags=newline_tags,
        double_newline_tags=double_newline_tags,
    )
