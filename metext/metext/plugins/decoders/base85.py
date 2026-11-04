import base64
import re
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable
from metext.utils import convert_to_bytes, z85


class Base85Decoder(BaseDecoder):
    PLUGIN_NAME = "base85"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        try:
            return base64.b85decode(_input)
        except Exception:
            return None


class Ascii85Decoder(BaseDecoder):
    PLUGIN_NAME = "ascii85"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        if not _input:
            return None

        _input = convert_to_bytes(_input).strip()

        try:
            if _input[:2] == b"<~" and _input[-2:] == b"~>":
                return base64.a85decode(_input, adobe=True)
            return base64.a85decode(_input, adobe=False, foldspaces=True)
        except:
            return None


class Z85Decoder(BaseDecoder):
    PLUGIN_NAME = "z85"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        try:
            _input = convert_to_bytes(_input).strip()
            if (
                re.search(
                    rb"[^0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.\-:+=^!/*?&<>()[]{}@%\$#]",
                    _input,
                )
                is not None
            ):
                return None
            return z85.decode(_input)
        except:
            return None
