# -*- coding: utf-8 -*-


from collections import defaultdict
from functools import lru_cache
import time
import typing

from icecream import ic
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import pdist
from spacy.tokens import Doc, Span
import networkx as nx

from .base import BaseTextRank, BaseTextRankFactory, Phrase, StopWordsLike


class TopicRankFactory(BaseTextRankFactory):
    _CLUSTER_THRESHOLD: float = 0.25
    _CLUSTER_METHOD: str = "average"

    def __init__(
        self,
        *,
        edge_weight: float = BaseTextRankFactory._EDGE_WEIGHT,
        pos_kept: typing.List[str] = None,
        token_lookback: int = BaseTextRankFactory._TOKEN_LOOKBACK,
        scrubber: typing.Optional[typing.Callable] = None,
        stopwords: typing.Optional[StopWordsLike] = None,
        threshold: float = _CLUSTER_THRESHOLD,
        method: str = _CLUSTER_METHOD,
    ) -> None:
        super().__init__(
            edge_weight=edge_weight,
            pos_kept=pos_kept,
            token_lookback=token_lookback,
            scrubber=scrubber,
            stopwords=stopwords,
        )

        self.threshold: float = threshold
        self.method: str = method

    def __call__(
        self,
        doc: Doc,
    ) -> Doc:
        Doc.set_extension("textrank", force=True, default=None)
        Doc.set_extension("phrases", force=True, default=[])

        doc._.textrank = TopicRank(
            doc,
            edge_weight=self.edge_weight,
            pos_kept=self.pos_kept,
            token_lookback=self.token_lookback,
            scrubber=self.scrubber,
            stopwords=self.stopwords,
            threshold=self.threshold,
            method=self.method,
        )

        doc._.phrases = doc._.textrank.calc_textrank()
        return doc


class TopicRank(BaseTextRank):
    def __init__(
        self,
        doc: Doc,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Callable,
        stopwords: typing.Dict[str, typing.List[str]],
        threshold: float,
        method: str,
    ) -> None:
        super().__init__(doc, edge_weight, pos_kept, token_lookback, scrubber, stopwords)

        self.threshold: float = threshold
        self.method: str = method

    def _cluster(
        self,
        candidates: typing.List[Span],
    ) -> typing.List[typing.List[Span]]:
        if not candidates:
            return []

        bag_of_words = list({word.text for candidate in candidates for word in candidate if not word.is_stop})

        # matrix = [[0] * len(bag_of_words) for _ in candidates]
        matrix = []

        for candidate in candidates:
            matrix.append([0] * len(bag_of_words))

            for term in candidate:
                if not term.is_stop:
                    try:
                        matrix[-1][bag_of_words.index(term.text)] += 1
                    except IndexError:
                        pass

        pairwise_dist = pdist(matrix, "jaccard")

        if not pairwise_dist.size:
            return [[candidate] for candidate in candidates]

        raw_clusters = linkage(pairwise_dist, method=self.method)
        cluster_ids = fcluster(raw_clusters, t=0.99 - self.threshold, criterion="distance")

        clusters = defaultdict(list)

        for cluster_id, candidate in zip(cluster_ids, candidates):
            clusters[cluster_id].append(candidate)

        return list(clusters.values())

    def _get_candidates(self) -> typing.List[Span]:
        candidates: typing.List[Span] = []

        try:
            noun_chunks = list(self.doc.noun_chunks)

            for chunk in noun_chunks:
                for token in chunk:
                    if self._keep_token(token):
                        candidates.append(self.doc[token.i : chunk.end])
                        break
        except NotImplementedError as ex:
            ic.disable()
            ic(ex)
            ic.enable()

        return candidates

    @property
    @lru_cache(maxsize=1)
    def node_list(self) -> typing.List[typing.Tuple[Span, ...]]:
        candidates = self._get_candidates()

        clustered = [tuple(cluster) for cluster in self._cluster(candidates)]

        return clustered

    @property
    def edge_list(
        self,
    ) -> typing.List[typing.Tuple[typing.List[Span], typing.List[Span], typing.Dict[str, float]]]:
        weighted_edges = []

        for i, source_topic in enumerate(self.node_list):
            for target_topic in self.node_list[i + 1 :]:
                weight = 0.0

                for source_member in source_topic:
                    for target_member in target_topic:
                        distance = abs(source_member.start - target_member.start)

                        if distance:
                            weight += 1.0 / distance

                weight_dict = {"weight": weight * self.edge_weight}
                weighted_edges.append((source_topic, target_topic, weight_dict))
                weighted_edges.append((target_topic, source_topic, weight_dict))

        return weighted_edges

    def calc_textrank(self) -> typing.List[Phrase]:
        t0 = time.time()
        self.reset()

        self.lemma_graph = self._construct_graph()

        self.ranks: typing.Dict[typing.List[Span], float] = nx.pagerank(
            self.lemma_graph,
            personalization=self.get_personalization(),
        )

        raw_phrase_list = [
            Phrase(
                text=self.scrubber(
                    min(
                        ((keyphrase, keyphrase.start) for keyphrase in topic),
                        key=lambda tup: tup[1],
                    )[0]
                ),
                chunks=list(topic),
                count=len(topic),
                rank=score,
            )
            for topic, score in self.ranks.items()
        ]

        phrase_list: typing.List[Phrase] = sorted(raw_phrase_list, key=lambda p: p.rank, reverse=True)

        t1 = time.time()
        self.elapsed_time = (t1 - t0) * 1000.0

        return phrase_list

    def reset(self) -> None:
        super().reset()
        TopicRank.node_list.fget.cache_clear()
