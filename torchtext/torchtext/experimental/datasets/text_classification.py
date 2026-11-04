import logging
import torch
import io
from torchtext.utils import download_from_url, extract_archive
from torchtext.data.utils import ngrams_iterator
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator
from torchtext.vocab import Vocab
from torchtext.datasets import TextClassificationDataset

URLS = {"IMDB": "http://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"}


def _create_data_from_iterator(vocab, iterator, removed_tokens):
    for cls, tokens in iterator:
        yield cls, iter(map(lambda x: vocab[x], filter(lambda x: x not in removed_tokens, tokens)))


def _imdb_iterator(key, extracted_files, tokenizer, ngrams, yield_cls=False):
    for fname in extracted_files:
        if "urls" in fname:
            continue
        elif key in fname and ("pos" in fname or "neg" in fname):
            with io.open(fname, encoding="utf8") as f:
                label = 1 if "pos" in fname else 0
                if yield_cls:
                    yield label, ngrams_iterator(tokenizer(f.read()), ngrams)
                else:
                    yield ngrams_iterator(tokenizer(f.read()), ngrams)


def _generate_data_iterators(dataset_name, root, ngrams, tokenizer, data_select):
    if not tokenizer:
        tokenizer = get_tokenizer("basic_english")

    if not set(data_select).issubset(set(("train", "test"))):
        raise TypeError("Given data selection {} is not supported!".format(data_select))

    dataset_tar = download_from_url(URLS[dataset_name], root=root)
    extracted_files = extract_archive(dataset_tar)

    iters_group = {}
    if "train" in data_select:
        iters_group["vocab"] = _imdb_iterator("train", extracted_files, tokenizer, ngrams)
    for item in data_select:
        iters_group[item] = _imdb_iterator(item, extracted_files, tokenizer, ngrams, yield_cls=True)
    return iters_group


def _setup_datasets(
    dataset_name, root=".data", ngrams=1, vocab=None, removed_tokens=[], tokenizer=None, data_select=("train", "test")
):

    if isinstance(data_select, str):
        data_select = [data_select]

    iters_group = _generate_data_iterators(dataset_name, root, ngrams, tokenizer, data_select)

    if vocab is None:
        if "vocab" not in iters_group.keys():
            raise TypeError("Must pass a vocab if train is not selected.")
        logging.info("Building Vocab based on train data")
        vocab = build_vocab_from_iterator(iters_group["vocab"])
    else:
        if not isinstance(vocab, Vocab):
            raise TypeError("Passed vocabulary is not of type Vocab")
    logging.info("Vocab has {} entries".format(len(vocab)))

    data = {}
    for item in data_select:
        data[item] = {}
        data[item]["data"] = []
        data[item]["labels"] = []
        logging.info("Creating {} data".format(item))
        data_iter = _create_data_from_iterator(vocab, iters_group[item], removed_tokens)
        for cls, tokens in data_iter:
            data[item]["data"].append((torch.tensor(cls), torch.tensor([token_id for token_id in tokens])))
            data[item]["labels"].append(cls)
        data[item]["labels"] = set(data[item]["labels"])

    return tuple(TextClassificationDataset(vocab, data[item]["data"], data[item]["labels"]) for item in data_select)


def IMDB(*args, **kwargs):

    return _setup_datasets(*(("IMDB",) + args), **kwargs)


DATASETS = {"IMDB": IMDB}


LABELS = {"IMDB": {0: "Negative", 1: "Positive"}}
