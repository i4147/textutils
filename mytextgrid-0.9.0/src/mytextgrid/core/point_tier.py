import decimal
from mytextgrid.core.tier import Tier
from mytextgrid.eval import obj_to_decimal

decimal.getcontext().prec = 16


class PointTier(Tier):
    def __init__(self, name="", xmin=0, xmax=1, textgrid=None):
        is_interval = False
        super().__init__(name, xmin, xmax, is_interval, textgrid)

    def insert_point(self, time, text=""):
        time_ = obj_to_decimal(time)
        self.eval_time_range(time_)
        index = self.get_index_at_time(time_)
        if index is not None:
            msg = f"Cannot insert a Point at {time}."
            raise ValueError(msg)
        point = Point(time_, text, self)
        self._items.append(point)
        self._items.sort(key=lambda x: x.time)

    def insert_points(self, *times):
        for time in times:
            self.insert_point(time)

    def remove_point(self, index):
        self._items.pop(index)

    def get_index_at_time(self, time):
        time_ = obj_to_decimal(time)
        self.eval_time_range(time_)
        for index, point in enumerate(self._items):
            if point.time == time_:
                return index
        return None

    def get_point_at_time(self, time):
        index = self.get_index_at_time(time)
        if index is None:
            return None
        return self._items[index]


class Point:
    def __init__(self, time, text="", tier=None):
        if not isinstance(time, (int, float, str, decimal.Decimal)):
            msg = "time MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(text, str):
            msg = "text MUST BE a str."
            raise TypeError(msg)
        if not isinstance(tier, PointTier):
            msg = "parent MUST BE A PointTier"
            raise TypeError(msg)
        self._time = obj_to_decimal(time)
        self._text = text
        self._tier = tier

    @property
    def time(self):
        return self._time

    @property
    def xmin(self):
        return self._time

    @property
    def xmax(self):
        return self._time

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            msg = "text MUST BE a str"
            raise TypeError(msg)
        self._text = value

    def tier(self):
        return self._tier

    def textgrid(self):
        tier = self.tier()
        if tier is None:
            return None
        return tier.textgrid()
