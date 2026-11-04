import json
from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.utils.regex import RE_JSON


class JsonExtractor(BaseExtractor):
    PLUGIN_NAME = "json"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:

        def validate(data):
            try:
                d = json.loads(data)
            except:
                return False
            if len(d) == 0:
                return False
            if isinstance(d, list) and len(d) < 2:
                return False
            return True

        yield from _extract_with_regex(
            _input,
            RE_JSON,
            validator=validate,
            per_line=False,
            data_kind=JsonExtractor.PLUGIN_NAME,
        )
