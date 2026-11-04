import re

from texting import LF, SP

SPACE = re.compile("\s+")
LINEFEED = re.compile("\r?\n")


def fold_to_vector(text: str, width=80, regex=SPACE, first_line_indent=0):
    lines = []
    pr = cu = la = 0
    th = pr + width
    if first_line_indent:
        text = SP * first_line_indent + text
    for match in regex.finditer(text):
        nx = match.start()
        if nx > th:
            lines.append(text[pr:cu])
            th = (pr := la) + width
        if LINEFEED.search(match.group()):
            lines.append(text[pr:nx])
            th = (pr := match.end()) + width
        cu = nx
        la = match.end()
    if len(text) > th:
        lines.append(text[(pr := la) : cu])
    if pr < len(text):
        lines.append(text[pr:])
    if first_line_indent:
        lines[0] = lines[0][first_line_indent:]
    return lines


def fold(text, width=80, delim=LF, regex=SPACE, first_line_indent=0):
    lines = fold_to_vector(text, width, regex, first_line_indent)
    return delim.join(lines)
