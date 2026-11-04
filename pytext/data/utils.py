import random
from contextlib import contextmanager
from copy import deepcopy


def get_tokenizer(tokenizer):
    if callable(tokenizer):
        return tokenizer
    if tokenizer == "spacy":
        try:
            import spacy

            spacy_en = spacy.load("en")
            return lambda s: [tok.text for tok in spacy_en.tokenizer(s)]
        except ImportError:
            print(
                "Please install SpaCy and the SpaCy English tokenizer. "
                "See the docs at https://spacy.io for more information."
            )
            raise
        except AttributeError:
            print(
                "Please install SpaCy and the SpaCy English tokenizer. "
                "See the docs at https://spacy.io for more information."
            )
            raise
    elif tokenizer == "moses":
        try:
            from sacremoses import MosesTokenizer

            moses_tokenizer = MosesTokenizer()
            return moses_tokenizer.tokenize
        except ImportError:
            print(
                "Please install SacreMoses. "
                "See the docs at https://github.com/alvations/sacremoses "
                "for more information."
            )
            raise
    elif tokenizer == "toktok":
        try:
            from nltk.tokenize.toktok import ToktokTokenizer

            toktok = ToktokTokenizer()
            return toktok.tokenize
        except ImportError:
            print("Please install NLTK. See the docs at https://nltk.org  for more information.")
            raise
    elif tokenizer == "revtok":
        try:
            import revtok

            return revtok.tokenize
        except ImportError:
            print("Please install revtok.")
            raise
    elif tokenizer == "subword":
        try:
            import revtok

            return lambda x: revtok.tokenize(x, decap=True)
        except ImportError:
            print("Please install revtok.")
            raise
    raise ValueError(
        "Requested tokenizer {}, valid choices are a "
        "callable that takes a single string as input, "
        '"revtok" for the revtok reversible tokenizer, '
        '"subword" for the revtok caps-aware tokenizer, '
        '"spacy" for the SpaCy English tokenizer, or '
        '"moses" for the NLTK port of the Moses tokenization '
        "script.".format(tokenizer)
    )


def interleave_keys(a, b):

    def interleave(args):
        return "".join([x for t in zip(*args) for x in t])

    return int("".join(interleave(format(x, "016b") for x in (a, b))), base=2)


def get_numpy_version():
    import numpy

    v = numpy.__version__
    version_substrings = v.split(".")
    major, minor = version_substrings[0], version_substrings[1]
    return int(major), int(minor)


class RandomShuffler(object):
    def __init__(self, random_state=None):
        self._random_state = random_state
        if self._random_state is None:
            self._random_state = random.getstate()

    @contextmanager
    def use_internal_state(self):
        old_state = random.getstate()
        random.setstate(self._random_state)
        yield
        self._random_state = random.getstate()
        random.setstate(old_state)

    @property
    def random_state(self):
        return deepcopy(self._random_state)

    @random_state.setter
    def random_state(self, s):
        self._random_state = s

    def __call__(self, data):
        with self.use_internal_state():
            return random.sample(data, len(data))


def typename(o):
    module = ""
    class_name = ""
    if (
        hasattr(o, "__module__")
        and o.__module__ != "builtins"
        and o.__module__ != "__builtin__"
        and o.__module__ is not None
    ):
        module = o.__module__ + "."

    if hasattr(o, "__qualname__"):
        class_name = o.__qualname__
    elif hasattr(o, "__name__"):
        class_name = o.__name__
    else:
        class_name = o.__class__.__name__

    return module + class_name
