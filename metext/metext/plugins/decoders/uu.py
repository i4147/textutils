from codecs import decode
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable


class UUDecoder(BaseDecoder):
    PLUGIN_NAME = "uu"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        try:
            return decode(_input, encoding="uu")
        except Exception:
            return None
