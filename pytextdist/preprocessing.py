from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import logging

logger = logging.getLogger(__name__)
from collections import Counter
from .input_validator import input_validator


def word_preprocessing(word, ignore_non_alnumspc=True, ignore_space=True, ignore_numeric=True, ignore_case=True):
    if ignore_non_alnumspc:
        word = "".join(filter(lambda x: x.isalnum() or x.isspace(), word))
    if ignore_space:
        word = "".join(filter(lambda x: not x.isspace(), word))
    if ignore_numeric:
        word = "".join(filter(lambda x: not x.isnumeric(), word))
    if ignore_case:
        word = word.lower()
    return word


def sentence_preprocessing(sentence, ignore_non_alnumspc=True, ignore_numeric=True, ignore_case=True):
    l_words = sentence.split()
    l_words = list(
        filter(
            lambda x: x != "",
            map(
                lambda x: word_preprocessing(
                    x,
                    ignore_non_alnumspc=ignore_non_alnumspc,
                    ignore_numeric=ignore_numeric,
                    ignore_case=ignore_case,
                    ignore_space=False,
                ),
                l_words,
            ),
        )
    )
    return l_words


def phrase_preprocessing(
    phrase, grain="char", ignore_non_alnumspc=True, ignore_space=True, ignore_numeric=True, ignore_case=True
):
    assert grain in ("char", "word"), "Illegal grain input: {}".format(grain)
    if grain == "char":
        return list(
            word_preprocessing(
                phrase,
                ignore_non_alnumspc=ignore_non_alnumspc,
                ignore_numeric=ignore_numeric,
                ignore_case=ignore_case,
                ignore_space=ignore_space,
            )
        )
    else:
        return sentence_preprocessing(
            phrase, ignore_non_alnumspc=ignore_non_alnumspc, ignore_numeric=ignore_numeric, ignore_case=ignore_case
        )


@input_validator(list, n=int)
def ngram_counter(list_of_token, n=2):
    if len(list_of_token) < n:
        raise Exception("Can't get {}-gram from input of length {}".format(n, len(list_of_token)))
    ngram_cnt = Counter([" ".join(list_of_token[index : index + n]) for index in range(len(list_of_token) - n + 1)])
    return ngram_cnt
