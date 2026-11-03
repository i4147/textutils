import re
from typing import List
from .types import Element

__all__ = ["parse_markdown_elements"]
_HDR = re.compile(r"^\s*#{1,6}\s+")
_LI = re.compile(r"^\s*([-*+]|[0-9]+[.)-])\s+")


def _is_heading(line: str) -> bool:
    return bool(_HDR.match(line))


def _heading_text(line: str) -> str:
    return _HDR.sub("", line).strip()


def _is_table_line(line: str) -> bool:
    line = line.rstrip()
    return line.startswith("|") and "|" in line


def _is_list_line(line: str) -> bool:
    return bool(_LI.match(line))


def parse_markdown_elements(md: str) -> list[Element]:
    lines = md.splitlines()
    n = len(lines)
    i = 0
    elements: list[Element] = []
    para: list[str] = []
    in_code = False
    code_buf: list[str] = []
    page = 1

    def flush_para():
        nonlocal para
        if para:
            txt = "\n".join(para).strip()
            if txt:
                elements.append(Element("Text", txt, page))
            para = []

    while i < n:
        line = lines[i]
        if line.strip().startswith("```"):
            if not in_code:
                flush_para()
                in_code = True
                code_buf = []
            else:
                txt = "\n".join(code_buf).rstrip()
                if txt:
                    elements.append(Element("Text", txt, page))
                in_code = False
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if _is_heading(line):
            flush_para()
            elements.append(Element("Title", _heading_text(line), page))
            i += 1
            continue
        if _is_table_line(line):
            flush_para()
            tbl = [line.rstrip()]
            j = i + 1
            while j < n and _is_table_line(lines[j]):
                tbl.append(lines[j].rstrip())
                j += 1
            elements.append(Element("Table", "\n".join(tbl).strip(), page))
            i = j
            continue
        if _is_list_line(line):
            flush_para()
            lst = []
            j = i
            while j < n and (
                _is_list_line(lines[j]) or (lines[j].strip() == "" and j + 1 < n and _is_list_line(lines[j + 1]))
            ):
                if _is_list_line(lines[j]):
                    item = _LI.sub("", lines[j]).strip()
                    if item:
                        lst.append(f"- {item}")
                j += 1
            if lst:
                elements.append(Element("Text", "\n".join(lst), page))
            i = j
            continue
        if not line.strip():
            flush_para()
            i += 1
            continue
        para.append(line.rstrip())
        i += 1
    flush_para()
    return elements
