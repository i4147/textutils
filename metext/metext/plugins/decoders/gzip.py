import gzip
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable


class GzipDecoder(BaseDecoder):
    PLUGIN_NAME = "gzip"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        if isinstance(_input, str):
            _input = bytes(_input, "utf8")

        try:
            return gzip.decompress(_input)
        except Exception:
            return None
