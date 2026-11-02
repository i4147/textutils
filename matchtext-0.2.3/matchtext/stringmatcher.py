from dataclasses import dataclass
import sys
from matchtext.runutils import ensurelogger, set_logger
from .utils import thisorthat


@dataclass(unsafe_hash=True, order=True)
class Match:
    __slots__ = ("end", "entrydata", "match", "matcherdata", "start")
    start: int
    end: int
    match: list
    entrydata: object
    matcherdata: object


_NOVALUE = object()


class _Node:
    __slots__ = ("children", "value")

    def __init__(self):
        self.children = dict()
        self.value = _NOVALUE

    def debug_print_node(self, file=sys.stderr):
        if self.value == _NOVALUE:
            print(f"Node(val=,children=[", end="", file=file)
        else:
            print(f"Node(val={self.value},children=[", end="", file=file)
        for c, n in self.children.items():
            print(f"{c}:", end="", file=file)
            n.print_node()
        print("])", end="", file=file)


class StringMatcher:
    def __init__(self, ignorefunc=None, mapfunc=None, matcherdata=None, defaultdata=None):
        self.ignorefunc = ignorefunc
        self.mapfunc = mapfunc
        self.defaultdata = defaultdata
        self.matcherdata = matcherdata
        self._root = _Node()

    def add(self, entry, data=None, listdata=None, append=False):
        if isinstance(entry, str):
            entry = [entry]
        for e in entry:
            node = self._get_node(e, create=True)
            if node == self._root:
                continue
            if node.value == _NOVALUE:
                if append:
                    node.value = [data]
                else:
                    node.value = data
            elif append:
                node.value.append(data)
            else:
                node.value = data

    def find(self, text, all=False, skip=True, fromidx=None, toidx=None, matchmaker=None):
        logger = ensurelogger()
        logger.debug("CALL")
        matches = []
        l = len(text)
        if fromidx is None:
            fromidx = 0
        if toidx is None:
            toidx = l - 1
        if fromidx >= l:
            return matches
        if toidx >= l:
            toidx = l - 1
        if fromidx > toidx:
            return matches
        i = fromidx
        logger.debug(f"From index {i} to index {toidx} for {text}")
        while i < toidx:
            chr = text[i]
            if self.ignorefunc and self.ignorefunc(chr):
                i += 1
                continue
            if self.mapfunc:
                chr = self.mapfunc(chr)
            longest_len = 0
            longest_match = None
            node = self._root
            node = node.children.get(chr)
            k = 0
            while node is not None:
                if node.value != _NOVALUE:
                    cur_len = k + 1
                    if matchmaker:
                        match = matchmaker(
                            i,
                            i + k + 1,
                            text[i : i + k + 1],
                            thisorthat(node.value, self.defaultdata),
                            self.matcherdata,
                        )
                    else:
                        match = Match(
                            i,
                            i + k + 1,
                            text[i : i + k + 1],
                            thisorthat(node.value, self.defaultdata),
                            self.matcherdata,
                        )
                    if all:
                        matches.append(match)
                    elif cur_len > longest_len:
                        longest_len = cur_len
                        longest_match = match
                while True:
                    k += 1
                    if i + k >= len(text):
                        break
                    chr = text[i + k]
                    if self.ignorefunc and self.ignorefunc(chr):
                        continue
                    if self.mapfunc:
                        chr = self.mapfunc(chr)
                    node = node.children.get(chr)
                    break
                if i + k >= len(text):
                    break
            if not all and longest_match is not None:
                matches.append(longest_match)
            if skip:
                i += max(k, 1)
            else:
                i += 1
        return matches

    def __setitem__(self, key, value):
        node = self._get_node(key, create=True)
        node.value = value

    def __getitem__(self, item):
        node = self._get_node(item, create=False, raise_error=True)
        if node.value == _NOVALUE:
            raise KeyError(item)
        return node.value

    def get(self, item, default=None):
        node = self._get_node(item, create=False, raise_error=False)
        if node is None:
            return default
        if node.value == _NOVALUE:
            return default
        return node.value

    def _get_node(self, item, create=False, raise_error=True):
        node = self._root
        for el in item:
            if self.ignorefunc and self.ignorefunc(el):
                continue
            if self.mapfunc:
                el = self.mapfunc(el)
            if create:
                node = node.children.setdefault(el, _Node())
            else:
                node = node.children.get(el)
                if not node:
                    if raise_error:
                        raise KeyError(item)
                    else:
                        return None
        return node

    def replace(self, text, fromidx=None, toidx=None, getter=None, replacer=None, matchmaker=None):
        matches = self.find(text, fromidx=fromidx, toidx=toidx, all=False, skip=True, matchmaker=matchmaker)
        if len(matches) == 0:
            return text
        parts = []
        last = 0
        for match in matches:
            if match.start > last:
                parts.append(text[last : match.start])
            if match.start >= last:
                if replacer:
                    rep = replacer(match)
                else:
                    rep = str(match.entrydata)
                parts.append(rep)
                last = match.end
        if last < len(text):
            parts.append(text[last:])
        return "".join(parts)
