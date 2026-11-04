import re

_BRACKETED_NUMBERS_PATTERN = re.compile(r"\[\s*\d+\s*\]")
_BRACKETED_PAGE_NUMBERS_PATTERN = re.compile(r"^\s*\[\s*\d+\s*\]\s*$", re.MULTILINE)
_STANDALONE_PAGE_NUMBERS_PATTERN = re.compile(r"^\s*\d+\s*$", re.MULTILINE)
_PAGE_NUMBERS_AT_END_PATTERN = re.compile(r"\s+\d+\s*$", re.MULTILINE)
_PAGE_NUMBERS_WITH_DASH_PATTERN = re.compile(
    r"\s+[-–—]\s*\d+\s*[-–—]?\s*$", re.MULTILINE
)
_WHITESPACE_PATTERN = re.compile(r"[^\S\n]+")
_MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{3,}")
_SINGLE_NEWLINE_PATTERN = re.compile(r"(?<!\n)\n(?!\n)")
_CHAPTER_MARKER_PATTERN = re.compile(r"<<CHAPTER_MARKER:[^>]*>>")
_METADATA_TAG_PATTERN = re.compile(r"<<METADATA_[^:]+:[^>]*>>")
_PAGE_CHAPTER_MARKER_PATTERN = re.compile(r"<<(?:CHAPTER|PAGE):[^>]*>>")


ABBREVIATIONS = {
    "Mr",
    "Mrs",
    "Ms",
    "Dr",
    "Prof",
    "Sr",
    "Jr",
    "vs",
    "etc",
    "i.e",
    "e.g",
    "Ph.D",
    "M.D",
    "B.A",
    "M.A",
    "D.C.L",
    "L.L.D",
    "F.R.S",
    "St",
    "Rev",
    "Hon",
    "Messrs",
    "Mmes",
    "Msgr",
    "U.S",
    "U.K",
    "A.M",
    "P.M",
    "a.m",
    "p.m",
}


class TextCleaner:
    def __init__(
        self,
        remove_page_numbers: bool = True,
        remove_footnotes: bool = True,
        replace_single_newlines: bool = True,
        normalize_whitespace: bool = True,
        preserve_single_newlines: bool = False,
    ):
        self.remove_page_numbers = remove_page_numbers
        self.remove_footnotes = remove_footnotes
        self.replace_single_newlines = replace_single_newlines
        self.normalize_whitespace = normalize_whitespace
        self.preserve_single_newlines = preserve_single_newlines

    def clean(self, text: str) -> str:
        markers = {}
        marker_count = [0]

        def save_marker(match: re.Match[str]) -> str:
            placeholder = f"___MARKER_{marker_count[0]}___"
            markers[placeholder] = match.group(0)
            marker_count[0] += 1
            return placeholder

        text = _PAGE_CHAPTER_MARKER_PATTERN.sub(save_marker, text)

        text = _METADATA_TAG_PATTERN.sub("", text)

        if self.remove_page_numbers:
            text = _BRACKETED_PAGE_NUMBERS_PATTERN.sub("", text)
            text = _STANDALONE_PAGE_NUMBERS_PATTERN.sub("", text)
            text = _PAGE_NUMBERS_AT_END_PATTERN.sub("", text)
            text = _PAGE_NUMBERS_WITH_DASH_PATTERN.sub("", text)

        if self.remove_footnotes:
            text = _BRACKETED_NUMBERS_PATTERN.sub("", text)

        if self.normalize_whitespace:
            lines = [
                _WHITESPACE_PATTERN.sub(" ", line).strip() for line in text.splitlines()
            ]
            text = "\n".join(lines)

            if not self.preserve_single_newlines:
                text = _MULTIPLE_NEWLINES_PATTERN.sub("\n\n", text).strip()
            else:
                text = _MULTIPLE_NEWLINES_PATTERN.sub("\n", text).strip()

        if self.replace_single_newlines and not self.preserve_single_newlines:
            text = _SINGLE_NEWLINE_PATTERN.sub(" ", text)

        for placeholder, marker in markers.items():
            text = text.replace(placeholder, marker)

        return text

    def apply_gutenberg_spacing(self, text: str) -> str:
        try:
            from phrasplit import split_sentences
        except ImportError:
            return self._apply_gutenberg_spacing_simple(text)

        paragraphs = text.split("\n\n")
        result_paragraphs = []

        for para in paragraphs:
            if not para.strip():
                result_paragraphs.append(para)
                continue

            sentences = split_sentences(para)

            formatted = "  ".join(sentences)
            result_paragraphs.append(formatted)

        result = "\n\n".join(result_paragraphs)

        result = re.sub(r":\s+", r":  ", result)

        return result

    def _apply_gutenberg_spacing_simple(self, text: str) -> str:
        abbrev_map = {}
        abbrev_counter = [0]

        def protect_abbrev(match: re.Match[str]) -> str:
            placeholder = f"__ABBREV_{abbrev_counter[0]}__"
            abbrev_map[placeholder] = match.group(0)
            abbrev_counter[0] += 1
            return placeholder

        for abbr in ABBREVIATIONS:
            text = re.sub(
                rf"\b{re.escape(abbr)}\.\s", protect_abbrev, text, flags=re.IGNORECASE
            )

        text = re.sub(r":\s+", r":  ", text)

        text = re.sub(r'\.\s+([A-Z"\'])', r".  \1", text)
        text = re.sub(r'([!?])\s+([A-Z"\'])', r"\1  \2", text)

        for placeholder, original in abbrev_map.items():
            text = text.replace(placeholder, original)

        text = re.sub(r" {3,}", "  ", text)

        return text

    def calculate_length(self, text: str) -> int:
        text = _CHAPTER_MARKER_PATTERN.sub("", text)
        text = _METADATA_TAG_PATTERN.sub("", text)
        text = text.replace("\n", "").strip()
        return len(text)


def clean_text(
    text: str,
    remove_page_numbers: bool = True,
    remove_footnotes: bool = True,
    replace_single_newlines: bool = True,
    normalize_whitespace: bool = True,
    preserve_single_newlines: bool = False,
) -> str:
    cleaner = TextCleaner(
        remove_page_numbers=remove_page_numbers,
        remove_footnotes=remove_footnotes,
        replace_single_newlines=replace_single_newlines,
        normalize_whitespace=normalize_whitespace,
        preserve_single_newlines=preserve_single_newlines,
    )
    return cleaner.clean(text)


def calculate_text_length(text: str) -> int:
    cleaner = TextCleaner()
    return cleaner.calculate_length(text)
