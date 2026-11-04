def aa_to_num(xseq):
    n = len(xseq)
    m = len(xseq[0]) if n > 0 else 0

    mret = []

    for seq in xseq:
        vls = aa_to_int(seq)
        vls = [i - 1 for i in vls]
        if -1 in vls:
            mret.append(-1)
            continue

        pot = list(range(m))

        total = 0
        for i, p in enumerate(pot):
            total += (20**p) * vls[i]

        mret.append(total)

    return mret


def aa_to_int(aa_list):
    aa_map = {
        "A": 1,
        "B": 21,
        "C": 5,
        "D": 4,
        "E": 7,
        "F": 14,
        "G": 8,
        "H": 9,
        "I": 10,
        "J": 0,
        "K": 12,
        "L": 11,
        "M": 13,
        "N": 3,
        "O": 0,
        "P": 15,
        "Q": 6,
        "R": 2,
        "S": 16,
        "T": 17,
        "U": 0,
        "V": 20,
        "W": 18,
        "X": 23,
        "Y": 19,
        "Z": 22,
        "*": 24,
        "-": 25,
        "?": 0,
    }

    aa_list = [aa_map[aa] for aa in aa_list]

    return aa_list
