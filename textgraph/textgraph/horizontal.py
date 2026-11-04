# coding: utf-8

import collections
import shutil


def horizontal(data, width=shutil.get_terminal_size().columns, character="█"):
    parts = [character * i for i in range(0, width)]

    if isinstance(data, list):
        if isinstance(data[0], tuple):
            labels = [k for k, v in data]
            nums = [v for k, v in data]
        else:
            labels = None
            nums = data
    elif isinstance(data, collections.OrderedDict):
        labels = [k for k in data.keys()]
        nums = [v for v in data.values()]

    fraction = max(nums) / float(len(parts) - 1)

    if labels:
        max_length = len(max(labels, key=len))
        labels = [x + " " * (max_length - len(x)) for x in labels]

        out = ""
        for index, value in enumerate(nums):
            out = out + labels[index]
            out = out + " " + parts[int(round(value / fraction))]
            out = out + "\n"
        return out

    return "".join(parts[int(round(x / fraction))] + "\n" for x in nums)
