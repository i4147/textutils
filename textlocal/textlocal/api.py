import json
import urllib.parse

import requests

from textlocal.messages import SMS


class Textlocal(object):
    DOMAIN = "https://api.txtlocal.com"

    def __init__(self, api_key=None, username=None, password=None, **kwargs):
        if api_key == username == password == None:
            raise Exception("Either api_key or username and password must be used.")
        elif (username is None and password is not None) or (password is None and username is not None):
            raise Exception("If using username and password both must be set.")
        self.api_key = api_key
        self.username = username
        self.password = password
        self.sender = kwargs.get("sender", None)
        self.simple_reply = kwargs.get("simple_reply", None)
        self.test = kwargs.get("test", False)

    def get_balance(self):
        PATHNAME = "balance"
        response = self._get(PATHNAME)
        balance = response.get("balance")
        return balance["sms"], balance["mms"]

    def get_templates(self):
        PATHNAME = "get_templates"
        response = self._get(PATHNAME)
        return response.get("templates")

    def check_keyword(self, keyword):
        PATHNAME = "check_keyword"
        response = self._get(PATHNAME, {"keyword": str(keyword)})
        return response.get("templates")

    def txt(self, numbers, message):
        sms = SMS(message, numbers)
        return self._send(sms)

    def _send(self, message):
        data = self._get_message_defaults()
        data.update(message.as_dict())
        return self._post("send", data)

    def _get(self, pathname, data=None):
        return self._call("get", pathname, data)

    def _post(self, pathname, data=None):
        return self._call("post", pathname, data)

    def _call(self, method, pathname, data=None):
        url = urllib.parse.urljoin(self.DOMAIN, pathname)
        if not data:
            data = dict()
        data.update(self._get_credentials())
        r = getattr(requests, method)(url, data)
        return r.json()

    def _get_credentials(self):
        if self.api_key:
            return {"apiKey": self.api_key}
        else:
            return {"username": self.username, "hash": self.password}

    def _get_message_defaults(self):
        defaults = {}
        if self.sender:
            defaults["sender"] = self.sender
        if self.simple_reply:
            defaults["simple_reply"] = self.simple_reply
        if self.test:
            defaults["test"] = self.test
        return defaults
