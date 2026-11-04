from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.plugins.validators.isbn import IsbnValidator
from metext.utils.regex import RE_ISBN, RE_ISBN10, RE_ISBN13


class IsbnExtractor(BaseExtractor):
    PLUGIN_NAME = "isbn"

    valid_isbns = set()

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ISBN,
            validator=IsbnValidator.run,
            cached_values=IsbnExtractor.valid_isbns,
            data_kind=IsbnExtractor.PLUGIN_NAME,
        )


class Isbn10Extractor(BaseExtractor):
    PLUGIN_NAME = "isbn10"
    PLUGIN_ACTIVE = False

    valid_isbns = set()

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ISBN10,
            validator=IsbnValidator.run,
            cached_values=Isbn10Extractor.valid_isbns,
            data_kind=Isbn10Extractor.PLUGIN_NAME,
        )


class Isbn13Extractor(BaseExtractor):
    PLUGIN_NAME = "isbn13"
    PLUGIN_ACTIVE = False

    valid_isbns = set()

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ISBN13,
            validator=IsbnValidator.run,
            cached_values=Isbn13Extractor.valid_isbns,
            data_kind=Isbn13Extractor.PLUGIN_NAME,
        )
