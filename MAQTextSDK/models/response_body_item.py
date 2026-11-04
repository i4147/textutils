# coding=utf-8

from msrest.serialization import Model


class ResponseBodyItem(Model):
    _validation = {
        "id": {"required": True},
        "sentiment": {"required": True},
    }

    _attribute_map = {
        "id": {"key": "id", "type": "str"},
        "sentiment": {"key": "sentiment", "type": "float"},
    }

    def __init__(self, **kwargs):
        super(ResponseBodyItem, self).__init__(**kwargs)
        self.id = kwargs.get("id", None)
        self.sentiment = kwargs.get("sentiment", None)
