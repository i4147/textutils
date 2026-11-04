from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.utils.regex import (
    RE_MD5,
    RE_SHA1,
    RE_SHA224,
    RE_SHA256,
    RE_SHA384,
    RE_SHA512,
)


class MD5Extractor(BaseExtractor):
    PLUGIN_NAME = "md5"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_MD5, per_line=True, data_kind=MD5Extractor.PLUGIN_NAME)


class SHA1Extractor(BaseExtractor):
    PLUGIN_NAME = "sha1"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_SHA1, per_line=True, data_kind=SHA1Extractor.PLUGIN_NAME)


class SHA224Extractor(BaseExtractor):
    PLUGIN_NAME = "sha224"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_SHA224, per_line=True, data_kind=SHA224Extractor.PLUGIN_NAME)


class SHA256Extractor(BaseExtractor):
    PLUGIN_NAME = "sha256"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_SHA256, per_line=True, data_kind=SHA256Extractor.PLUGIN_NAME)


class SHA384Extractor(BaseExtractor):
    PLUGIN_NAME = "sha384"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_SHA384, per_line=True, data_kind=SHA384Extractor.PLUGIN_NAME)


class SHA512Extractor(BaseExtractor):
    PLUGIN_NAME = "sha512"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(_input, RE_SHA512, per_line=True, data_kind=SHA512Extractor.PLUGIN_NAME)
