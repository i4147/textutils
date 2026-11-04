import re
from typing import Callable
from collections.abc import Iterable
from pathlib import Path

MAX_CHUNK_CHAR_COUNT = 10_000

SCENE_HEADING_KEYWORDS = [
    "INT.",
    "INT ",
    "INT/",
    "EXT.",
    "EXT ",
    "EXT/",
    "I/E",
    "I./E.",
    "E/I",
    "E./I.",
    "EST.",
    "EST ",
    "EST/",
    "ESTABLISHING",
    "INTERIOR",
    "EXTERIOR",
]

SCENE_TRANSITION_KEYWORDS = [
    "CUT TO",
    "FADE TO",
    "FADE IN",
    "FADE OUT",
    "SMASH TO",
    "SMASH CUT TO",
    "WHIP PAN TO",
    "DISSOLVE TO",
]

RE_FOUNTAIN_SCENE_HEADING = re.compile(r"^\.[a-zA-Z0-9]")

RE_PAGE_NUMBER = re.compile(r"^\s*(\d{1,4})\.?\s*$")

RE_ROMAN_NUMERAL_PAGE_NUMBER = re.compile(r"^\s*[ivxlc]{1,10}\.?\s*$")


class Strutil:
    def __init__(self, log: Callable = print):
        self.log = log

    def chunk_pages(
        self,
        pages: list[str],
        max_chunk_chars: int = MAX_CHUNK_CHAR_COUNT,
        join_str: str = "\n\n",
    ) -> list[str]:
        return self.chunk_strs_by_char_count(
            strs=pages,
            max_char_count=max_chunk_chars,
            join_str=join_str,
        )

    def chunk_screenplay_text(
        self,
        text: str,
        max_chunk_chars: int = MAX_CHUNK_CHAR_COUNT,
        join_str="\n\n",
    ) -> list[str]:

        chunks = self.split_by_scene_heading(text)

        chunks = [
            s
            for s in self.flatten([
                c if len(c) <= max_chunk_chars else self.split_by_scene_transition(c) for c in chunks
            ])
        ]

        chunks = [
            s for s in self.flatten([c if len(c) <= max_chunk_chars else self.split_by_page_number(c) for c in chunks])
        ]

        return self.chunk_strs_by_char_count(
            strs=chunks,
            max_char_count=max_chunk_chars,
            join_str=join_str,
        )

    def chunk_generic_text(
        self,
        text: str,
        max_chunk_chars: int = MAX_CHUNK_CHAR_COUNT,
        join_str="\n\n",
    ) -> list[str]:
        chunks = self.split_by_page_number(text)

        chunks = [
            s
            for s in self.flatten([c if len(c) <= max_chunk_chars else self.split_by_emptyish_lines(c) for c in chunks])
        ]

        return self.chunk_strs_by_char_count(
            strs=chunks,
            max_char_count=max_chunk_chars,
            join_str=join_str,
        )

    def chunk_strs_by_char_count(
        self,
        strs: list[str],
        max_char_count: int = MAX_CHUNK_CHAR_COUNT,
        join_str: str = "\n\n",
    ) -> list[str]:
        res, buff, buff_chars = [], [], 0

        for s in strs:
            s_len = len(s)

            if s_len > max_char_count:
                if buff:
                    res.append(join_str.join(buff))
                    buff, buff_chars = [], 0
                self.log(f"single string length ({s_len}) exceeds max_char_count ({max_char_count})")
                res.append(s)
                continue

            if buff_chars + (len(join_str) if buff else 0) + s_len > max_char_count:
                res.append(join_str.join(buff))
                buff, buff_chars = [], 0

            buff.append(s)
            buff_chars += s_len + (len(join_str) if buff_chars > 0 else 0)

        if buff:
            res.append(join_str.join(buff))

        return res

    def split_by_line_type(self, text: str, line_matcher: Callable) -> list[str]:
        buff = []
        lines = text.split("\n")
        start, end = 0, 1
        while end <= len(lines):
            if end == len(lines):
                buff.append("\n".join(lines[start : len(lines)]))
            elif line_matcher(lines[end]):
                buff.append("\n".join(lines[start:end]))
                start = end
            end += 1
        return buff

    def split_by_scene_heading(self, text: str) -> list[str]:
        return self.split_by_line_type(
            text=text,
            line_matcher=self.line_is_scene_heading,
        )

    def split_by_scene_transition(self, text: str) -> list[str]:
        return self.split_by_line_type(
            text=text,
            line_matcher=self.line_is_transition,
        )

    def split_by_page_number(self, text: str) -> list[str]:
        return self.split_by_line_type(
            text=text,
            line_matcher=self.line_is_page_number,
        )

    def split_by_emptyish_lines(self, text: str) -> list[str]:
        return self.split_by_line_type(
            text=text,
            line_matcher=self.line_is_emptyish,
        )

    def line_is_scene_heading(self, line: str) -> bool:
        l = line.lstrip().upper()
        for k in SCENE_HEADING_KEYWORDS:
            if l.startswith(k):
                return True

        return bool(RE_FOUNTAIN_SCENE_HEADING.match(l))

    def line_is_transition(self, line: str) -> bool:
        l = line.strip().upper()
        for k in SCENE_TRANSITION_KEYWORDS:
            if l.startswith(k):
                return True

        return line.rstrip().upper().endswith(" TO:")

    def line_is_page_number(self, line: str) -> bool:
        l = line.strip()
        return bool(RE_PAGE_NUMBER.match(l) or RE_ROMAN_NUMERAL_PAGE_NUMBER.match(l))

    def line_is_emptyish(self, line: str) -> bool:
        l = line.strip()
        return l == "" or (len(l) == 1 and not l.isalnum())

    def subarrayify(self, arr: list, subarray_length: int) -> list[str]:
        if subarray_length < 2:
            raise ValueError("Subarray length must be at least 2")
        return [arr[i : i + subarray_length] for i in range(0, len(arr), subarray_length)]

    def remove_consecutive_blank_lines(self, text: str) -> str:
        lines = text.split("\n")
        res = []
        i = 0
        while i < len(lines):
            l = lines[i]
            if not l.strip() == "":
                res.append(l)
                i += 1
            else:
                if i < len(lines) - 1 and not lines[i + 1].strip() == "":
                    res.append(l)
                    res.append(lines[i + 1])
                    i += 2
                else:
                    i += 1
        return "\n".join(res)

    def flatten(self, lst):
        for item in lst:
            if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
                yield from self.flatten(item)
            else:
                yield item

    @staticmethod
    def write_file(path: Path, text: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
