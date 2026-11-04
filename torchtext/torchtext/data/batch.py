import torch


class Batch(object):
    def __init__(self, data=None, dataset=None, device=None):
        if data is not None:
            self.batch_size = len(data)
            self.dataset = dataset
            self.fields = dataset.fields.keys()
            self.input_fields = [k for k, v in dataset.fields.items() if v is not None and not v.is_target]
            self.target_fields = [k for k, v in dataset.fields.items() if v is not None and v.is_target]

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
            return "Empty {} instance".format(torch.typename(self))

        fields_to_index = filter(lambda field: field is not None, self.fields)
        var_strs = "\n".join([
            "\t[." + name + "]" + ":" + _short_str(getattr(self, name))
            for name in fields_to_index
            if hasattr(self, name)
        ])

        data_str = (
            " from {}".format(self.dataset.name.upper())
            if hasattr(self.dataset, "name") and isinstance(self.dataset.name, str)
            else ""
        )

        strt = "[{} of size {}{}]\n{}".format(torch.typename(self), self.batch_size, data_str, var_strs)
        return "\n" + strt

    def __len__(self):
        return self.batch_size

    def _get_field_values(self, fields):
        if len(fields) == 0:
            return None
        elif len(fields) == 1:
            return getattr(self, fields[0])
        else:
            return tuple(getattr(self, f) for f in fields)

    def __iter__(self):
        yield self._get_field_values(self.input_fields)
        yield self._get_field_values(self.target_fields)


def _short_str(tensor):
    if not torch.is_tensor(tensor):
        if hasattr(tensor, "data"):
            tensor = getattr(tensor, "data")
        elif isinstance(tensor, tuple):
            return str(tuple(_short_str(t) for t in tensor))
        else:
            return str(tensor)

    size_str = "x".join(str(size) for size in tensor.size())
    device_str = "" if not tensor.is_cuda else " (GPU {})".format(tensor.get_device())
    strt = "[{} of size {}{}]".format(torch.typename(tensor), size_str, device_str)
    return strt
