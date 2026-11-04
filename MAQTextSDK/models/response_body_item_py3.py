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

    def __init__(self, *, id: str, sentiment: float, **kwargs) -> None:
        super(ResponseBodyItem, self).__init__(**kwargs)
        self.id = id
        self.sentiment = sentiment
