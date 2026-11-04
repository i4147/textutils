from texting.bracket import br
from texting.chars import CO, LF, TB


def join_lines(lines, delim="", level=0, hover=True):
    ind = TB * level if level else ""
    return (
        f"{LF + ind + TB}{(delim + LF + ind + TB).join(lines)}{delim + LF + ind}"
        if hover
        else f"{ind + TB}{(delim + LF + ind + TB).join(lines)}{delim}"
    )


def liner(lines, delim=LF, level=0, bracket=None, discrete=False):
    if discrete:
        return lines
    hover = bool(bracket)
    joined = (
        join_lines(lines, CO if delim.find(CO) >= 0 else "", level, hover)
        if len(lines) and delim.find(LF) >= 0
        else delim.join(lines)
    )
    return br(joined, bracket)
