import xml.etree.ElementTree as ET

import requests

from metext.plugin_base import BaseValidator


def check_isbn_via_oclc(isbn):
    resp = requests.get(r"http://classify.oclc.org/classify2/Classify?isbn={}&summary=true".format(isbn))
    if resp.status_code != 200:
        return False
    x = ET.fromstring(resp.content)
    return x.find("{http://classify.oclc.org}work") is not None


def is_isbn(isbn: str) -> bool:
    if not isinstance(isbn, str):
        try:
            isbn = str(isbn)
        except:
            return False

    isbn = "".join(filter(lambda x: x.isdigit() or x in ["x", "X"], isbn))

    if len(isbn) not in [10, 13]:
        return False

    if len(isbn) == 10:
        return check_isbn_10(isbn)
    return check_isbn_13(isbn)


def check_isbn_10(isbn: str) -> bool:
    sum_ = sum((index + 1) * (int(value) if value not in ["x", "X"] else 10) for index, value in enumerate(isbn[::-1]))
    return sum_ % 11 == 0


def check_isbn_13(isbn: str) -> bool:
    sum_ = sum(int(value) * 3 if (index + 1) % 2 == 0 else int(value) for index, value in enumerate(isbn[::-1]))
    return sum_ % 10 == 0


class IsbnValidator(BaseValidator):
    PLUGIN_NAME = "isbn"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        isbn = _input.split(":")[-1]
        return is_isbn(isbn) and check_isbn_via_oclc(isbn)
