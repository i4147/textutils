from collections import Counter


def count_occurrences(input_list):

    counts = Counter(input_list)

    unique_items = list(counts.keys())
    counts = list(counts.values())

    sorted_items_counts = sorted(zip(unique_items, counts), key=lambda x: x[1], reverse=True)

    unique_items, counts = zip(*sorted_items_counts)

    return (unique_items, counts)
