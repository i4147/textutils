import base64
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable
from metext.utils import convert_to_bytes

CHARSETS_BASE64 = {
    "std": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
    "urlsafe": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
    "filenamesafe": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",
    "radix-64": "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+/",
}


class Base64Decoder(BaseDecoder):
    PLUGIN_NAME = "base64"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        charset = kwargs.get("charset", CHARSETS_BASE64["std"])
        if len(charset) != 64:
            raise AssertionError("Only full chars set or special chars set can be defined")

        if isinstance(_input, str):
            _input = convert_to_bytes(_input)
        if charset != CHARSETS_BASE64["std"]:
            tbl = bytes.maketrans(convert_to_bytes(charset), convert_to_bytes(CHARSETS_BASE64["std"]))
            _input = _input.translate(tbl)

        _input += b"=" * ((4 - len(_input) & 3) & 3)
        try:
            base64.b64decode(_input[:64], altchars=charset[-2:], validate=True)
        except:
            return None

        try:
            return base64.b64decode(
                b"".join(p.strip() for p in _input.splitlines()),
                altchars=charset[-2:],
                validate=True,
            )
        except:
            return None


class Base64UrlDecoder(BaseDecoder):
    PLUGIN_NAME = "base64url"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        return Base64Decoder.run(_input, charset=CHARSETS_BASE64["urlsafe"], **kwargs)
