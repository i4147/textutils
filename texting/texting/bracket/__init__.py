from texting.enum.brackets import ANG, BRC, BRK, PAR


def parenth(x):
    return "(" + str(x) + ")"


def bracket(x):
    return "[" + str(x) + "]"


def brace(x):
    return "{" + str(x) + "}"


def anglebr(x):
    return "<" + str(x) + ">"


def br(x, mode=BRK):
    if mode == PAR:
        return "(" + str(x) + ")"
    if mode == BRK:
        return "[" + str(x) + "]"
    if mode == BRC:
        return "{" + str(x) + "}"
    if mode == ANG:
        return "<" + str(x) + ">"
    return x


def to_br(mode):
    if mode == PAR:
        return parenth
    if mode == BRK:
        return bracket
    if mode == BRC:
        return brace
    if mode == ANG:
        return anglebr
    return None
