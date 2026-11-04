import re

from metext.plugin_base import BaseValidator
from metext.plugins.decoders.base32 import Base32Decoder
from metext.plugins.decoders.base64 import Base64Decoder, Base64UrlDecoder
from metext.plugins.decoders.base85 import Ascii85Decoder, Base85Decoder


class Ascii85Validator(BaseValidator):
    PLUGIN_NAME = "ascii85"

    @classmethod
    def run(cls, _input, **kwargs):
        return Ascii85Decoder.run(_input, **kwargs) is not None


class Base32Validator(BaseValidator):
    PLUGIN_NAME = "base32"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        return Base32Decoder.run(_input, **kwargs) is not None


class Base64Validator(BaseValidator):
    PLUGIN_NAME = "base64"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        if not _input:
            return False

        strict = kwargs.get("strict", False)

        if strict:
            if _input[0] in ["/", "+", "0"]:
                return False
            if len(_input) >= 32 and not re.search(r"(?=.*[a-f])(?=.*[A-F])(?=.*[+/\d]).+", _input[:32]):
                return False
            alts = "|".join(
                4 * i
                for i in [
                    "0",
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "a",
                    "b",
                    "c",
                    "d",
                    "e",
                    "f",
                    "A",
                    "B",
                    "C",
                    "D",
                    "E",
                    "F",
                ]
            )
            if re.match(r"(?:[A-Za-z0-9+/]{{4}})*(?:{0})".format(alts), _input):
                return False

        return Base64Decoder.run(_input, **kwargs) is not None


class Base64UrlValidator(BaseValidator):
    PLUGIN_NAME = "base64url"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        return Base64UrlDecoder.run(_input, **kwargs) is not None


class Base85Validator(BaseValidator):
    PLUGIN_NAME = "base85"

    @classmethod
    def run(cls, _input, **kwargs):
        return Base85Decoder.run(_input, **kwargs) is not None
