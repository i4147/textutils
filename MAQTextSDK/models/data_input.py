# coding=utf-8

from msrest.serialization import Model


class DataInput(Model):
    _attribute_map = {
        "data": {"key": "data", "type": "[DataInputDataItem]"},
    }

    def __init__(self, **kwargs):
        super(DataInput, self).__init__(**kwargs)
        self.data = kwargs.get("data", None)
