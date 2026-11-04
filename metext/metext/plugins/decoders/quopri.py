import quopri
import re
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable
from metext.utils import convert_to_bytes


class QuoPriDecoder(BaseDecoder):
    PLUGIN_NAME = "quopri"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        try:
            _input = convert_to_bytes(_input)
        except:
            return None

        if re.search(rb"[^ -~\s]", _input) or re.search(rb"=(?:[0-9a-f]{2}|[0-9A-F]{2})", _input) is None:
            return None

        try:
            return quopri.decodestring(_input)
        except Exception:
            return None
