from .. import data
import io


class LanguageModelingDataset(data.Dataset):
    def __init__(self, path, text_field, newline_eos=True, encoding="utf-8", **kwargs):
        fields = [("text", text_field)]
        text = []
        with io.open(path, encoding=encoding) as f:
            for line in f:
                text += text_field.preprocess(line)
                if newline_eos:
                    text.append("<eos>")

        examples = [data.Example.fromlist([text], fields)]
        super(LanguageModelingDataset, self).__init__(examples, fields, **kwargs)


class WikiText2(LanguageModelingDataset):
    urls = ["https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-2-v1.zip"]
    name = "wikitext-2"
    dirname = "wikitext-2"

    @classmethod
    def splits(
        cls,
        text_field,
        root=".data",
        train="wiki.train.tokens",
        validation="wiki.valid.tokens",
        test="wiki.test.tokens",
        **kwargs,
    ):
        return super(WikiText2, cls).splits(
            root=root, train=train, validation=validation, test=test, text_field=text_field, **kwargs
        )

    @classmethod
    def iters(cls, batch_size=32, bptt_len=35, device=0, root=".data", vectors=None, **kwargs):
        TEXT = data.Field()

        train, val, test = cls.splits(TEXT, root=root, **kwargs)

        TEXT.build_vocab(train, vectors=vectors)

        return data.BPTTIterator.splits((train, val, test), batch_size=batch_size, bptt_len=bptt_len, device=device)


class WikiText103(LanguageModelingDataset):
    urls = ["https://s3.amazonaws.com/research.metamind.io/wikitext/wikitext-103-v1.zip"]
    name = "wikitext-103"
    dirname = "wikitext-103"

    @classmethod
    def splits(
        cls,
        text_field,
        root=".data",
        train="wiki.train.tokens",
        validation="wiki.valid.tokens",
        test="wiki.test.tokens",
        **kwargs,
    ):
        return super(WikiText103, cls).splits(
            root=root, train=train, validation=validation, test=test, text_field=text_field, **kwargs
        )

    @classmethod
    def iters(cls, batch_size=32, bptt_len=35, device=0, root=".data", vectors=None, **kwargs):
        TEXT = data.Field()

        train, val, test = cls.splits(TEXT, root=root, **kwargs)

        TEXT.build_vocab(train, vectors=vectors)

        return data.BPTTIterator.splits((train, val, test), batch_size=batch_size, bptt_len=bptt_len, device=device)


class PennTreebank(LanguageModelingDataset):
    urls = [
        "https://raw.githubusercontent.com/wojzaremba/lstm/master/data/ptb.train.txt",
        "https://raw.githubusercontent.com/wojzaremba/lstm/master/data/ptb.valid.txt",
        "https://raw.githubusercontent.com/wojzaremba/lstm/master/data/ptb.test.txt",
    ]
    name = "penn-treebank"
    dirname = ""

    @classmethod
    def splits(
        cls, text_field, root=".data", train="ptb.train.txt", validation="ptb.valid.txt", test="ptb.test.txt", **kwargs
    ):
        return super(PennTreebank, cls).splits(
            root=root, train=train, validation=validation, test=test, text_field=text_field, **kwargs
        )

    @classmethod
    def iters(cls, batch_size=32, bptt_len=35, device=0, root=".data", vectors=None, **kwargs):
        TEXT = data.Field()

        train, val, test = cls.splits(TEXT, root=root, **kwargs)

        TEXT.build_vocab(train, vectors=vectors)

        return data.BPTTIterator.splits((train, val, test), batch_size=batch_size, bptt_len=bptt_len, device=device)
