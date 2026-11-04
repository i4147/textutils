from .. import data
import random


class SequenceTaggingDataset(data.Dataset):
    @staticmethod
    def sort_key(example):
        for attr in dir(example):
            if not callable(getattr(example, attr)) and not attr.startswith("__"):
                return len(getattr(example, attr))
        return 0

    def __init__(self, path, fields, separator="\t", **kwargs):
        examples = []
        columns = []

        with open(path) as input_file:
            for line in input_file:
                line = line.strip()
                if line == "":
                    if columns:
                        examples.append(data.Example.fromlist(columns, fields))
                    columns = []
                else:
                    for i, column in enumerate(line.split(separator)):
                        if len(columns) < i + 1:
                            columns.append([])
                        columns[i].append(column)

            if columns:
                examples.append(data.Example.fromlist(columns, fields))
        super(SequenceTaggingDataset, self).__init__(examples, fields, **kwargs)


class UDPOS(SequenceTaggingDataset):
    urls = ["https://bitbucket.org/sivareddyg/public/downloads/en-ud-v2.zip"]
    dirname = "en-ud-v2"
    name = "udpos"

    @classmethod
    def splits(
        cls,
        fields,
        root=".data",
        train="en-ud-tag.v2.train.txt",
        validation="en-ud-tag.v2.dev.txt",
        test="en-ud-tag.v2.test.txt",
        **kwargs,
    ):

        return super(UDPOS, cls).splits(
            fields=fields, root=root, train=train, validation=validation, test=test, **kwargs
        )


class CoNLL2000Chunking(SequenceTaggingDataset):
    urls = [
        "https://www.clips.uantwerpen.be/conll2000/chunking/train.txt.gz",
        "https://www.clips.uantwerpen.be/conll2000/chunking/test.txt.gz",
    ]
    dirname = ""
    name = "conll2000"

    @classmethod
    def splits(cls, fields, root=".data", train="train.txt", test="test.txt", validation_frac=0.1, **kwargs):

        train, test = super(CoNLL2000Chunking, cls).splits(
            fields=fields, root=root, train=train, test=test, separator=" ", **kwargs
        )

        sort_key = train.sort_key

        random.seed(0)
        train, val = train.split(1 - validation_frac, random_state=random.getstate())
        random.seed()

        train.sort_key = sort_key
        val.sort_key = sort_key

        return train, val, test
