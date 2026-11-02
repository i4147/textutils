import decimal
from mytextgrid.eval import obj_to_decimal

decimal.getcontext().prec = 16


class Tier:
    def __init__(self, name="", xmin=0, xmax=1, is_interval=True, textgrid=None):
        if not isinstance(name, str):
            msg = "name MUST BE a str."
            raise TypeError(msg)
        if not isinstance(xmin, (int, float, str, decimal.Decimal)):
            msg = "xmin MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(xmax, (int, float, str, decimal.Decimal)):
            msg = "xmax MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(is_interval, bool):
            msg = "is_interval MUST BE a boolean value."
            raise TypeError(msg)
        xmin_ = obj_to_decimal(xmin)
        xmax_ = obj_to_decimal(xmax)
        assert xmax_ > xmin_, "xmax MUST BE greater than xmin"
        self._name = name
        self._xmin = xmin_
        self._xmax = xmax_
        self._is_interval = is_interval
        self._textgrid = textgrid
        self._items = []

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)

    def __getitem__(self, key):
        return self._items[key]

    @property
    def name(self):
        return self._name

    @property
    def xmin(self):
        return self._xmin

    @property
    def xmax(self):
        return self._xmax

    @property
    def items(self):
        return self._items

    def duration(self):
        return self.xmax - self.xmin

    def is_interval(self):
        return self._is_interval

    def eval_time_range(self, time):
        time_ = obj_to_decimal(time)
        if self._xmin > time_ > self._xmax:
            msg = f"{time_} (s) is out of range of the tier {self._name}"
            raise ValueError(msg)
        if self._xmin == time_:
            msg = f"{time_} seconds is at the left edge of the tier {self._name}."
            raise ValueError(msg)
        if self._xmax == time_:
            msg = f"{time_} seconds is at the right edge of the tier {self._name}."
            raise ValueError(msg)

    def textgrid(self):
        return self._textgrid
