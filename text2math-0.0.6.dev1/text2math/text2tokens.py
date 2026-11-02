__title__ = "text2math"
__author__ = "Steven Cutting"
__author_email__ = "steven.e.cutting@linux.com"
__created_on__ = "02/13/2016"
__copyright__ = "text2math Copyright (C) 2016  Steven Cutting"
from itertools import repeat, count
import json
import os
import re
import sys

try:
    import cytoolz as tlz
except ImportError:
    import toolz as tlz
filter_c = tlz.curry(tlz.filter)
map_c = tlz.curry(tlz.map)
sliding_window_c = tlz.curry(tlz.sliding_window)
if sys.version_info[0] < 3:
    from itertools import izip as zip
with open(os.path.join(os.path.dirname(__file__), "stopwords.json")) as fp:
    STOPWORDS = frozenset(json.load(fp))
PUNCTUATIONPAT = r"[\!\"\#\$\%\&\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~']+"
PUNCTUATIONPAT_SPLIT = r"[\!\"\#\$\%\&\(\)\*\+\,\-\.\/\:\;\<\=\>\?\@\[\\\]\^\_\`\{\|\}\~]+"
PUNCTUATIONPAT_DROP = r"[\']+"


@tlz.curry
def join_strings(glue, strings):
    return glue.join(strings)


def simple_split(string):
    return string.split()


@tlz.curry
def split_on_reg(regpattern, string):
    return (bit for bit in re.split(regpattern, string))


def splitter_of_words(string):
    non_alpha_num = r"""[,-/\#\$\%\(\)\*\+\<\=\>\@\[\\\]\^\`\{\|\}\~ :?&;!'"\n\t\r_]+"""
    return split_on_reg(non_alpha_num, string)


def lower(string):
    return string.lower()


@tlz.curry
def replace(new, old, string):
    return string.replace(old, new)


def replace_punct(string, replace="", pattern=PUNCTUATIONPAT):
    return re.subn(pattern, replace, string)[0]


def punct_to_space(string, pattern=PUNCTUATIONPAT_SPLIT):
    return replace_punct(string, replace=" ", pattern=pattern)


def drop_punct(string, pattern=PUNCTUATIONPAT_DROP):
    return replace_punct(string, replace="", pattern=pattern)


@tlz.curry
def merge_on(old, string):
    return replace(new="", old=old, string=string)


def filter_whitespace(tokenset):
    return tlz.filter(tlz.compose(bool, lambda string: string.strip()), tokenset)


@tlz.curry
def filter_shorter_than(n, tokenset):
    return tlz.filter(lambda tkn: len(tkn) >= n, tokenset)


@tlz.curry
def filter_longer_than(n, tokenset):
    return tlz.filter(lambda tkn: len(tkn) < n, tokenset)


not_stopword = lambda string: string not in STOPWORDS


def filter_stopwords(tokenset):
    return tlz.filter(not_stopword, tokenset)


@tlz.curry
def ngram_tuples(n, string, minlen=3, maxlen=25):
    return tlz.pipe(
        string,
        lower,
        simple_split,
        filter_longer_than(maxlen),
        tlz.compose(tlz.concat, map_c(splitter_of_words)),
        filter_shorter_than(minlen),
        filter_stopwords,
        sliding_window_c(n),
    )


@tlz.curry
def ngram(n, string, minlen=3, maxlen=25):
    try:
        return tlz.pipe(string, ngram_tuples(n, minlen=minlen, maxlen=maxlen), map_c(join_strings("_")))
    except StopIteration:
        return []


def unigram(string, **kwargs):
    return ngram(n=1, string=string, **kwargs)


def bigram(string, **kwargs):
    return ngram(n=2, string=string, **kwargs)


def trigram(string, **kwargs):
    return ngram(n=3, string=string, **kwargs)


def uni_and_bigram_tuples(string, minlen=3, maxlen=25):
    return tlz.pipe(
        string,
        lower,
        simple_split,
        filter_longer_than(maxlen),
        tlz.compose(tlz.concat, map_c(splitter_of_words)),
        filter_shorter_than(minlen),
        filter_stopwords,
        tuple,
        tlz.juxt(sliding_window_c(1), sliding_window_c(2)),
        tlz.interleave,
        map_c(join_strings("_")),
    )
