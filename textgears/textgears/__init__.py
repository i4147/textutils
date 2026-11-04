# coding: utf-8

import requests

__author__ = "Hayato Tominaga"
__author_email__ = "takemehighermore@gmaill.com"
__license__ = "MIT License"
__version__ = "1.0.0"


class CheckResult(object):
    def __init__(self, data):

        self.raw = data
        self.index = data.get("index", 0)
        self.result = data.get("result")

    @property
    def errors(self):

        errors_raw = self.raw.get("errors")
        error_map_tuple = map((lambda e: (e.get("bad"), e.get("better"))), errors_raw)

        return dict(error_map_tuple)

    def __eq__(self, other):

        return len(self.errors) == len(other.errors)

    def __ne__(self, other):

        return not self.__eq__(other)

    def __iter__(self):

        return self

    def next(self):

        if self.index >= len(self.errors):
            self.index = 0
            raise StopIteration

        key = self.errors.keys()[self.index]
        self.index += 1
        return {key: self.errors[key]}

    def __repr__(self):

        return repr(self.errors)


class TextGears:
    def __init__(self, apikey):

        self.key = apikey
        self.url = "https://api.textgears.com/check.php"

    def check(self, text):
        response = self.access(text)
        data = response.json()

        return CheckResult(data)

    def access(self, text):

        params = {"text": text, "key": self.key}
        return requests.post(self.url, params=params)


def check(text, apikey):

    client = TextGears(apikey=apikey)
    return client.check(text)
