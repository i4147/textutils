from intype import is_numeric

from texting.chars import SP
from texting.has_ansi import has_ansi
from texting.lange import lange


def lpad(text: str, width: int, fill: str = SP):
    return f"{text:{fill[0]}>{width}}"


def rpad(text: str, width: int, fill: str = SP):
    return f"{text:{fill[0]}<{width}}"


def cpad(text: str, width: int, fill: str = SP):
    return f"{text:{fill[0]}^{width}}"


def ansi_pad_len(tx, pd):
    return len(tx) + pd - lange(tx) if has_ansi(tx) else pd


def to_pad(fill=SP, ansi=True, dock=False):
    if dock:
        padder = lpad if dock < 0 else rpad
        return (
            (lambda tx, pd: padder(tx, ansi_pad_len(tx, pd), fill)) if ansi else (lambda tx, pd: padder(tx, pd, fill))
        )
    else:
        return (
            (lambda tx, pd, v: (lpad if is_numeric(v) else rpad)(tx, ansi_pad_len(tx, pd), fill))
            if ansi
            else (lambda tx, pd, v: (lpad if is_numeric(v) else rpad)(tx, pd, fill))
        )


def to_lpad(fill=SP, ansi=True):
    return (lambda tx, pd: lpad(tx, ansi_pad_len(tx, pd), fill)) if ansi else (lambda tx, pd: lpad(tx, pd, fill))


def to_rpad(fill=SP, ansi=True):
    return (lambda tx, pd: rpad(tx, ansi_pad_len(tx, pd), fill)) if ansi else (lambda tx, pd: rpad(tx, pd, fill))
