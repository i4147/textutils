import re
import sys
from typing import Iterable, List
import unicodedata
from .mappings import PUA_BULLETS, TRANSLATE_MAP

RE_PUA = re.compile(r"[\uE000-\uF8FF]")
RE_CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
RE_TOC_LINE = re.compile(r"\.{3,}\s*\d+\s*$")
RE_LIST_HEAD = re.compile(r"^\s*(?:•|\*|·|∙|‧|■|▪|●|◦|—|-)\s*")


def _translate_basic(s: str) -> str:
    if any(ch in s for ch in PUA_BULLETS):
        for ch in PUA_BULLETS:
            s = s.replace(ch, "•")
    return s.translate(str.maketrans(TRANSLATE_MAP))


def clean_text(
    s: str,
    *,
    bullet: str = "-",
    drop_pua_rest: bool = True,
    normalize_form: str = "NFKC",
    collapse_ws: bool = True,
    strip_toc_lines: bool = True,
    preserve_markdown_tables: bool = True,
) -> str:
    if not s:
        return s
    s = _translate_basic(s)
    s = unicodedata.normalize(normalize_form, s)
    if drop_pua_rest:
        s = RE_PUA.sub("", s)
    out_lines: list[str] = []
    for ln in s.splitlines():
        if strip_toc_lines and RE_TOC_LINE.search(ln.strip()):
            continue
        ln = RE_LIST_HEAD.sub(f"{bullet} ", ln)
        out_lines.append(ln)
    s = "\n".join(out_lines)
    s = RE_CTRL.sub("", s)
    if collapse_ws:
        if preserve_markdown_tables:
            new_lines: list[str] = []
            for ln in s.splitlines():
                is_table = ln.lstrip().startswith("|") and ("|" in ln.lstrip()[1:])
                if is_table:
                    new_lines.append(ln.rstrip())
                else:
                    ln = re.sub(r"[ \t]+", " ", ln)
                    new_lines.append(ln.strip())
            s = "\n".join(new_lines)
        else:
            s = re.sub(r"[ \t]+", " ", s)
            s = re.sub(r" ?\n ?", "\n", s)
            s = s.strip()
    return s


def clean_lines(lines: Iterable[str], **kwargs) -> list[str]:
    return [clean_text(x, **kwargs) for x in lines]


def _get_text_field(obj, key: str = "text") -> str:
    if isinstance(obj, dict):
        return obj.get(key, "")
    return getattr(obj, key, "")


def _set_text_field(obj, value: str, key: str = "text") -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def clean_chunks(
    chunks,
    *,
    text_key: str = "text",
    bullet: str = "-",
    preserve_markdown_tables: bool = True,
    in_place: bool = True,
):
    if not in_place:
        cleaned = []
    for c in chunks:
        t = _get_text_field(c, text_key) or ""
        t2 = clean_text(t, bullet=bullet, preserve_markdown_tables=preserve_markdown_tables)
        if in_place:
            _set_text_field(c, t2, text_key)
        else:
            if isinstance(c, dict):
                nc = dict(c)
                nc[text_key] = t2
            else:
                from copy import copy

                nc = copy(c)
                setattr(nc, text_key, t2)
            cleaned.append(nc)
    return chunks if in_place else cleaned


def main(argv: list[str] | None = None) -> None:
    data = sys.stdin.read()
    sys.stdout.write(clean_text(data))
