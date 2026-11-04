# coding: utf8
from collections import Counter, OrderedDict
from itertools import chain
import six

# import torch
import numpy
import pickle
from tqdm import tqdm

from .dataset import Dataset
from .pipeline import Pipeline
from .utils import get_tokenizer
from ..vocab import Vocab, SubwordVocab


class RawField(object):
    def __init__(self, preprocessing=None, postprocessing=None):
        self.preprocessing = preprocessing
        self.postprocessing = postprocessing

    def preprocess(self, x):
        if self.preprocessing is not None:
            return self.preprocessing(x)
        else:
            return x

    def process(self, batch, *args, **kwargs):
        if self.postprocessing is not None:
            batch = self.postprocessing(batch)
        return batch


class Field(RawField):
    vocab_cls = Vocab
    dtypes = {
        numpy.float32: float,
        numpy.float: float,
        numpy.float64: float,
        numpy.double: float,
        numpy.float16: float,
        numpy.half: float,
        numpy.uint8: int,
        numpy.int8: int,
        numpy.int16: int,
        numpy.short: int,
        numpy.int32: int,
        numpy.int: int,
        numpy.int64: int,
        numpy.long: int,
    }

    def __init__(
        self,
        sequential=True,
        use_vocab=True,
        init_token=None,
        eos_token=None,
        fix_length=None,
        dtype=numpy.long,
        preprocessing=None,
        postprocessing=None,
        lower=False,
        tokenize=(lambda s: s.split()),
        include_lengths=False,
        batch_first=False,
        pad_token="<pad>",
        unk_token="<unk>",
        pad_first=False,
        truncate_first=False,
    ):
        self.sequential = sequential
        self.use_vocab = use_vocab
        self.init_token = init_token
        self.eos_token = eos_token
        self.unk_token = unk_token
        self.fix_length = fix_length
        self.dtype = dtype
        self.preprocessing = preprocessing
        self.postprocessing = postprocessing
        self.lower = lower
        self.tokenize = get_tokenizer(tokenize)
        self.include_lengths = include_lengths
        self.batch_first = batch_first
        self.pad_token = pad_token if self.sequential else None
        self.pad_first = pad_first
        self.truncate_first = truncate_first

    def preprocess(self, x):
        if six.PY2 and isinstance(x, six.string_types) and not isinstance(x, six.text_type):
            x = Pipeline(lambda s: six.text_type(s, encoding="utf-8"))(x)
        if self.sequential and isinstance(x, six.text_type):
            x = self.tokenize(x.rstrip("\n"))
        if self.lower:
            x = Pipeline(six.text_type.lower)(x)
        if self.preprocessing is not None:
            return self.preprocessing(x)
        else:
            return x

    def process(self, batch, device=None):
        padded = self.pad(batch)
        tensor = self.numericalize(padded, device=device)
        return tensor

    def pad(self, minibatch):
        minibatch = list(minibatch)
        if not self.sequential:
            return minibatch
        if self.fix_length is None:
            max_len = max(len(x) for x in minibatch)
        else:
            max_len = self.fix_length + (self.init_token, self.eos_token).count(None) - 2
        padded, lengths = [], []
        for x in minibatch:
            if self.pad_first:
                padded.append(
                    [self.pad_token] * max(0, max_len - len(x))
                    + ([] if self.init_token is None else [self.init_token])
                    + list(x[-max_len:] if self.truncate_first else x[:max_len])
                    + ([] if self.eos_token is None else [self.eos_token])
                )
            else:
                padded.append(
                    ([] if self.init_token is None else [self.init_token])
                    + list(x[-max_len:] if self.truncate_first else x[:max_len])
                    + ([] if self.eos_token is None else [self.eos_token])
                    + [self.pad_token] * max(0, max_len - len(x))
                )
            lengths.append(len(padded[-1]) - max(0, max_len - len(x)))
        if self.include_lengths:
            return (padded, lengths)
        return padded

    def build_vocab(self, *args, **kwargs):
        counter = Counter()
        sources = []
        for arg in args:
            if isinstance(arg, Dataset):
                sources += [getattr(arg, name) for name, field in arg.fields.items() if field is self]
            else:
                sources.append(arg)
        for data in sources:
            for x in data:
                if not self.sequential:
                    x = [x]
                try:
                    counter.update(x)
                except TypeError:
                    counter.update(chain.from_iterable(x))
        specials = list(
            OrderedDict.fromkeys(
                tok for tok in [self.unk_token, self.pad_token, self.init_token, self.eos_token] if tok is not None
            )
        )
        self.vocab = self.vocab_cls(counter, specials=specials, **kwargs)

    def numericalize(self, arr, device=None):
        if self.include_lengths and not isinstance(arr, tuple):
            raise ValueError(
                "Field has include_lengths set to True, but input data is not a tuple of (data batch, batch lengths)."
            )
        if isinstance(arr, tuple):
            arr, lengths = arr
            lengths = torch.tensor(lengths, dtype=self.dtype)

        if self.use_vocab:
            if self.sequential:
                arr = [[self.vocab.stoi[x] for x in ex] for ex in arr]
            else:
                arr = [self.vocab.stoi[x] for x in arr]

            if self.postprocessing is not None:
                arr = self.postprocessing(arr, self.vocab)
        else:
            if self.dtype not in self.dtypes:
                raise ValueError(
                    "Specified Field dtype {} can not be used with "
                    "use_vocab=False because we do not know how to numericalize it. "
                    "Please raise an issue at "
                    "https://github.com/pytorch/text/issues".format(self.dtype)
                )
            numericalization_func = self.dtypes[self.dtype]
            if not self.sequential:
                arr = [numericalization_func(x) if isinstance(x, six.string_types) else x for x in arr]
            if self.postprocessing is not None:
                arr = self.postprocessing(arr, None)

        var = numpy.array(arr, dtype=self.dtype)

        if self.sequential and not self.batch_first:
            var = numpy.transpose(var)
        # if self.sequential:
        # var = var.contiguous()

        if self.include_lengths:
            return var, lengths
        return var


