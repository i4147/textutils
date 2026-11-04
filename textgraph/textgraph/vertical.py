# coding: utf-8

import math


def vertical(nums, height=10, character="▉"):
    fraction = max(nums) / float(height)
    nums = [int(math.ceil(n / fraction)) for n in nums]

    out = ""
    row_numbers = list(range(1, height + 1))
    row_numbers.reverse()
    for i in row_numbers:
        for j in nums:
            if j >= i:
                out = out + character
            else:
                out = out + " "
        out = out + "\n"
    return out
