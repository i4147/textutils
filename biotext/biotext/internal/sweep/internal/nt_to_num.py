def nt_to_num(xseq):
    n = len(xseq)
    m = len(xseq[0]) if n > 0 else 0

    mret = []

    for seq in xseq:
        vls = nt_to_int(seq)
        vls = [i - 1 for i in vls]
        if -1 in vls:
            mret.append(-1)
            continue

        pot = list(range(m))

        total = 0
        for i, p in enumerate(pot):
            total += (4**p) * vls[i]

        mret.append(total)

    return mret


def nt_to_int(nt_list):
    nt_map = {
        "A": 1,
        "B": 11,
        "C": 2,
        "D": 12,
        "E": 0,
        "F": 0,
        "G": 3,
        "H": 13,
        "I": 0,
        "J": 0,
        "K": 7,
        "L": 0,
        "M": 8,
        "N": 15,
        "O": 0,
        "P": 0,
        "Q": 0,
        "R": 5,
        "S": 9,
        "T": 4,
        "U": 4,
        "V": 14,
        "W": 10,
        "X": 15,
        "Y": 6,
        "Z": 0,
        "*": 0,
        "-": 16,
        "?": 0,
    }

    nt_list = [nt_map[aa] for aa in nt_list]

    return nt_list
