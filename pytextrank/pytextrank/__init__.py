# -*- coding: utf-8 -*-


import pathlib
import typing

from spacy.language import Language

from .base import BaseTextRankFactory, BaseTextRank, Lemma, Paragraph, Phrase, Sentence, VectorElem, StopWordsLike

from .biasedrank import BiasedTextRankFactory, BiasedTextRank

from .positionrank import PositionRankFactory, PositionRank

from .topicrank import TopicRankFactory, TopicRank

from .util import groupby_apply, default_scrubber, maniacal_scrubber, split_grafs, filter_quotes

from .version import get_repo_version, __version__, __version_major__, __version_minor__, __version_patch__


_DEFAULT_CONFIG = {
    "edge_weight": BaseTextRankFactory._EDGE_WEIGHT,
    "pos_kept": BaseTextRankFactory._POS_KEPT,
    "token_lookback": BaseTextRankFactory._TOKEN_LOOKBACK,
    "scrubber": None,
    "stopwords": None,
}

_TOPIC_DEFAULT_CONFIG = {
    **_DEFAULT_CONFIG,
    "threshold": TopicRankFactory._CLUSTER_THRESHOLD,
    "method": TopicRankFactory._CLUSTER_METHOD,
}


try:

    @Language.factory("textrank", default_config=_DEFAULT_CONFIG)
    def _create_component_tr(
        nlp: Language,
        name: str,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Optional[typing.Callable],
        stopwords: typing.Optional[StopWordsLike],
    ) -> BaseTextRankFactory:
        return BaseTextRankFactory(
            edge_weight=edge_weight,
            pos_kept=pos_kept,
            token_lookback=token_lookback,
            scrubber=scrubber,
            stopwords=stopwords,
        )

    @Language.factory("positionrank", default_config=_DEFAULT_CONFIG)
    def _create_component_pr(
        nlp: Language,
        name: str,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Optional[typing.Callable],
        stopwords: typing.Optional[StopWordsLike],
    ) -> PositionRankFactory:
        return PositionRankFactory(
            edge_weight=edge_weight,
            pos_kept=pos_kept,
            token_lookback=token_lookback,
            scrubber=scrubber,
            stopwords=stopwords,
        )

    @Language.factory("biasedtextrank", default_config=_DEFAULT_CONFIG)
    def _create_component_br(
        nlp: Language,
        name: str,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Optional[typing.Callable],
        stopwords: typing.Optional[StopWordsLike],
    ) -> BiasedTextRankFactory:
        return BiasedTextRankFactory(
            edge_weight=edge_weight,
            pos_kept=pos_kept,
            token_lookback=token_lookback,
            scrubber=scrubber,
            stopwords=stopwords,
        )

    @Language.factory("topicrank", default_config=_TOPIC_DEFAULT_CONFIG)
    def _create_component_tor(
        nlp: Language,
        name: str,
        edge_weight: float,
        pos_kept: typing.List[str],
        token_lookback: int,
        scrubber: typing.Optional[typing.Callable],
        stopwords: typing.Optional[StopWordsLike],
        threshold: float,
        method: str,
    ) -> TopicRankFactory:
        return TopicRankFactory(
            edge_weight=edge_weight,
            pos_kept=pos_kept,
            token_lookback=token_lookback,
            scrubber=scrubber,
            stopwords=stopwords,
            threshold=threshold,
            method=method,
        )

except Exception:
    print("ERROR: it appears that `spaCy` 3.x has not been imported?")
