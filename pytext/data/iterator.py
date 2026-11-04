from __future__ import division

import math
import random

import logging

from .utils import RandomShuffler
from .batch import Batch
from .dataset import Dataset

logger = logging.getLogger(__name__)


class Iterator(object):
    def __init__(
        self,
        dataset,
        batch_size,
        sort_key=None,
        device=None,
        batch_size_fn=None,
        train=True,
        repeat=None,
        shuffle=None,
        sort=None,
        sort_within_batch=None,
    ):
        self.batch_size, self.train, self.dataset = batch_size, train, dataset
        self.batch_size_fn = batch_size_fn
        self.iterations = 0
        self.repeat = train if repeat is None else repeat
        self.shuffle = train if shuffle is None else shuffle
        self.sort = not train if sort is None else sort

        if sort_within_batch is None:
            self.sort_within_batch = self.sort
        else:
            self.sort_within_batch = sort_within_batch
        if sort_key is None:
            self.sort_key = dataset.sort_key
        else:
            self.sort_key = sort_key

        if type(device) == int:
            logger.warning(
                "The `device` argument should be set by using `torch.device`"
                + " or passing a string as an argument. This behavior will be"
                + " deprecated soon and currently defaults to cpu."
            )
            device = None
        self.device = device
        self.random_shuffler = RandomShuffler()

        self._iterations_this_epoch = 0
        self._random_state_this_epoch = None
        self._restored_from_state = False

    @classmethod
    def splits(cls, datasets, batch_sizes=None, **kwargs):
        if batch_sizes is None:
            batch_sizes = [kwargs.pop("batch_size")] * len(datasets)
        ret = []
        for i in range(len(datasets)):
            train = i == 0
            ret.append(cls(datasets[i], batch_size=batch_sizes[i], train=train, **kwargs))
        return tuple(ret)

    def data(self):
        if self.sort:
            xs = sorted(self.dataset, key=self.sort_key)
        elif self.shuffle:
            xs = [self.dataset[i] for i in self.random_shuffler(range(len(self.dataset)))]
        else:
            xs = self.dataset
        return xs

    def init_epoch(self):

        if self._restored_from_state:
            self.random_shuffler.random_state = self._random_state_this_epoch
        else:
            self._random_state_this_epoch = self.random_shuffler.random_state

        self.create_batches()

        if self._restored_from_state:
            self._restored_from_state = False
        else:
            self._iterations_this_epoch = 0

        if not self.repeat:
            self.iterations = 0

    def create_batches(self):
        self.batches = batch(self.data(), self.batch_size, self.batch_size_fn)

    @property
    def epoch(self):
        return math.floor(self.iterations / len(self))

    def __len__(self):
        if self.batch_size_fn is not None:
            raise NotImplementedError
        return math.ceil(len(self.dataset) / self.batch_size)

    def __iter__(self):
        while True:
            self.init_epoch()
            for idx, minibatch in enumerate(self.batches):
                if self._iterations_this_epoch > idx:
                    continue
                self.iterations += 1
                self._iterations_this_epoch += 1
                if self.sort_within_batch:
                    if self.sort:
                        minibatch.reverse()
                    else:
                        minibatch.sort(key=self.sort_key, reverse=True)
                yield Batch(minibatch, self.dataset, self.device)
            if not self.repeat:
                return

    def state_dict(self):
        return {
            "iterations": self.iterations,
            "iterations_this_epoch": self._iterations_this_epoch,
            "random_state_this_epoch": self._random_state_this_epoch,
        }

    def load_state_dict(self, state_dict):
        self.iterations = state_dict["iterations"]
        self._iterations_this_epoch = state_dict["iterations_this_epoch"]
        self._random_state_this_epoch = state_dict["random_state_this_epoch"]
        self._restored_from_state = True


class BPTTIterator(Iterator):
    def __init__(self, dataset, batch_size, bptt_len, **kwargs):
        self.bptt_len = bptt_len
        super(BPTTIterator, self).__init__(dataset, batch_size, **kwargs)

    def __len__(self):
        return math.ceil((len(self.dataset[0].text) / self.batch_size - 1) / self.bptt_len)

    def __iter__(self):
        text = self.dataset[0].text
        TEXT = self.dataset.fields["text"]
        TEXT.eos_token = None
        text = text + ([TEXT.pad_token] * int(math.ceil(len(text) / self.batch_size) * self.batch_size - len(text)))
        data = TEXT.numericalize([text], device=self.device)
        data = data.view(self.batch_size, -1).t().contiguous()
        dataset = Dataset(examples=self.dataset.examples, fields=[("text", TEXT), ("target", TEXT)])
        while True:
            for i in range(0, len(self) * self.bptt_len, self.bptt_len):
                self.iterations += 1
                seq_len = min(self.bptt_len, len(data) - i - 1)
                yield Batch.fromvars(
                    dataset, self.batch_size, text=data[i : i + seq_len], target=data[i + 1 : i + 1 + seq_len]
                )
            if not self.repeat:
                return


class BucketIterator(Iterator):
    def create_batches(self):
        if self.sort:
            self.batches = batch(self.data(), self.batch_size, self.batch_size_fn)
        else:
            self.batches = pool(
                self.data(),
                self.batch_size,
                self.sort_key,
                self.batch_size_fn,
                random_shuffler=self.random_shuffler,
                shuffle=self.shuffle,
                sort_within_batch=self.sort_within_batch,
            )


def batch(data, batch_size, batch_size_fn=None):
    if batch_size_fn is None:

        def batch_size_fn(new, count, sofar):
            return count

    minibatch, size_so_far = [], 0
    for ex in data:
        minibatch.append(ex)
        size_so_far = batch_size_fn(ex, len(minibatch), size_so_far)
        if size_so_far == batch_size:
            yield minibatch
            minibatch, size_so_far = [], 0
        elif size_so_far > batch_size:
            yield minibatch[:-1]
            minibatch, size_so_far = minibatch[-1:], batch_size_fn(ex, 1, 0)
    if minibatch:
        yield minibatch


def pool(
    data,
    batch_size,
    key,
    batch_size_fn=lambda new, count, sofar: count,
    random_shuffler=None,
    shuffle=False,
    sort_within_batch=False,
):
    if random_shuffler is None:
        random_shuffler = random.shuffle
    for p in batch(data, batch_size * 100, batch_size_fn):
        p_batch = (
            batch(sorted(p, key=key), batch_size, batch_size_fn)
            if sort_within_batch
            else batch(p, batch_size, batch_size_fn)
        )
        if shuffle:
            for b in random_shuffler(list(p_batch)):
                yield b
        else:
            for b in list(p_batch):
                yield b
