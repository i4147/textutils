import decimal
from mytextgrid.core.tier import Tier
from mytextgrid.eval import obj_to_decimal

decimal.getcontext().prec = 16


class IntervalTier(Tier):
    def __init__(self, name="", xmin=0, xmax=1, textgrid=None):
        is_interval = True
        super().__init__(name, xmin, xmax, is_interval, textgrid)
        self._items = [Interval(self._xmin, self._xmax, "", self)]

    def insert_boundaries(self, *times):
        for time in times:
            self.insert_boundary(time)

    def insert_boundary(self, time):
        time_ = obj_to_decimal(time)
        self.eval_time_range(time_)
        index = self.get_index_at_time(time_)
        old_interval = self._items[index]
        if old_interval.xmin == time_:
            msg = f"There is already a boundary at {time_}"
            raise ValueError(msg)
        new_left_interval = Interval(
            old_interval.xmin,
            time_,
            old_interval.text,
            self,
        )
        new_right_interval = Interval(
            time_,
            old_interval.xmax,
            "",
            self,
        )
        self._items[index] = new_left_interval
        self._items.insert(index + 1, new_right_interval)
        return (index, index + 1)

    def remove_boundary(self, time):
        time_ = obj_to_decimal(time)
        self.eval_time_range(time_)
        index = self.get_index_at_time_boundary(time_)
        if index is None:
            msg = f"No boundary to remove at {time}."
            raise ValueError(msg)
        interval_left = self._items[index - 1]
        interval_right = self._items[index]
        new_interval = Interval(
            self, xmin=interval_left.xmin, xmax=interval_right.xmax, text=interval_left.text + interval_right.text
        )
        self._items[index] = new_interval
        self._items.remove(interval_left)

    def move_boundary(self, src_time, dst_time):
        src_time_ = obj_to_decimal(src_time)
        dst_time_ = obj_to_decimal(dst_time)
        if src_time_ == dst_time_:
            msg = "src_time and dst_time MUST NOT BE equal"
            raise ValueError(msg)
        self.eval_time_range(src_time_)
        self.eval_time_range(dst_time_)
        index = self.get_index_at_time_boundary(src_time_)
        if index is None:
            msg = f"No boundary found at src_time ({src_time_})"
            raise ValueError(msg)
        left_interval = self._items[index - 1]
        right_interval = self._items[index]
        if left_interval.xmin >= dst_time_ >= right_interval.xmax:
            msg = "Cannot move the source boundary outside its neighbors boundaries."
            raise ValueError(msg)
        new_left_interval = Interval(self, xmin=left_interval.xmin, xmax=dst_time_, text=left_interval.text)
        new_right_interval = Interval(self, xmin=dst_time_, xmax=right_interval.xmax, text=right_interval.text)
        self._items[index - 1] = new_left_interval
        self._items[index] = new_right_interval

    def set_text_at_index(self, index, *text_items):
        if (index + len(text_items) - 1) > len(self._items):
            msg = "more text items than intervals."
            raise IndexError(msg)
        for index_, text in enumerate(text_items, start=index):
            self._items[index_].text = text

    def get_index_at_time(self, time):
        time_ = obj_to_decimal(time)
        if time_ == self._xmax:
            return len(self._items) - 1
        for index, interval in enumerate(self._items):
            if interval.xmin <= time_ < interval.xmax:
                return index
        return None

    def get_interval_at_time(self, time):
        index = self.get_index_at_time(time)
        if index is None:
            return None
        return self._items[index]

    def get_index_at_time_boundary(self, time):
        time_ = obj_to_decimal(time)
        for index, interval in enumerate(self._items):
            if index == 0:
                continue
            if interval.xmin == time_:
                return index
        return None


class Interval:
    def __init__(self, xmin, xmax, text="", tier=None):
        if not isinstance(xmin, (int, float, str, decimal.Decimal)):
            msg = "xmin MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(xmax, (int, float, str, decimal.Decimal)):
            msg = "xmax MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(text, str):
            msg = "text MUST BE a str."
            raise TypeError(msg)
        if not isinstance(tier, IntervalTier):
            msg = "tier MUST BE AN IntervalTier"
            raise TypeError(msg)
        xmin_ = obj_to_decimal(xmin)
        xmax_ = obj_to_decimal(xmax)
        assert xmax_ > xmin_, "xmax MUST BE greater than xmin"
        self._tier = tier
        self._xmin = xmin_
        self._xmax = xmax_
        self._text = text

    @property
    def xmin(self):
        return self._xmin

    @property
    def xmax(self):
        return self._xmax

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        if not isinstance(value, str):
            msg = "text MUST BE a str"
            raise TypeError(msg)
        self._text = value

    def duration(self):
        return self._xmax - self._xmin

    def tier(self):
        return self._tier

    def textgrid(self):
        tier = self.tier()
        if tier is None:
            return None
        return tier.textgrid()
