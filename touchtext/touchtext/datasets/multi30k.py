import os, sys

curdir = os.path.dirname(os.path.abspath(__file__))

from typing import Union, Tuple

from ..data.datasets_utils import (
    _wrap_split_argument,
    _create_dataset_directory,
    DATASETS_CACHE_DIR,
)
from ..wget import download as wget_download

URL = {
    "train": {
        "en": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/train.en",
        "de": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/train.de",
    },
    "valid": {
        "en": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/valid.en",
        "de": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/valid.de",
    },
    "test": {
        "en": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/test.en",
        "de": r"https://github.com/hailiang-wang/touchtext/raw/main/data/Multi30k/test.de",
    },
}

_PREFIX = {
    "train": "train",
    "valid": "val",
    "test": "test",
}

NUM_LINES = {
    "train": 29000,
    "valid": 1014,
    "test": 1000,
}

DATASET_NAME = "Multi30k"
DATASET_CACHE_DIR = os.path.join(DATASETS_CACHE_DIR, DATASET_NAME)

print("touchtext>> DATASET_CACHE_DIR=%s" % DATASET_CACHE_DIR)


@_create_dataset_directory(dataset_name=DATASET_NAME)
@_wrap_split_argument(("train", "valid", "test"))
def Multi30k(root: str, split: Union[Tuple[str], str], language_pair: Tuple[str] = ("de", "en")):

    assert len(language_pair) == 2, "language_pair must contain only 2 elements: src and tgt language respectively"
    assert tuple(sorted(language_pair)) == (
        "de",
        "en",
    ), "language_pair must be either ('de','en') or ('en', 'de')"

    src_file_path = os.path.join(root, "%s.%s" % (split, language_pair[0]))
    tgt_file_path = os.path.join(root, "%s.%s" % (split, language_pair[1]))

    print("[touchtext] Multi30k load << root %s, split %s, file %s" % (root, split, src_file_path))
    print("[touchtext] Multi30k load << root %s, split %s, file %s" % (root, split, tgt_file_path))

    src_data_dp = []
    tgt_data_dp = []

    if not os.path.exists(src_file_path):
        wget_download(URL[split][language_pair[0]], src_file_path)

    if not os.path.exists(tgt_file_path):
        wget_download(URL[split][language_pair[1]], tgt_file_path)

    with open(src_file_path, "r", encoding="utf-8") as fin:
        for x in fin.readlines():
            src_data_dp.append(x.strip())

    with open(tgt_file_path, "r", encoding="utf-8") as fin:
        for x in fin.readlines():
            tgt_data_dp.append(x.strip())

    if len(src_data_dp) != len(tgt_data_dp):
        raise BaseException(
            "Multi30k data(%s) length not matched %d != %d" % (language_pair, len(src_data_dp), len(tgt_data_dp))
        )

    return list(zip(src_data_dp, tgt_data_dp))
