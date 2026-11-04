# coding=utf-8

from msrest.serialization import Model


class DataInputDataItem(Model):
    _validation = {
        "id": {"required": True},
        "text": {"required": True},
    }

    _attribute_map = {
        "id": {"key": "id", "type": "str"},
        "text": {"key": "text", "type": "str"},
    }

    def __init__(self, **kwargs):
        super(DataInputDataItem, self).__init__(**kwargs)
        self.id = kwargs.get("id", None)
        self.text = kwargs.get("text", None)
