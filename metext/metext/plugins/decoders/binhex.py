import binhex
import os
import tempfile
from io import BytesIO
from typing import Optional

from metext.plugin_base import BaseDecoder, Decodable


class BinhexDecoder(BaseDecoder):
    PLUGIN_NAME = "binhex"

    @classmethod
    def run(cls, _input: Decodable, **kwargs) -> Optional[bytes]:
        if isinstance(_input, str):
            _input = bytes(_input, "utf8")

        p = os.path.join(tempfile.gettempdir(), tempfile.gettempprefix() + "bhx123")
        try:
            binhex.hexbin(BytesIO(_input), p)
            with open(p, "rb") as tf:
                return tf.read()
        except:
            return None
        finally:
            try:
                os.remove(p)
            except:
                pass
