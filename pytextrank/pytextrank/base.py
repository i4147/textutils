# -*- coding: utf-8 -*-


from collections import Counter, defaultdict, OrderedDict
from dataclasses import dataclass
import json
import math
import pathlib
import time
import typing

from icecream import ic
from spacy.tokens import Doc, Span, Token
import graphviz
import networkx as nx

from .util import groupby_apply, default_scrubber

try:
    import altair as alt
    import pandas as pd
except ImportError:
    _has_altair_and_pandas = False
else:
    _has_altair_and_pandas = True

StopWordsLike = typing.Union[str, pathlib.Path, typing.Dict[str, typing.List[str]]]


@dataclass(order=True, frozen=True)
class Lemma:
    lemma: str
    pos: str

    def label(self) -> str:
        return str((
            self.lemma,
            self.pos,
        ))


@dataclass
class Phrase:
    text: str
    chunks: typing.List[Span]
    count: int
    rank: float


@dataclass
class Sentence:
    start: int
    end: int
    sent_id: int
    phrases: typing.Set[int]
    distance: float

    def empty(self) -> bool:
        return len(self.phrases) == 0

    def text(
        self,
        doc: Doc,
    ) -> str:
        return doc[self.start : self.end]


@dataclass
class VectorElem:
    phrase: Phrase
    phrase_id: int
    coord: float


@dataclass
class Paragraph:
    start: int
    end: int
    para_id: int
    distance: float


class BaseTextRankFactory:
    _EDGE_WEIGHT: float = 1.0
    _POS_KEPT: typing.List[str] = ["ADJ", "NOUN", "PROPN", "VERB"]
    _TOKEN_LOOKBACK: int = 3

    def __init__(
        self,
        *,
        edge_weight: float = _EDGE_WEIGHT,
        pos_kept: typing.List[str] = None,
        token_lookback: int = _TOKEN_LOOKBACK,
        scrubber: typing.Optional[typing.Callable] = None,
        stopwords: typing.Optional[StopWordsLike] = None,
    ) -> None:
        self.edge_weight: float = edge_weight
        self.token_lookback: int = token_lookback

        if pos_kept:
            self.pos_kept: typing.List[str] = pos_kept
        else:
            self.pos_kept = self._POS_KEPT

        if scrubber:
            self.scrubber: typing.Callable = scrubber
        else:
            self.scrubber = default_scrubber

        if stopwords:
            self.stopwords: typing.Dict[str, typing.List[str]] = self._load_stopwords(stopwords)
        else:
            self.stopwords = defaultdict(list)

    @classmethod
    def _load_stopwords(
        cls,
        stopwords: typing.Optional[StopWordsLike] = None,
    ) -> typing.Dict[str, typing.List[str]]:
        if isinstance(stopwords, dict):
            return stopwords

        if isinstance(stopwords, pathlib.Path):
            path: pathlib.Path = stopwords
        else:
            path = pathlib.Path(str)

        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)

                if data:
                    return data.items()

        raise TypeError("cannot parse the stopwords source as a dictionary")

    def __call__(
        self,
        doc: Doc,
    ) -> Doc:
        Doc.set_extension("textrank", force=True, default=None)
        Doc.set_extension("phrases", force=True, default=[])

        doc._.textrank = BaseTextRank(
            doc,
            edge_weight=self.edge_weight,
            pos_kept=self.pos_kept,
            token_lookback=self.token_lookback,
            scrubber=self.scrubber,
            stopwords=self.stopwords,
        )

        doc._.phrases = doc._.textrank.calc_textrank()
        return doc


