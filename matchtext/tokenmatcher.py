from collections import defaultdict
from dataclasses import dataclass
import sys
from matchtext.runutils import ensurelogger, set_logger
from matchtext.utils import thisorthat


@dataclass(unsafe_hash=True, order=True)
class Match:
    __slots__ = ("end", "entrydata", "match", "matcherdata", "start")
    start: int
    end: int
    match: list
    entrydata: object
    matcherdata: object


class Node(object):
    __slots__ = ("data", "is_match", "nodes")

    def __init__(self, is_match=None, data=None, nodes=None):
        self.is_match = is_match
        self.data = data
        self.nodes = nodes

    @staticmethod
    def dict_repr(nodes):
        if nodes is not None:
            return str([(t, n) for t, n in nodes.items()])
        return None

    def __repr__(self):
        nodes = Node.dict_repr(self.nodes)
        return f"Node(is_match={self.is_match},data={self.data},nodes={nodes})"


class TokenMatcher:
    def __init__(self, ignorefunc=None, mapfunc=None, matcherdata=None, defaultdata=None):
        self.nodes = defaultdict(Node)
        self.ignorefunc = ignorefunc
        self.mapfunc = mapfunc
        self.defaultdata = defaultdata
        self.matcherdata = matcherdata

    def add(self, entry, data=None, append=False, listdata=None):
        if isinstance(entry, str):
            entry = [entry]
        node = None
        i = 0
        for token in entry:
            if self.mapfunc is not None:
                token = self.mapfunc(token)
            if self.ignorefunc is not None and self.ignorefunc(token):
                continue
            if i == 0:
                node = self.nodes[token]
            elif node.nodes is None:
                node.nodes = defaultdict(Node)
                tmpnode = Node()
                node.nodes[token] = tmpnode
                node = tmpnode
            else:
                node = node.nodes[token]
            i += 1
        if append and data is not None:
            if node.data:
                node.data.append(data)
            else:
                node.data = [data]
                node.is_match = True
        else:
            node.data = data
            node.is_match = True

    def find(self, tokens, all=False, skip=True, fromidx=None, toidx=None, getter=None, matchmaker=None):
        logger = ensurelogger()
        logger.debug("CALL")
        matches = []
        l = len(tokens)
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
        logger.debug(f"From index {i} to index {toidx} for {tokens}")
        while i <= toidx:
            token_obj = tokens[i]
            if getter:
                token = getter(token_obj)
            else:
                token = token_obj
            logger.debug(f"Check token {i}={token}")
            if self.mapfunc:
                token = self.mapfunc(token)
            if token in self.nodes:
                longest = 0
                node = self.nodes[token]
                logger.debug(f"Got a first token match for {token}")
                thismatches = []
                thistokens = [token]
                if node.is_match:
                    logger.debug(f"First token match is also entry match")
                    longest = 1
                    if matchmaker:
                        match = matchmaker(
                            i, i + 1, thistokens.copy(), thisorthat(node.data, self.defaultdata), self.matcherdata
                        )
                    else:
                        match = Match(
                            i, i + 1, thistokens.copy(), thisorthat(node.data, self.defaultdata), self.matcherdata
                        )
                    thismatches.append(match)
                j = i + 1
                nignored = 0
                while j <= toidx:
                    logger.debug(f"j={j}")
                    if node.nodes:
                        tok = tokens[j]
                        if self.mapfunc:
                            tok = self.mapfunc(tok)
                        if self.ignorefunc and self.ignorefunc(tok):
                            j += 1
                            nignored += 1
                            continue
                        if tok in node.nodes:
                            logger.debug(f"Found token {tok}")
                            node = node.nodes[tok]
                            thistokens.append(tok)
                            if node.is_match:
                                logger.debug(f"Also is entry match")
                                if matchmaker:
                                    match = matchmaker(
                                        i,
                                        i + len(thistokens) + nignored,
                                        thistokens.copy(),
                                        thisorthat(node.data, self.defaultdata),
                                        self.matcherdata,
                                    )
                                else:
                                    match = Match(
                                        i,
                                        i + len(thistokens) + nignored,
                                        thistokens.copy(),
                                        thisorthat(node.data, self.defaultdata),
                                        self.matcherdata,
                                    )
                                if all:
                                    thismatches.append(match)
                                    longest = max(longest, len(thistokens))
                                elif len(thistokens) > longest:
                                    thismatches = [match]
                                    longest = len(thistokens)
                            j += 1
                            continue
                        else:
                            logger.debug(f"Breaking: {tok} does not match, j={j}")
                            break
                    else:
                        logger.debug("Breaking: no nodes")
                        break
                logger.debug(f"Going through thismatches: {thismatches}")
                for m in thismatches:
                    matches.append(m)
                if thismatches and skip:
                    i += longest - 1
            i += 1
            logger.debug(f"Incremented i to {i}")
        return matches

    def replace(self, tokens, fromidx=None, toidx=None, getter=None, replacer=None, matchmaker=None):
        tokens = tokens.copy()
        matches = self.find(
            tokens, fromidx=fromidx, toidx=toidx, all=False, skip=True, getter=getter, matchmaker=matchmaker
        )
        matches = sorted(matches, key=lambda x: x.start, reverse=True)
        for match in matches:
            if replacer:
                rep = replacer(match)
            else:
                rep = [match.entrydata]
            tokens[match.start : match.end] = rep
        return tokens
