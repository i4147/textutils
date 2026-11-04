import io
import re

import torch

__all__ = [
    "sentencepiece_numericalizer",
    "sentencepiece_tokenizer",
    "numericalize_tokens_from_iterator",
    "filter_wikipedia_xml",
    "to_map_style_dataset",
]


"""
This file contains experimental functionality.
All of these are experimental, unstable, and subject to change or deletion.
"""


def sentencepiece_numericalizer(sp_model):

    def _internal_func(txt_iter):
        for line in txt_iter:
            yield sp_model.EncodeAsIds(line)

    return _internal_func


def sentencepiece_tokenizer(sp_model):

    def _internal_func(txt_iter):
        for line in txt_iter:
            yield sp_model.EncodeAsPieces(line)

    return _internal_func


def custom_replace(replace_pattern):

    _patterns = list((re.compile(p), r) for (p, r) in replace_pattern)

    def _internal_func(txt_iter):
        for line in txt_iter:
            for pattern_re, replaced_str in _patterns:
                line = pattern_re.sub(replaced_str, line)
            yield line

    return _internal_func


def simple_space_split(iterator):

    for line in iterator:
        yield line.split()


def numericalize_tokens_from_iterator(vocab, iterator, removed_tokens=None):
    for tokens in iterator:
        if removed_tokens is None:
            yield iter(vocab[token] for token in tokens)
        else:
            yield iter(map(lambda x: vocab[x], filter(lambda x: x not in removed_tokens, tokens)))


_patterns = [
    (r"<.*>", ""),
    (r"&amp;", "&"),
    (r"&lt;", "<"),
    (r"&gt;", ">"),
    (r"<ref[^<]*<\/ref>", ""),
    (r"<[^>]*>", ""),
    (r"\[http:[^] ]*", "["),
    (r"\|thumb", ""),
    (r"\|left", ""),
    (r"\|right", ""),
    (r"\|\d+px", ""),
    (r"\[\[image:[^\[\]]*\|", ""),
    (r"\[\[category:([^|\]]*)[^]]*\]\]", "[[$1]]"),
    (r"\[\[[a-z\-]*:[^\]]*\]\]", ""),
    (r"\[\[[^\|\]]*\|", "[["),
    (r"\{\{[^\}]*\}\}", ""),
    (r"\{[^\}]*\}", ""),
    (r"\[", ""),
    (r"\]", ""),
    (r"&[^;]*;", " "),
    (r"A", "a"),
    (r"B", "b"),
    (r"C", "c"),
    (r"D", "d"),
    (r"E", "e"),
    (r"F", "f"),
    (r"G", "g"),
    (r"H", "h"),
    (r"I", "i"),
    (r"J", "j"),
    (r"K", "k"),
    (r"L", "l"),
    (r"M", "m"),
    (r"N", "n"),
    (r"O", "o"),
    (r"P", "p"),
    (r"Q", "q"),
    (r"R", "r"),
    (r"S", "s"),
    (r"T", "t"),
    (r"U", "u"),
    (r"V", "v"),
    (r"W", "w"),
    (r"X", "x"),
    (r"Y", "y"),
    (r"Z", "z"),
    (r"0", " zero "),
    (r"1", " one "),
    (r"2", " two "),
    (r"3", " three "),
    (r"4", " four "),
    (r"5", " five "),
    (r"6", " six "),
    (r"7", " seven "),
    (r"8", " eight "),
    (r"9", " nine "),
    (r"[^a-z\n]+", " "),
    (r"\n ", ""),
    (r"\s+", " "),
    (r"\n\s*\n", r"\n"),
]


def filter_wikipedia_xml(text_iterator):

    try:
        iter(text_iterator)
    except:
        raise TypeError("Input {} must support iterator semantics".format(text_iterator))

    norm_transform = custom_replace(_patterns)
    for line in text_iterator:
        if "#redirect" in line or "#REDIRECT" in line:
            continue
        line = list(norm_transform([line]))[0].strip()
        if line:
            yield line


def to_map_style_dataset(iter_data):

    class _MapStyleDataset(torch.utils.data.Dataset):
        def __init__(self, iter_data) -> None:
            self._data = list(iter_data)

        def __len__(self):
            return len(self._data)

        def __getitem__(self, idx):
            return self._data[idx]

    return _MapStyleDataset(iter_data)
