from collections import Counter, OrderedDict
from typing import Dict, Iterable, List, Optional

from .vocab import Vocab


def vocab(
    ordered_dict: Dict, min_freq: int = 1, specials: Optional[List[str]] = None, special_first: bool = True
) -> Vocab:
    specials = specials or []
    for token in specials:
        ordered_dict.pop(token, None)

    tokens = []
    for token, freq in ordered_dict.items():
        if freq >= min_freq:
            tokens.append(token)

    if special_first:
        tokens[0:0] = specials
    else:
        tokens.extend(specials)

    return Vocab(tokens)


def build_vocab_from_iterator(
    iterator: Iterable,
    min_freq: int = 1,
    specials: Optional[List[str]] = None,
    special_first: bool = True,
    max_tokens: Optional[int] = None,
) -> Vocab:

    counter = Counter()
    for tokens in iterator:
        counter.update(tokens)

    specials = specials or []

    sorted_by_freq_tuples = sorted(counter.items(), key=lambda x: (-x[1], x[0]))

    if max_tokens is None:
        ordered_dict = OrderedDict(sorted_by_freq_tuples)
    else:
        assert len(specials) < max_tokens, "len(specials) >= max_tokens, so the vocab will be entirely special tokens."
        ordered_dict = OrderedDict(sorted_by_freq_tuples[: max_tokens - len(specials)])

    word_vocab = vocab(ordered_dict, min_freq=min_freq, specials=specials, special_first=special_first)
    return word_vocab
