# coding: utf-8


def spark(nums, characters=" ▁▂▃▄▅▆▇█"):
    fraction = max(nums) / float(len(characters) - 1)
    return "".join(characters[int(round(x / fraction))] for x in nums)
