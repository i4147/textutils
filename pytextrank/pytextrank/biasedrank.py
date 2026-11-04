# -*- coding: utf-8 -*-


import typing

from spacy.tokens import Doc, Token

from .base import BaseTextRankFactory, BaseTextRank, Lemma, Phrase


class BiasedTextRankFactory(BaseTextRankFactory):
    def __call__(
        self,
        doc: Doc,
    ) -> Doc:
        Doc.set_extension("textrank", force=True, default=None)
        Doc.set_extension("phrases", force=True, default=[])

        doc._.textrank = BiasedTextRank(
            doc,
            edge_weight=self.edge_weight,
            pos_kept=self.pos_kept,
            token_lookback=self.token_lookback,
            scrubber=self.scrubber,
            stopwords=self.stopwords,
        )

        doc._.phrases = doc._.textrank.calc_textrank()
        return doc


class BiasedTextRank(BaseTextRank):
    _DEFAULT_BIAS: float = 1.0

    def _get_node_bias(
        self,
        token: Token,
    ) -> float:
        if token.text.lower() in self.focus_tokens:
            return self.node_bias

        if token.lemma_.lower() in self.focus_tokens:
            return self.node_bias

        return self.default_bias

    def get_personalization(
        self,
    ) -> typing.Optional[typing.Dict[Lemma, float]]:

        weighted_nodes: typing.Dict[Lemma, float] = {
            Lemma(token.lemma_, token.pos_): self._get_node_bias(token)
            for token in self.doc
            if token.pos_ in self.pos_kept
        }

        total_weight = sum(weighted_nodes.values())

        if total_weight == 0.0:
            return None

        normalized_weighted_nodes: typing.Dict[Lemma, float] = {
            lemma: weight / total_weight for lemma, weight in weighted_nodes.items()
        }

        return normalized_weighted_nodes

    def change_focus(
        self,
        focus: str = None,
        bias: float = _DEFAULT_BIAS,
        default_bias: float = _DEFAULT_BIAS,
    ) -> typing.List[Phrase]:
        if focus:
            self.focus_tokens = set(focus.lower().split(" "))
        else:
            self.focus_tokens = set()

        self.node_bias = bias
        self.default_bias = default_bias

        self.doc._.phrases = self.calc_textrank()

        return self.doc._.phrases
