import base64
from typing import Optional

import pem

from metext.plugin_base import BaseDecoder, Decodable


class PemDecoder(BaseDecoder):
    PLUGIN_NAME = "pem"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        if isinstance(_input, str):
            _input = _input.encode("utf-8")

        if not _input.startswith(b"-----"):
            return None

        try:
            pems = pem.parse(_input)
        except:
            return None

        res = []
        for p in pems:
            try:
                res.append(base64.b64decode(b"".join(p.as_bytes().splitlines()[1:-1])))
            except:
                continue

        return b"\n\n".join(res)
