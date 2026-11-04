import json
from typing import Iterable

from netaddr import EUI

from metext.plugin_base import BaseExtractor
from metext.plugins.extractors import _extract_with_regex
from metext.utils.regex import RE_MAC


class MACAddressExtractor(BaseExtractor):
    PLUGIN_NAME = "mac"

    @classmethod
    def run(cls, _input: str, **kwargs) -> Iterable[dict]:
        for mac in _extract_with_regex(_input, RE_MAC, data_kind=MACAddressExtractor.PLUGIN_NAME):
            try:
                info = EUI(mac["value"]).info
                if info:
                    mac.update({"info": (json.loads(str(info).replace("'", '"')))})
            except:
                pass
            yield mac
