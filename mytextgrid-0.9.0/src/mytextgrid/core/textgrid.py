import decimal
from mytextgrid.core.interval_tier import IntervalTier
from mytextgrid.core.point_tier import PointTier
from mytextgrid.eval import obj_to_decimal
from mytextgrid.io import textgrid_out

decimal.getcontext().prec = 16


def create_textgrid(xmin=0, xmax=1):
    return TextGrid(xmin, xmax)


class TextGrid:
    def __init__(self, xmin=0, xmax=1):
        if not isinstance(xmin, (int, float, str, decimal.Decimal)):
            msg = "xmin MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        if not isinstance(xmax, (int, float, str, decimal.Decimal)):
            msg = "xmax MUST BE an int, float, str or decimal.Decimal."
            raise TypeError(msg)
        xmin_ = obj_to_decimal(xmin)
        xmax_ = obj_to_decimal(xmax)
        assert xmax_ > xmin_, "xmax MUST BE greater than xmin"
        self._xmin = xmin_
        self._xmax = xmax_
        self._tiers = []

    @property
    def xmin(self):
        return self._xmin

    @property
    def xmax(self):
        return self._xmax

    @property
    def tiers(self):
        return self._tiers

    def __len__(self):
        return len(self._tiers)

    def __iter__(self):
        return iter(self._tiers)

    def __getitem__(self, key):
        return self._tiers[key]

    def describe(self):
        size = len(self._tiers)
        summary = []
        for index, tier in enumerate(self._tiers):
            tier_class = "IntervalTier" if tier.is_interval() else "PointTier"
            summary.append(f"    {index}\t{tier_class}\t{tier.name}\t(size = {len(tier)})")
        summary_str = ""
        if size > 0:
            content = "\n".join(summary)
            head = "Tiers summary:"
            summary_str = f"\n{head}\n{content}"
        message = (
            "TextGrid:\n"
            f"    Startig time (sec):    {self.xmin}\n"
            f"    Ending time (sec):     {self.xmax}\n"
            f"    Number of tiers:       {size}"
            f"{summary_str}"
        )
        print(message)

    def duration(self):
        return self._xmax - self._xmin

    def insert_tier(self, name, interval_tier=True, index=None):
        if index is None:
            index = len(self)
        if not isinstance(index, int):
            msg = "index MUST BE a int value."
            raise ValueError(msg)
        if interval_tier:
            tier = IntervalTier(name, self._xmin, self._xmax, self)
        else:
            tier = PointTier(name, self._xmin, self._xmax, self)
        self.tiers.insert(index, tier)
        return tier

    def remove_tier(self, index):
        return self._tiers.pop(index)

    def get_tier_by_name(self, tier_name):
        if not isinstance(tier_name, str):
            msg = "tier MUST BE a str"
            raise TypeError(msg)
        list_ = [tier for tier in self._tiers if tier.name == tier_name]
        return list_

    def to_dict(self):
        tiers_list = []
        for tier in self._tiers:
            items_list = []
            for item in tier:
                if tier.is_interval():
                    item = {"xmin": item.xmin, "xmax": item.xmax, "text": item.text}
                else:
                    item = {"number": item.time, "mark": item.text}
                items_list.append(item)
            tiers_list.append({"interval_tier": tier.is_interval(), "name": tier.name, "items": items_list})
        textgrid_dict = {"xmin": self._xmin, "xmax": self._xmax, "tiers": tiers_list}
        return textgrid_dict

    def write(self, path, short_format=False, encoding="utf-8"):
        textgrid_out.textgrid_to_text_file(self, path, short_format, encoding)

    def write_as_json(self, *args, **kwds):
        textgrid_out.textgrid_to_json(self, *args, **kwds)
