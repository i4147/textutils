import os
import glob
import io

from .. import data


class IMDB(data.Dataset):
    urls = ["http://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz"]
    name = "imdb"
    dirname = "aclImdb"

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    def __init__(self, path, text_field, label_field, **kwargs):
        fields = [("text", text_field), ("label", label_field)]
        examples = []

        for label in ["pos", "neg"]:
            for fname in glob.iglob(os.path.join(path, label, "*.txt")):
                with io.open(fname, "r", encoding="utf-8") as f:
                    text = f.readline()
                examples.append(data.Example.fromlist([text, label], fields))

        super(IMDB, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, text_field, label_field, root=".data", train="train", test="test", **kwargs):
        return super(IMDB, cls).splits(
            root=root, text_field=text_field, label_field=label_field, train=train, validation=None, test=test, **kwargs
        )

    @classmethod
    def iters(cls, batch_size=32, device=0, root=".data", vectors=None, **kwargs):
        TEXT = data.Field()
        LABEL = data.Field(sequential=False)

        train, test = cls.splits(TEXT, LABEL, root=root, **kwargs)

        TEXT.build_vocab(train, vectors=vectors)
        LABEL.build_vocab(train)

        return data.BucketIterator.splits((train, test), batch_size=batch_size, device=device)
