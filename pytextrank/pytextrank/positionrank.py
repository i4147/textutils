# -*- coding: utf-8 -*-


import typing

from spacy.tokens import Doc

from .base import BaseTextRankFactory, BaseTextRank, Lemma
from .util import groupby_apply


class PositionRankFactory(BaseTextRankFactory):
    def __call__(
        self,
        doc: Doc,
    ) -> Doc:
        Doc.set_extension("textrank", force=True, default=None)
        Doc.set_extension("phrases", force=True, default=[])

        doc._.textrank = PositionRank(
            doc,
            edge_weight=self.edge_weight,
            pos_kept=self.pos_kept,
            token_lookback=self.token_lookback,
            scrubber=self.scrubber,
            stopwords=self.stopwords,
        )

        doc._.phrases = doc._.textrank.calc_textrank()
        return doc


class PositionRank(BaseTextRank):
    def get_personalization(self) -> typing.Optional[typing.Dict[Lemma, float]]:
        weighted_tokens: typing.List[typing.Tuple[str, float]] = [
            (tok, 1 / (i + 1))
            for i, tok in enumerate(token.lemma_ for token in self.doc if token.pos_ in self.pos_kept)
        ]

        keyfunc = lambda x: x[0]
        applyfunc = lambda g: sum(w for text, w in g)

        accumulated_weighted_tokens: typing.List[typing.Tuple[str, float]] = groupby_apply(
            weighted_tokens,
            keyfunc,
            applyfunc,
        )

        accumulated_weighted_tokens = sorted(accumulated_weighted_tokens, key=lambda x: x[1])

        norm_weighted_tokens = {
            k: w / sum(w_ for _, w_ in accumulated_weighted_tokens) for k, w in accumulated_weighted_tokens
        }

        weighted_nodes: typing.Dict[Lemma, float] = {
            Lemma(token.lemma_, token.pos_): norm_weighted_tokens[token.lemma_]
            for token in self.doc
            if token.pos_ in self.pos_kept
        }

        return weighted_nodes
