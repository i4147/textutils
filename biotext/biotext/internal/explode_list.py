def explode_list(lists_of_lists, return_indices=False):
    flattened_list = []
    indices = []

    for sublist_idx, sublist in enumerate(lists_of_lists):
        for item_idx, item in enumerate(sublist):
            flattened_list.append(item)
            indices.append((sublist_idx, item_idx))

    if return_indices:
        return flattened_list, indices
    else:
        return flattened_list
