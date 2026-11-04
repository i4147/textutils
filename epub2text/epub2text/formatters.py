import re

from phrasplit import (
    split_clauses,
    split_paragraphs,
    split_sentences,
)
from phrasplit import (
    split_long_lines as _phrasplit_split_long_lines,
)


def collapse_paragraph(paragraph: str) -> str:
    result = re.sub(r"\s*\n\s*", " ", paragraph)
    result = re.sub(r"  +", " ", result)
    return result.strip()


def format_paragraphs(
    text: str,
    separator: str = "  ",
    one_line_per_paragraph: bool = False,
) -> str:
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_parts = []
    for i, para in enumerate(paragraphs):
        if one_line_per_paragraph:
            para = collapse_paragraph(para)

        if i == 0:
            result_parts.append(para)
        else:
            is_likely_chapter_title = (
                len(para) < 100
                and not para.rstrip().endswith((".", "!", "?", '"', "'"))
                and "\n" not in para
            )

            if separator and not is_likely_chapter_title:
                lines = para.split("\n")
                lines[0] = separator + lines[0]
                para = "\n".join(lines)
            result_parts.append(para)

    return "\n".join(result_parts)


def format_sentences(
    text: str,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_lines: list[str] = []
    for i, para in enumerate(paragraphs):
        is_likely_chapter_title = (
            len(para) < 100
            and not para.rstrip().endswith((".", "!", "?", '"', "'"))
            and "\n" not in para
        )

        if is_likely_chapter_title:
            result_lines.append(para)
            continue

        sentences = split_sentences(para, language_model)

        if not sentences:
            continue

        for j, sent in enumerate(sentences):
            if i > 0 and j == 0 and separator:
                result_lines.append(separator + sent)
            else:
                result_lines.append(sent)

    return "\n".join(result_lines)


def format_clauses(
    text: str,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:

    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_lines: list[str] = []
    for i, para in enumerate(paragraphs):
        is_likely_chapter_title = (
            len(para) < 100
            and not para.rstrip().endswith((".", "!", "?", '"', "'"))
            and "\n" not in para
        )

        if is_likely_chapter_title:
            result_lines.append(para)
            continue

        clauses = split_clauses(para, language_model)

        if not clauses:
            continue

        is_first_clause_in_para = True
        for clause in clauses:
            if i > 0 and is_first_clause_in_para and separator:
                result_lines.append(separator + clause)
            else:
                result_lines.append(clause)
            is_first_clause_in_para = False

    return "\n".join(result_lines)


def split_long_lines(
    text: str,
    max_length: int,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:
    lines = text.split("\n")
    result_lines: list[str] = []

    for line in lines:
        is_likely_chapter_title = (
            len(line.strip()) < 100
            and line.strip()
            and not line.strip().endswith((".", "!", "?", '"', "'"))
        )

        if is_likely_chapter_title:
            result_lines.append(line)
            continue

        if len(line) <= max_length:
            result_lines.append(line)
            continue

        has_separator = line.startswith(separator) if separator else False
        content = line[len(separator) :] if has_separator else line

        split_lines_list = _phrasplit_split_long_lines(
            content, max_length, language_model
        )
        for k, split_line in enumerate(split_lines_list):
            if k == 0 and has_separator:
                result_lines.append(separator + split_line)
            else:
                result_lines.append(split_line)

    return "\n".join(result_lines)


__all__ = [
    "collapse_paragraph",
    "format_paragraphs",
    "format_sentences",
    "format_clauses",
    "split_long_lines",
    "split_paragraphs",
]
