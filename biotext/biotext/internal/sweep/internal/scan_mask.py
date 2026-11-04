def scan_mask(xseq, xmask):
    xseq_len = len(xseq)

    min_len = 10
    if xseq_len < min_len:
        xseq = xseq + "K" * (min_len - xseq_len)
        xseq = xseq[:min_len]

        xseq_len = min_len

    ids = (i for i, bit in enumerate(xmask) if bit)

    IDS = [range(idx, min(idx + xseq_len, xseq_len)) for idx in ids]

    lmx = min(map(len, IDS))

    xcols = [xseq[idx] for ids_array in IDS for idx in ids_array[:lmx]]

    xcols = [xcols[i : i + lmx] for i in range(0, len(xcols), lmx)]

    xcols = list(zip(*xcols))

    return xcols
