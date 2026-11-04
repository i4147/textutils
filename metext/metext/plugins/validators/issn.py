import re
import xml.etree.ElementTree as ET

import requests

from metext.plugin_base import BaseValidator


def check_issn_via_oclc(isbn):
    resp = requests.get(r"http://classify.oclc.org/classify2/Classify?issn={}&summary=true".format(isbn))
    if resp.status_code != 200:
        return False
    x = ET.fromstring(resp.content)
    works = x.find("{http://classify.oclc.org}works")
    return len(works) > 0


def is_issn(issn: str) -> bool:
    if not isinstance(issn, str):
        try:
            issn = str(issn)
        except:
            return False

    issn = re.sub(r"[^0-9xX]", "", issn)

    if len(issn) != 8:
        return False

    sum_ = sum((index + 1) * int(value) if value.isdigit() else 10 for index, value in enumerate(issn[::-1]))
    return sum_ % 11 == 0


class IssnValidator(BaseValidator):
    PLUGIN_NAME = "issn"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        issn = _input.split(":")[-1]
        return is_issn(issn) and check_issn_via_oclc(issn)
