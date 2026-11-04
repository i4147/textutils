import io
import os
import zipfile
import tarfile
import gzip
import shutil
from functools import partial

# import torch.utils.data
from .datasetbase import Dataset as DatasetBase

from .utils import RandomShuffler
from .example import Example
from ..utils import download_from_url, unicode_csv_reader


class Dataset(DatasetBase):
    sort_key = None

    def __init__(self, examples, fields, filter_pred=None):
        if filter_pred is not None:
            make_list = isinstance(examples, list)
            examples = filter(filter_pred, examples)
            if make_list:
                examples = list(examples)
        self.examples = examples
        self.fields = dict(fields)
        for n, f in list(self.fields.items()):
            if isinstance(n, tuple):
                self.fields.update(zip(n, f))
                del self.fields[n]

    @classmethod
    def splits(cls, path=None, root=".data", train=None, validation=None, test=None, **kwargs):
        if path is None:
            path = cls.download(root)
        train_data = None if train is None else cls(os.path.join(path, train), **kwargs)
        val_data = None if validation is None else cls(os.path.join(path, validation), **kwargs)
        test_data = None if test is None else cls(os.path.join(path, test), **kwargs)
        return tuple(d for d in (train_data, val_data, test_data) if d is not None)

    def split(self, split_ratio=0.7, stratified=False, strata_field="label", random_state=None):
        train_ratio, test_ratio, val_ratio = check_split_ratio(split_ratio)

        rnd = RandomShuffler(random_state)
        if not stratified:
            train_data, test_data, val_data = rationed_split(self.examples, train_ratio, test_ratio, val_ratio, rnd)
        else:
            if strata_field not in self.fields:
                raise ValueError("Invalid field name for strata_field {}".format(strata_field))
            strata = stratify(self.examples, strata_field)
            train_data, test_data, val_data = [], [], []
            for group in strata:
                group_train, group_test, group_val = rationed_split(group, train_ratio, test_ratio, val_ratio, rnd)
                train_data += group_train
                test_data += group_test
                val_data += group_val

        splits = tuple(Dataset(d, self.fields) for d in (train_data, val_data, test_data) if d)

        if self.sort_key:
            for subset in splits:
                subset.sort_key = self.sort_key
        return splits

    def __getitem__(self, i):
        return self.examples[i]

    def __len__(self):
        try:
            return len(self.examples)
        except TypeError:
            return 2**32

    def __iter__(self):
        for x in self.examples:
            yield x

    def __getattr__(self, attr):
        if attr in self.fields:
            for x in self.examples:
                yield getattr(x, attr)

    @classmethod
    def download(cls, root, check=None):
        path = os.path.join(root, cls.name)
        check = path if check is None else check
        if not os.path.isdir(check):
            for url in cls.urls:
                if isinstance(url, tuple):
                    url, filename = url
                else:
                    filename = os.path.basename(url)
                zpath = os.path.join(path, filename)
                if not os.path.isfile(zpath):
                    if not os.path.exists(os.path.dirname(zpath)):
                        os.makedirs(os.path.dirname(zpath))
                    print("downloading {}".format(filename))
                    download_from_url(url, zpath)
                zroot, ext = os.path.splitext(zpath)
                _, ext_inner = os.path.splitext(zroot)
                if ext == ".zip":
                    with zipfile.ZipFile(zpath, "r") as zfile:
                        print("extracting")
                        zfile.extractall(path)
                elif ext == ".tgz" or ext == ".gz" and ext_inner == ".tar":
                    with tarfile.open(zpath, "r:gz") as tar:
                        dirs = [member for member in tar.getmembers()]
                        tar.extractall(path=path, members=dirs)
                elif ext == ".gz":
                    with gzip.open(zpath, "rb") as gz:
                        with open(zroot, "wb") as uncompressed:
                            shutil.copyfileobj(gz, uncompressed)

        return os.path.join(path, cls.dirname)


class TabularDataset(Dataset):
    def __init__(self, path, format, fields, skip_header=False, **kwargs):
        make_example = {
            "json": Example.fromJSON,
            "dict": Example.fromdict,
            "tsv": Example.fromCSV,
            "csv": Example.fromCSV,
        }[format.lower()]

        with io.open(os.path.expanduser(path), encoding="utf8") as f:
            if format == "csv":
                reader = unicode_csv_reader(f)
            elif format == "tsv":
                reader = unicode_csv_reader(f, delimiter="\t")
            else:
                reader = f

            if format in ["csv", "tsv"] and isinstance(fields, dict):
                if skip_header:
                    raise ValueError(
                        "When using a dict to specify fields with a {} file,"
                        "skip_header must be False and"
                        "the file must have a header.".format(format)
                    )
                header = next(reader)
                field_to_index = {f: header.index(f) for f in fields.keys()}
                make_example = partial(make_example, field_to_index=field_to_index)

            if skip_header:
                next(reader)

            examples = [make_example(line, fields) for line in reader]

        if isinstance(fields, dict):
            fields, field_dict = [], fields
            for field in field_dict.values():
                if isinstance(field, list):
                    fields.extend(field)
                else:
                    fields.append(field)

        super(TabularDataset, self).__init__(examples, fields, **kwargs)


def check_split_ratio(split_ratio):
    valid_ratio = 0.0
    if isinstance(split_ratio, float):
        assert split_ratio > 0.0 and split_ratio < 1.0, "Split ratio {} not between 0 and 1".format(split_ratio)

        test_ratio = 1.0 - split_ratio
        return (split_ratio, test_ratio, valid_ratio)
    elif isinstance(split_ratio, list):
        length = len(split_ratio)
        assert length == 2 or length == 3, "Length of split ratio list should be 2 or 3, got {}".format(split_ratio)

        ratio_sum = sum(split_ratio)
        if not ratio_sum == 1.0:
            split_ratio = [float(ratio) / ratio_sum for ratio in split_ratio]

        if length == 2:
            return tuple(split_ratio + [valid_ratio])
        return tuple(split_ratio)
    else:
        raise ValueError("Split ratio must be float or a list, got {}".format(type(split_ratio)))


def stratify(examples, strata_field):
    unique_strata = set(getattr(example, strata_field) for example in examples)
    strata_maps = {s: [] for s in unique_strata}
    for example in examples:
        strata_maps[getattr(example, strata_field)].append(example)
    return list(strata_maps.values())


def rationed_split(examples, train_ratio, test_ratio, val_ratio, rnd):
    N = len(examples)
    randperm = rnd(range(N))
    train_len = int(round(train_ratio * N))

    if not val_ratio:
        test_len = N - train_len
    else:
        test_len = int(round(test_ratio * N))

    indices = (randperm[:train_len], randperm[train_len : train_len + test_len], randperm[train_len + test_len :])

    data = tuple([examples[i] for i in index] for index in indices)

    return data
