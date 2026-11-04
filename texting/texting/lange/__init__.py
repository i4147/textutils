from texting.has_ansi import ANSI, ASTRAL


def lange(tx):
    tx = ANSI.sub("", tx, 0)
    tx = ASTRAL.sub("_", tx, 0)
    return len(tx)
