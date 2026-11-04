def split_array(arr, chunk_size):
    chunks = []
    for i in range(0, len(arr), chunk_size):
        chunks.append(arr[i : i + chunk_size])
    return chunks
