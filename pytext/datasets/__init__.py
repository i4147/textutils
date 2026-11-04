from .language_modeling import LanguageModelingDataset, WikiText2, PennTreebank
from .snli import SNLI
from .sst import SST
from .translation import TranslationDataset, Multi30k, IWSLT, WMT14
from .sequence_tagging import SequenceTaggingDataset, UDPOS, CoNLL2000Chunking
from .trec import TREC
from .imdb import IMDB
from .babi import BABI20


__all__ = [
    "LanguageModelingDataset",
    "SNLI",
    "SST",
    "TranslationDataset",
    "Multi30k",
    "IWSLT",
    "WMT14WikiText2",
    "PennTreeBank",
    "TREC",
    "IMDB",
    "SequenceTaggingDataset",
    "UDPOS",
    "CoNLL2000Chunking",
    "BABI20",
]
