from typing import Iterable

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.plugins.validators.ip import IPv4AddressValidator, IPv6AddressValidator
from metext.utils.regex import RE_IPV4, RE_IPV6

SYMBOLS_HYPHEN_LIKE = [
    "-",
    "–",
    "—",
    "−",
]


class IPv4AddressExtractor(BaseExtractor):
    PLUGIN_NAME = "ipv4"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:

        def validate(value):
            first = value.split(".")
            return IPv4AddressValidator.run(value) and (first == "0" or len(first) > 1)

        yield from _extract_with_regex(
            _input,
            RE_IPV4,
            validator=validate,
            per_line=True,
            data_kind=IPv4AddressExtractor.PLUGIN_NAME,
        )


class IPv6AddressExtractor(BaseExtractor):
    PLUGIN_NAME = "ipv6"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        yield from _extract_with_regex(
            _input,
            RE_IPV6,
            validator=lambda val: len(val) > 6 and IPv6AddressValidator.run(val),
            per_line=True,
            data_kind=IPv6AddressExtractor.PLUGIN_NAME,
        )
