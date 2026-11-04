import os

from .. import data


class TREC(data.Dataset):
    urls = ["http://cogcomp.org/Data/QA/QC/train_5500.label", "http://cogcomp.org/Data/QA/QC/TREC_10.label"]
    name = "trec"
    dirname = ""

    @staticmethod
    def sort_key(ex):
        return len(ex.text)

    def __init__(self, path, text_field, label_field, fine_grained=False, **kwargs):
        fields = [("text", text_field), ("label", label_field)]
        examples = []

        def get_label_str(label):
            return label.split(":")[0] if not fine_grained else label

        label_field.preprocessing = data.Pipeline(get_label_str)

        for line in open(os.path.expanduser(path), "rb"):
            label, _, text = line.replace(b"\xf0", b" ").decode().partition(" ")
            examples.append(data.Example.fromlist([text, label], fields))

        super(TREC, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, text_field, label_field, root=".data", train="train_5500.label", test="TREC_10.label", **kwargs):
        return super(TREC, cls).splits(
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
