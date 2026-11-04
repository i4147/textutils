from texting.has_ansi.regs import ANSI, ASTRAL, HAN


def has_ansi(tx):
    return bool(ANSI.search(tx))


def has_han(tx):
    return bool(HAN.search(tx))


def has_astral(tx):
    return bool(ASTRAL.search(tx))
