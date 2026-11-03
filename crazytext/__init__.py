import re
from crazytext import utils

__version__ = "1.0.4"
from crazytext.utils import Counter
from crazytext.utils import Extractor
from crazytext.utils import Cleaner
from crazytext.utils import Dataframe


def to_cv(x, max_features):
    return utils._to_cv(x, max_features)


def to_tfid(x, max_features):
    return utils._to_tfidf(x, max_features)
