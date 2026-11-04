import six

import extract_msg

from .utils import BaseParser


def ensure_bytes(string):
    if isinstance(string, six.string_types):
        return string.encode("utf-8")
    return string


class Parser(BaseParser):
    def extract(self, filename, **kwargs):
        m = extract_msg.Message(filename)
        return ensure_bytes(m.subject) + six.b("\n\n") + ensure_bytes(m.body)
