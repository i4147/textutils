# -*- coding: utf-8 -*-

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))

import nltk
import re
import string
from itertools import chain
from abc import ABCMeta, abstractmethod
from jgtextrank.decorators import requires_nltk_corpus

PUNCTUATION_REGEX = re.compile("[{0}]".format(re.escape(string.punctuation)))

from nltk import pos_tag

__author__ = "Jie Gao <j.gao@sheffield.ac.uk>"

# from nltk.data import load
# _POS_TAGGER = 'taggers/maxent_treebank_pos_tagger/english.pickle'
# tagger = load(_POS_TAGGER)


def pos_tagging():

    return pos_tag


def strip_punc(s, all=False):
    if all:
        return PUNCTUATION_REGEX.sub("", s.strip())
    else:
        return s.strip().strip(string.punctuation)


def with_metaclass(meta, *bases):

    class metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return metaclass("temporary_class", None, {})


class BaseTokenizer(with_metaclass(ABCMeta), nltk.tokenize.api.TokenizerI):
    @abstractmethod
    def tokenize(self, text):
        return

    def itokenize(self, text, *args, **kwargs):
        return (t for t in self.tokenize(text, *args, **kwargs))


class WordTokenizer(BaseTokenizer):
    def tokenize(self, text, include_punc=True):
        tokens = nltk.tokenize.word_tokenize(text)
        if include_punc:
            return tokens
        else:
            return [
                word if word.startswith("'") else strip_punc(word, all=False)
                for word in tokens
                if strip_punc(word, all=False)
            ]


class SentenceTokenizer(BaseTokenizer):
    @requires_nltk_corpus
    def tokenize(self, text):
        return nltk.tokenize.sent_tokenize(text)


sent_tokenize = SentenceTokenizer().itokenize

_word_tokenizer = WordTokenizer()


def word_tokenize(text, include_punc=True, *args, **kwargs):
    words = chain.from_iterable(
        _word_tokenizer.itokenize(sentence, include_punc=include_punc, *args, **kwargs)
        for sentence in sent_tokenize(text)
    )
    return words


def word_2_tokenised_sentences(text, include_punc=True, *args, **kwargs):
    sentences = sent_tokenize(text)
    for sentence in sentences:
        yield _word_tokenizer.itokenize(sentence, include_punc=include_punc, *args, **kwargs)


if __name__ == "__main__":
    tokenised_text = [
        "Compatibility",
        "of",
        "systems",
        "of",
        "linear",
        "constraints",
        "over",
        "the",
        "set",
        "of",
        "natural",
        "numbers",
        ".",
        "Criteria",
        "of",
        "compatibility",
        "of",
        "a",
        "system",
        "of",
        "linear",
        "Diophantine",
        "equations",
        ",",
        "strict",
        "inequations",
        ",",
        "and",
        "nonstrict",
        "inequations",
        "are",
        "considered",
        ".",
        "Upper",
        "bounds",
        "for",
        "components",
        "of",
        "a",
        "minimal",
        "set",
        "of",
        "solutions",
        "and",
        "algorithms",
        "of",
        "construction",
        "of",
        "minimal",
        "generating",
        "sets",
        "of",
        "solutions",
        "for",
        "all",
        "types",
        "of",
        "systems",
        "are",
        "given",
        ".",
        "These",
        "criteria",
        "and",
        "the",
        "corresponding",
        "algorithms",
        "for",
        "constructing",
        "a",
        "minimal",
        "supporting",
        "set",
        "of",
        "solutions",
        "can",
        "be",
        "used",
        "in",
        "solving",
        "all",
        "the",
        "considered",
        "types",
        "systems",
        "and",
        "systems",
        "of",
        "mixed",
        "types",
        ".",
    ]
    print(sent_tokenize(tokenised_text))