class BaseTextRank:
    def __init__(
        self,
        doc: Doc,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Callable,
        stopwords: typing.Dict[str, typing.List[str]],
    ) -> None:
        self.doc: Doc = doc
        self.edge_weight: float = edge_weight
        self.token_lookback: int = token_lookback
        self.pos_kept: typing.List[str] = pos_kept
        self.scrubber: typing.Callable = scrubber
        self.stopwords: typing.Dict[str, typing.List[str]] = stopwords

        self.focus_tokens: typing.Set[str] = set()
        self.node_bias = 1.0
        self.default_bias = 1.0

        self.elapsed_time: float = 0.0
        self.lemma_graph: nx.Graph = nx.Graph()
        self.phrases: typing.List[Phrase] = []
        self.ranks: typing.Dict[Lemma, float] = {}
        self.seen_lemma: typing.Dict[Lemma, typing.Set[int]] = OrderedDict()

    def reset(self) -> None:
        self.elapsed_time = 0.0
        self.lemma_graph = nx.Graph()
        self.phrases = []
        self.ranks = {}
        self.seen_lemma = OrderedDict()

    def calc_textrank(self) -> typing.List[Phrase]:
        t0 = time.time()
        self.reset()
        self.lemma_graph = self._construct_graph()

        self.ranks = nx.pagerank(
            self.lemma_graph,
            personalization=self.get_personalization(),
        )

        nc_phrases: typing.Dict[Span, float] = {}

        try:
            nc_phrases = self._collect_phrases(self.doc.noun_chunks, self.ranks)
        except NotImplementedError as ex:
            ic.disable()
            ic(ex)
            ic.enable()

        ent_phrases: typing.Dict[Span, float] = self._collect_phrases(self.doc.ents, self.ranks)
        all_phrases: typing.Dict[Span, float] = {**nc_phrases, **ent_phrases}

        raw_phrase_list: typing.List[Phrase] = self._get_min_phrases(all_phrases)
        phrase_list: typing.List[Phrase] = sorted(raw_phrase_list, key=lambda p: p.rank, reverse=True)

        t1 = time.time()
        self.elapsed_time = (t1 - t0) * 1000.0

        return phrase_list

    def get_personalization(self) -> typing.Optional[typing.Dict[Lemma, float]]:
        return None

    def _construct_graph(self) -> nx.Graph:
        g = nx.Graph()

        g.add_nodes_from(self.node_list)

        g.add_edges_from(self.edge_list)

        return g

    def _keep_token(
        self,
        token: Token,
    ) -> bool:
        lemma = token.lemma_.lower().strip()

        if self._is_stopword(lemma, token):
            return False

        if token.pos_ not in self.pos_kept:
            return False

        key = Lemma(
            lemma,
            token.pos_,
        )

        if key not in self.seen_lemma:
            self.seen_lemma[key] = set([token.i])
        else:
            self.seen_lemma[key].add(token.i)

        return True

    def _is_stopword(
        self,
        lemma: str,
        token: Token,
    ) -> bool:
        return lemma in self.stopwords and token.pos_ in self.stopwords[lemma]

    @property
    def node_list(self) -> typing.List[Lemma]:
        nodes: typing.List[Lemma] = [Lemma(token.lemma_, token.pos_) for token in self.doc if self._keep_token(token)]

        return nodes

    @property
    def edge_list(self) -> typing.List[typing.Tuple[Lemma, Lemma, typing.Dict[str, float]]]:
        edges: typing.List[typing.Tuple[Lemma, Lemma]] = []

        for sent in self.doc.sents:
            h = [Lemma(token.lemma_, token.pos_) for token in sent if self._keep_token(token)]

            for hop in range(self.token_lookback):
                for idx, node in enumerate(h[: -1 - hop]):
                    nbor = h[hop + idx + 1]
                    edges.append((node, nbor))

        weighted_edges: typing.List[typing.Tuple[Lemma, Lemma, typing.Dict[str, float]]] = [
            (*n, {"weight": w * self.edge_weight}) for n, w in Counter(edges).items()
        ]

        return weighted_edges

    def _collect_phrases(
        self, spans: typing.Iterable[Span], ranks: typing.Dict[Lemma, float]
    ) -> typing.Dict[Span, float]:
        phrases: typing.Dict[Span, float] = {
            span: sum(ranks[Lemma(token.lemma_, token.pos_)] for token in span if self._keep_token(token))
            for span in spans
        }

        return {span: self._calc_discounted_normalised_rank(span, sum_rank) for span, sum_rank in phrases.items()}

    def _calc_discounted_normalised_rank(self, span: Span, sum_rank: float) -> float:
        if len(span) < 1:
            return 0.0
        non_lemma = len([tok for tok in span if tok.pos_ not in self.pos_kept])
        non_lemma_discount = len(span) / (len(span) + (2.0 * non_lemma) + 1.0)

        phrase_rank = math.sqrt(sum_rank / (len(span) + non_lemma))

        return phrase_rank * non_lemma_discount

    def _get_min_phrases(self, all_phrases: typing.Dict[Span, float]) -> typing.List[Phrase]:
        try:
            data: typing.List[typing.Tuple[Span, float, Span]] = [
                (self.scrubber(span), rank, span) for span, rank in all_phrases.items()
            ]
        except AttributeError:
            raise FutureWarning("Text-based scrubbers are deprecated. Use a `Span` instead.")

        keyfunc = lambda x: x[0]
        applyfunc = lambda g: list((rank, spans) for text, rank, spans in g)

        phrases: typing.List[typing.Tuple[str, typing.List[typing.Tuple[float, Span]]]] = groupby_apply(
            data,
            keyfunc,
            applyfunc,
        )

        phrase_list: typing.List[Phrase] = [
            Phrase(
                text=p[0],
                rank=max(rank for rank, span in p[1]),
                count=len(p[1]),
                chunks=list(span for rank, span in p[1]),
            )
            for p in phrases
        ]

        return phrase_list

    def get_unit_vector(
        self,
        limit_phrases: int,
    ) -> typing.List[VectorElem]:
        unit_vector: typing.List[VectorElem] = [
            VectorElem(
                phrase=p,
                phrase_id=phrase_id,
                coord=p.rank,
            )
            for phrase_id, p in enumerate(self.doc._.phrases)
        ]

        limit = min(limit_phrases, len(unit_vector))
        unit_vector = unit_vector[:limit]

        sum_length = sum([elem.coord for elem in unit_vector])

        for elem in unit_vector:
            if sum_length > 0.0:
                elem.coord = elem.coord / sum_length
            else:
                elem.coord = 0.0

        return unit_vector

    def calc_sent_dist(
        self,
        limit_phrases: int,
    ) -> typing.List[Sentence]:
        unit_vector = self.get_unit_vector(limit_phrases)

        sent_dist: typing.List[Sentence] = [
            Sentence(
                start=s.start,
                end=s.end,
                sent_id=sent_id,
                phrases=set(),
                distance=0.0,
            )
            for sent_id, s in enumerate(self.doc.sents)
        ]

        for elem in unit_vector:
            for chunk in elem.phrase.chunks:
                for sent in sent_dist:
                    if chunk.start >= sent.start and chunk.end <= sent.end:
                        sent.phrases.add(elem.phrase_id)
                        break

        for sent in sent_dist:
            sum_sq = 0.0

            for elem in unit_vector:
                if elem.phrase_id not in sent.phrases:
                    sum_sq += elem.coord**2.0

            sent.distance = math.sqrt(sum_sq)

        return sent_dist

    def segment_paragraphs(
        self,
        sent_dist: typing.List[Sentence],
    ) -> typing.List[Paragraph]:
        para_elem: typing.List[int] = []
        para_bounds: typing.List[typing.List[int]] = []

        for sent_id, s in enumerate(self.doc.sents):
            toke_0 = str(s.__getitem__(0))
            ret_count = sum(map(lambda c: 1 if c == "\n" else 0, toke_0))

            if ret_count > 1:
                if len(para_elem) > 0:
                    para_bounds.append(para_elem)

                para_elem = []

            para_elem.append(sent_id)

        if len(para_elem) > 0:
            para_bounds.append(para_elem)

        para_list: typing.List[Paragraph] = []

        for para_id, para_elem in enumerate(para_bounds):
            sum_dist = [sent_dist[sent_id].distance for sent_id in para_elem]

            para_list.append(
                Paragraph(
                    para_id=para_id,
                    start=para_elem[0],
                    end=para_elem[-1],
                    distance=sum(sum_dist) / float(len(sum_dist)),
                )
            )

        return para_list

    def summary(
        self,
        *,
        limit_phrases: int = 10,
        limit_sentences: int = 4,
        preserve_order: bool = False,
        level: str = "sentence",
    ) -> typing.Iterator[str]:
        sent_dist: typing.List[Sentence] = self.calc_sent_dist(limit_phrases)

        if level == "sentence":
            top_sent_ids: typing.List[int] = [
                sent.sent_id for sent in sorted(sent_dist, key=lambda sent: sent.distance)
            ]

            limit = min(limit_sentences, len(top_sent_ids))
            top_sent_ids = top_sent_ids[:limit]

            if preserve_order:
                top_sent_ids.sort()

            for sent_id in top_sent_ids:
                yield sent_dist[sent_id].text(self.doc)

        if level == "paragraph":
            top_sent_ids = [
                sent_id
                for p in sorted(self.segment_paragraphs(sent_dist), key=lambda x: x.distance)
                for sent_id in range(p.start, p.end + 1)
            ]

            limit_para = min(limit_sentences, len(top_sent_ids))
            top_sent_ids = top_sent_ids[:limit_para]

            if preserve_order:
                top_sent_ids.sort()

            for sent_id in top_sent_ids:
                yield sent_dist[sent_id].text(self.doc)

    def write_dot(
        self,
        *,
        path: typing.Optional[typing.Union[str, pathlib.Path]] = "graph.dot",
    ) -> None:
        dot = graphviz.Graph()

        for lemma in self.lemma_graph.nodes():
            rank = self.ranks[lemma]
            key = lemma.label()

            label = "{} ({:.4f})".format(key, rank)
            dot.node(key, label)

        for edge in self.lemma_graph.edges():
            dot.edge(edge[0].label(), edge[1].label(), constraint="false")

        if isinstance(path, str):
            path = pathlib.Path(path)

        with open(path, "w") as f:
            f.write(dot.source)

    def plot_keyphrases(self) -> typing.Any:
        if not _has_altair_and_pandas:
            raise ImportError(
                "altair and pandas are required to use this method. Install them with `pip install 'pytextrank[viz]'`"
            )

        source = pd.DataFrame([p.__dict__ for p in self.doc._.phrases]).drop("chunks", axis=1).reset_index()

        c = (
            alt
            .Chart(source)
            .mark_bar()
            .encode(x="index", y="rank", color="count", tooltip=["text", "rank", "count"])
            .properties(title="Keyphrase profile of the document")
        )

        return c
