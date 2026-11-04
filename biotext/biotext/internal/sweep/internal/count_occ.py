from collections import Counter


def count_occ(input_list):
    count_dict = Counter(input_list)

    items, counts = zip(*sorted(count_dict.items()))

    return list(items), list(counts)
