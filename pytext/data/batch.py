import numpy
from .utils import typename
# import torch


class Batch(object):
    def __init__(self, data=None, dataset=None, device=None):
        if data is not None:
            self.batch_size = len(data)
            self.dataset = dataset
            self.fields = dataset.fields.keys()

            for name, field in dataset.fields.items():
                if field is not None:
                    batch = [getattr(x, name) for x in data]
                    setattr(self, name, field.process(batch, device=device))

    @classmethod
    def fromvars(cls, dataset, batch_size, train=None, **kwargs):
        batch = cls()
        batch.batch_size = batch_size
        batch.dataset = dataset
        batch.fields = dataset.fields.keys()
        for k, v in kwargs.items():
            setattr(batch, k, v)
        return batch

    def __repr__(self):
        return str(self)

    def __str__(self):
        if not self.__dict__:
            return "Empty {} instance".format(typename(self))

        var_strs = "\n".join([
            "\t[." + name + "]" + ":" + _short_str(getattr(self, name)) for name in self.fields if hasattr(self, name)
        ])

        data_str = (
            " from {}".format(self.dataset.name.upper())
            if hasattr(self.dataset, "name") and isinstance(self.dataset.name, str)
            else ""
        )

        strt = "[{} of size {}{}]\n{}".format(typename(self), self.batch_size, data_str, var_strs)
        return "\n" + strt

    def __len__(self):
        return self.batch_size


def _short_str(tensor):
    if not isinstance(tensor, numpy.ndarray):
        if hasattr(tensor, "data"):
            tensor = getattr(tensor, "data")
        elif isinstance(tensor, tuple):
            return str(tuple(_short_str(t) for t in tensor))
        else:
            return str(tensor)

    size_str = "x".join(str(size) for size in tensor.shape)
    # device_str = '' if not tensor.is_cuda else \
    #' (GPU {})'.format(tensor.get_device())
    strt = "[{} of size {}{}]".format(typename(tensor), size_str, device_str)
    return strt
