from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable
from metext.utils.sabyenc import old_yenc


class YEncDecoder(BaseDecoder):
    PLUGIN_NAME = "yenc"
    PLUGIN_ACTIVE = True

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:

        if isinstance(_input, str):
            _input = _input.encode("utf8")

        if not _input:
            return None

        try:
            decoded, *_ = old_yenc(_input)
            return decoded
        except Exception as e:
            return None
