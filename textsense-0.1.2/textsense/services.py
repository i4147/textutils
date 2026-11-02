import requests
import json


class InvalidApiKeyError(Exception):
    def __init__(self, value=""):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SERVICE:
    def __init__(self, key=""):
        self._headers = {}
        self._headers["requestURL"] = "https://192.168.1.40:8011/"
        self._headers["content_type"] = "application/json"
        self._headers["X-Api-Key"] = key

    @property
    def api_key(self):
        return self._headers["X-Api-Key"]

    @api_key.setter
    def api_key(self, key):
        self._headers["X-Api-Key"] = key

    def set_api_key(self, key):
        self.api_key = key

    def __str__(self):
        return "TextSense Platform with Api service authenticated key {}".format(str(self._headers["X-Api-Key"]))

    def __repr__(self):
        return "Service Api Key ({})".format(str(self._headers["X-Api-Key"]))

    def sentiment(self, text):
        url = self._headers["requestURL"] + "sentiment"
        data = {"text": text}
        try:
            response = requests.post(url=url, headers=self._headers, json=data, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                raise InvalidApiKeyError()
        except InvalidApiKeyError:
            return json.dumps({"message": "Invalid Api-Key"})

    def similar_words(self, word):
        url = self._headers["requestURL"] + "similar_words"
        data = {"text": word, "collection": "BloombergandReuters"}
        try:
            response = requests.post(url=url, headers=self._headers, json=data, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                raise InvalidApiKeyError()
        except InvalidApiKeyError:
            return json.dumps({"message": "Invalid Api-Key"})

    def important_keywords(self, text):
        url = self._headers["requestURL"] + "important_keywords"
        data = {"text": text, "collection": "BloombergandReuters"}
        try:
            response = requests.post(url=url, headers=self._headers, json=data, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                raise InvalidApiKeyError()
        except InvalidApiKeyError:
            return json.dumps({"message": "Invalid Api-Key"})

    def extractive_summary(self, text):
        url = self._headers["requestURL"] + "extractive_summary"
        data = {"text": text}
        try:
            response = requests.post(url=url, headers=self._headers, json=data, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                raise InvalidApiKeyError()
        except InvalidApiKeyError:
            return json.dumps({"message": "Invalid Api-Key"})

    def news_classification(self, news):
        url = self._headers["requestURL"] + "news_classification"
        data = {"news": news}
        try:
            response = requests.post(url=url, headers=self._headers, json=data, verify=False)
            if response.status_code == 200:
                return response.json()
            else:
                raise InvalidApiKeyError()
        except InvalidApiKeyError:
            return json.dumps({"message": "Invalid Api-Key"})
