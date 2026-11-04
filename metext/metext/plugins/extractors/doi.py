from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.plugins.validators.doi import DoiValidator
from metext.utils.regex import RE_DOI


class DoiExtractor(BaseExtractor):
    PLUGIN_NAME = "doi"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_DOI,
            validator=DoiValidator.run,
            per_line=True,
            data_kind=DoiExtractor.PLUGIN_NAME,
            postprocess=lambda x: x.split("(")[0] if "(" in x and ")" not in x else x,
        )
