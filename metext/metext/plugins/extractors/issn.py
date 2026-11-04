from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.plugins.validators.issn import IssnValidator
from metext.utils.regex import RE_ISSN


class IssnExtractor(BaseExtractor):
    PLUGIN_NAME = "issn"

    valid_issns = set()

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_ISSN,
            validator=IssnValidator.run,
            cached_values=IssnExtractor.valid_issns,
            data_kind=IssnExtractor.PLUGIN_NAME,
        )
