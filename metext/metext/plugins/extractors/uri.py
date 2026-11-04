import re
from typing import Iterable
from urllib.parse import unquote_plus

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.plugins.validators.uri import (
    DataURIValidator,
    MagnetValidator,
    URIValidator,
    URLValidator,
)
from metext.utils.regex import RE_DATA_URI, RE_URL, RE_URL_FORM_FIELDS, RE_URN
from metext.utils.uri import URI, URI_SCHEMES


class URIExtractor(BaseExtractor):
    PLUGIN_NAME = "uri"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        strict = kwargs.get("strict", False)
        schemes = kwargs.get("schemes", URI_SCHEMES)
        re_uri = re.compile(
            r"\b(?=(?:{}):){}\b".format(
                "|".join(set(schemes + [s.upper() for s in schemes] + [s.lower() for s in schemes])),
                URI,
            ),
            re.VERBOSE,
        )
        yield from _extract_with_regex(
            _input,
            re_uri,
            preprocess=lambda x: "" if re.search(r"(?:[a-z]{2}|[A-Z]{2}):", x) is None else x,
            validator=lambda val: URIValidator.run(val, strict=strict, schemes=schemes),
            data_kind=URIExtractor.PLUGIN_NAME,
        )


class URLExtractor(BaseExtractor):
    PLUGIN_NAME = "url"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_URL,
            validator=URLValidator.run,
            data_kind=URLExtractor.PLUGIN_NAME,
        )


class URNExtractor(BaseExtractor):
    PLUGIN_NAME = "urn"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_URN,
            data_kind=URNExtractor.PLUGIN_NAME,
        )


class DataURIExtractor(BaseExtractor):
    PLUGIN_NAME = "data_uri"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_DATA_URI,
            validator=DataURIValidator.run,
            data_kind=DataURIExtractor.PLUGIN_NAME,
        )


class MagnetExtractor(BaseExtractor):
    PLUGIN_NAME = "magnet"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:

        yield from (
            magnet
            for magnet in URIExtractor.run(_input, schemes=["magnet"], strict=False)
            if MagnetValidator.run(magnet["value"])
        )


class FormFieldsExtractor(BaseExtractor):
    PLUGIN_NAME = "form_fields"
    PLUGIN_ACTIVE = False

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        min_len = kwargs.get("min_len", 20)
        decode = kwargs.get("decode", True)

        yield from _extract_with_regex(
            _input,
            RE_URL_FORM_FIELDS,
            validator=lambda val: len(val) >= min_len and not ("&" not in val and val.endswith("=")),
            postprocess=lambda val: unquote_plus(val) if decode else val,
            data_kind=FormFieldsExtractor.PLUGIN_NAME,
        )