class ReversibleField(Field):
    def __init__(self, **kwargs):
        if kwargs.get("tokenize") is list:
            self.use_revtok = False
        else:
            self.use_revtok = True
        if kwargs.get("tokenize") is None:
            kwargs["tokenize"] = "revtok"
        if "unk_token" not in kwargs:
            kwargs["unk_token"] = " UNK "
        super(ReversibleField, self).__init__(**kwargs)

    def reverse(self, batch):
        if self.use_revtok:
            try:
                import revtok
            except ImportError:
                print("Please install revtok.")
                raise
        if not self.batch_first:
            batch = numpy.transpose(batch)
        # with torch.cuda.device_of(batch):
        batch = batch.tolist()
        batch = [[self.vocab.itos[ind] for ind in ex] for ex in batch]

        def trim(s, t):
            sentence = []
            for w in s:
                if w == t:
                    break
                sentence.append(w)
            return sentence

        batch = [trim(ex, self.eos_token) for ex in batch]

        def filter_special(tok):
            return tok not in (self.init_token, self.pad_token)

        batch = [filter(filter_special, ex) for ex in batch]
        if self.use_revtok:
            return [revtok.detokenize(ex) for ex in batch]
        return ["".join(ex) for ex in batch]


class SubwordField(ReversibleField):
    vocab_cls = SubwordVocab

    def __init__(self, **kwargs):
        kwargs["tokenize"] = "subword"
        if "unk_token" not in kwargs:
            kwargs["unk_token"] = "�"
        super(SubwordField, self).__init__(**kwargs)

    def segment(self, *args):
        sources = []
        for arg in args:
            if isinstance(arg, Dataset):
                sources += [getattr(arg, name) for name, field in arg.fields.items() if field is self]
            else:
                sources.append(arg)
        for data in sources:
            for x in tqdm(data, "segmenting"):
                x[:] = self.vocab.segment(x)


