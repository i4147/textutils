import re

from texting.chars import COLF, COSP, LF, RN, TB, VO
from texting.indexing import after_nontab, index_nontab


def tag(label, item):
    i = index_nontab(label)
    key, text = str(label), str(item)
    if not key.endswith(")"):
        key = f"{key[0:i]}[{key[i:]}]"
    if re.search(LF, text):
        t = " " * i
        if (text.endswith("}") or text.endswith("]")) and not text.endswith("]]"):
            text = RN.join(after_nontab([t + x for x in text.split(RN)]))
        else:
            text = RN.join([""] + ([t + TB + x for x in text.split(RN)]) + [TB])
    return f"{key} ({text})"


def tags(*labels, **items):
    if (size := len(labels)) == 0:
        label = ""
    elif size == 1:
        label = f"[{labels[0]}]"
    else:
        label = labels[0]
        for v in labels[1:]:
            label = tag(label, v)
    for key, item in items.items():
        label = label + COLF + tag(key, item)
    return label


def link(label, item):
    if (label := str(label)) and (item := str(item)):
        return label + COSP + item
    if label:
        return label
    if item:
        return item
    return VO
