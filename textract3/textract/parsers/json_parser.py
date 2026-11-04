import json
import six

from .utils import BaseParser


class Parser(BaseParser):
    def extract(self, filename, **kwargs):
        with open(filename, "r") as raw:
            deserialized_json = json.load(raw)
        return self.get_text(deserialized_json)

    def get_text(self, deserialized_json):
        if isinstance(deserialized_json, dict):
            result = ""
            for key in sorted(deserialized_json):
                result += self.get_text(deserialized_json[key]) + " "
            return result

        if isinstance(deserialized_json, list):
            result = ""
            for item in deserialized_json:
                result += self.get_text(item) + " "
            return result

        if isinstance(deserialized_json, six.string_types):
            return deserialized_json
        else:
            return ""