class NestedField(Field):
    def __init__(
        self,
        nesting_field,
        use_vocab=True,
        init_token=None,
        eos_token=None,
        fix_length=None,
        dtype=numpy.long,
        preprocessing=None,
        postprocessing=None,
        tokenize=lambda s: s.split(),
        include_lengths=False,
        pad_token="<pad>",
        pad_first=False,
        truncate_first=False,
    ):
        if isinstance(nesting_field, NestedField):
            raise ValueError("nesting field must not be another NestedField")
        if nesting_field.include_lengths:
            raise ValueError("nesting field cannot have include_lengths=True")

        if nesting_field.sequential:
            pad_token = nesting_field.pad_token
        super(NestedField, self).__init__(
            use_vocab=use_vocab,
            init_token=init_token,
            eos_token=eos_token,
            fix_length=fix_length,
            dtype=dtype,
            preprocessing=preprocessing,
            postprocessing=postprocessing,
            lower=nesting_field.lower,
            tokenize=tokenize,
            batch_first=True,
            pad_token=pad_token,
            unk_token=nesting_field.unk_token,
            pad_first=pad_first,
            truncate_first=truncate_first,
            include_lengths=include_lengths,
        )
        self.nesting_field = nesting_field
        self.nesting_field.batch_first = True

    def preprocess(self, xs):
        return [self.nesting_field.preprocess(x) for x in super(NestedField, self).preprocess(xs)]

    def pad(self, minibatch):
        minibatch = list(minibatch)
        if not self.nesting_field.sequential:
            return super(NestedField, self).pad(minibatch)

        old_pad_token = self.pad_token
        old_init_token = self.init_token
        old_eos_token = self.eos_token
        old_fix_len = self.nesting_field.fix_length
        if self.nesting_field.fix_length is None:
            max_len = max(len(xs) for ex in minibatch for xs in ex)
            fix_len = max_len + 2 - (self.nesting_field.init_token, self.nesting_field.eos_token).count(None)
            self.nesting_field.fix_length = fix_len
        self.pad_token = [self.pad_token] * self.nesting_field.fix_length
        if self.init_token is not None:
            # self.init_token = self.nesting_field.pad([[self.init_token]])[0]
            self.init_token = [self.init_token]
        if self.eos_token is not None:
            # self.eos_token = self.nesting_field.pad([[self.eos_token]])[0]
            self.eos_token = [self.eos_token]
        old_include_lengths = self.include_lengths
        self.include_lengths = True
        self.nesting_field.include_lengths = True
        padded, sentence_lengths = super(NestedField, self).pad(minibatch)
        padded_with_lengths = [self.nesting_field.pad(ex) for ex in padded]
        word_lengths = []
        final_padded = []
        max_sen_len = len(padded[0])
        for (pad, lens), sentence_len in zip(padded_with_lengths, sentence_lengths):
            if sentence_len == max_sen_len:
                lens = lens
                pad = pad
            elif self.pad_first:
                lens[: (max_sen_len - sentence_len)] = [0] * (max_sen_len - sentence_len)
                pad[: (max_sen_len - sentence_len)] = [self.pad_token] * (max_sen_len - sentence_len)
            else:
                lens[-(max_sen_len - sentence_len) :] = [0] * (max_sen_len - sentence_len)
                pad[-(max_sen_len - sentence_len) :] = [self.pad_token] * (max_sen_len - sentence_len)
            word_lengths.append(lens)
            final_padded.append(pad)
        padded = final_padded

        self.nesting_field.fix_length = old_fix_len
        self.pad_token = old_pad_token
        self.init_token = old_init_token
        self.eos_token = old_eos_token
        self.include_lengths = old_include_lengths
        if self.include_lengths:
            return padded, sentence_lengths, word_lengths
        return padded

    def build_vocab(self, *args, **kwargs):
        sources = []
        for arg in args:
            if isinstance(arg, Dataset):
                sources.extend([getattr(arg, name) for name, field in arg.fields.items() if field is self])
            else:
                sources.append(arg)

        flattened = []
        for source in sources:
            flattened.extend(source)
        old_vectors = None
        old_unk_init = None
        old_vectors_cache = None
        if "vectors" in kwargs.keys():
            old_vectors = kwargs["vectors"]
            kwargs["vectors"] = None
        if "unk_init" in kwargs.keys():
            old_unk_init = kwargs["unk_init"]
            kwargs["unk_init"] = None
        if "vectors_cache" in kwargs.keys():
            old_vectors_cache = kwargs["vectors_cache"]
            kwargs["vectors_cache"] = None
        self.nesting_field.build_vocab(*flattened, **kwargs)
        super(NestedField, self).build_vocab()
        self.vocab.extend(self.nesting_field.vocab)
        if old_vectors is not None:
            self.vocab.load_vectors(old_vectors, unk_init=old_unk_init, cache=old_vectors_cache)

        self.nesting_field.vocab = self.vocab

    def numericalize(self, arrs, device=None):
        numericalized = []
        self.nesting_field.include_lengths = False
        if self.include_lengths:
            arrs, sentence_lengths, word_lengths = arrs

        for arr in arrs:
            numericalized_ex = self.nesting_field.numericalize(arr, device=device)
            numericalized.append(numericalized_ex)
        padded_batch = numpy.stack(numericalized)

        self.nesting_field.include_lengths = True
        if self.include_lengths:
            sentence_lengths = numpy.ndarray(sentence_lengths, dtype=numpy.long)
            word_lengths = numpy.ndarray(word_lengths, dtype=numpy.long)
            return (padded_batch, sentence_lengths, word_lengths)
        return padded_batch


class LabelField(Field):
    def __init__(self, **kwargs):
        kwargs["sequential"] = False
        kwargs["unk_token"] = None

        super(LabelField, self).__init__(**kwargs)
