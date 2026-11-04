from .. import data


class ShiftReduceField(data.Field):
    def __init__(self):

        super(ShiftReduceField, self).__init__(
            preprocessing=lambda parse: ["reduce" if t == ")" else "shift" for t in parse if t != "("]
        )

        self.build_vocab([["reduce"], ["shift"]])


class ParsedTextField(data.Field):
    def __init__(self, eos_token="<pad>", lower=False, reverse=False):
        if reverse:
            super(ParsedTextField, self).__init__(
                eos_token=eos_token,
                lower=lower,
                preprocessing=lambda parse: [t for t in parse if t not in ("(", ")")],
                postprocessing=lambda parse, _: [list(reversed(p)) for p in parse],
                include_lengths=True,
            )
        else:
            super(ParsedTextField, self).__init__(
                eos_token=eos_token,
                lower=lower,
                preprocessing=lambda parse: [t for t in parse if t not in ("(", ")")],
                include_lengths=True,
            )


class NLIDataset(data.TabularDataset):
    urls = []
    dirname = ""
    name = "nli"

    @staticmethod
    def sort_key(ex):
        return data.interleave_keys(len(ex.premise), len(ex.hypothesis))

    @classmethod
    def splits(
        cls,
        text_field,
        label_field,
        parse_field=None,
        extra_fields={},
        root=".data",
        train="train.jsonl",
        validation="val.jsonl",
        test="test.jsonl",
    ):
        path = cls.download(root)

        if parse_field is None:
            fields = {
                "sentence1": ("premise", text_field),
                "sentence2": ("hypothesis", text_field),
                "gold_label": ("label", label_field),
            }
        else:
            fields = {
                "sentence1_binary_parse": [("premise", text_field), ("premise_transitions", parse_field)],
                "sentence2_binary_parse": [("hypothesis", text_field), ("hypothesis_transitions", parse_field)],
                "gold_label": ("label", label_field),
            }

        for key in extra_fields:
            if key not in fields.keys():
                fields[key] = extra_fields[key]

        return super(NLIDataset, cls).splits(
            path, root, train, validation, test, format="json", fields=fields, filter_pred=lambda ex: ex.label != "-"
        )

    @classmethod
    def iters(cls, batch_size=32, device=0, root=".data", vectors=None, trees=False, **kwargs):
        if trees:
            TEXT = ParsedTextField()
            TRANSITIONS = ShiftReduceField()
        else:
            TEXT = data.Field(tokenize="spacy")
            TRANSITIONS = None
        LABEL = data.Field(sequential=False)

        train, val, test = cls.splits(TEXT, LABEL, TRANSITIONS, root=root, **kwargs)

        TEXT.build_vocab(train, vectors=vectors)
        LABEL.build_vocab(train)

        return data.BucketIterator.splits((train, val, test), batch_size=batch_size, device=device)


class SNLI(NLIDataset):
    urls = ["http://nlp.stanford.edu/projects/snli/snli_1.0.zip"]
    dirname = "snli_1.0"
    name = "snli"

    @classmethod
    def splits(
        cls,
        text_field,
        label_field,
        parse_field=None,
        root=".data",
        train="snli_1.0_train.jsonl",
        validation="snli_1.0_dev.jsonl",
        test="snli_1.0_test.jsonl",
    ):
        return super(SNLI, cls).splits(
            text_field, label_field, parse_field=parse_field, root=root, train=train, validation=validation, test=test
        )


class MultiNLI(NLIDataset):
    urls = ["http://www.nyu.edu/projects/bowman/multinli/multinli_1.0.zip"]
    dirname = "multinli_1.0"
    name = "multinli"

    @classmethod
    def splits(
        cls,
        text_field,
        label_field,
        parse_field=None,
        genre_field=None,
        root=".data",
        train="multinli_1.0_train.jsonl",
        validation="multinli_1.0_dev_matched.jsonl",
        test="multinli_1.0_dev_mismatched.jsonl",
    ):
        extra_fields = {}
        if genre_field is not None:
            extra_fields["genre"] = ("genre", genre_field)

        return super(MultiNLI, cls).splits(
            text_field,
            label_field,
            parse_field=parse_field,
            extra_fields=extra_fields,
            root=root,
            train=train,
            validation=validation,
            test=test,
        )


class XNLI(NLIDataset):
    urls = ["http://www.nyu.edu/projects/bowman/xnli/XNLI-1.0.zip"]
    dirname = "XNLI-1.0"
    name = "xnli"

    @classmethod
    def splits(
        cls,
        text_field,
        label_field,
        genre_field=None,
        language_field=None,
        root=".data",
        validation="xnli.dev.jsonl",
        test="xnli.test.jsonl",
    ):
        extra_fields = {}
        if genre_field is not None:
            extra_fields["genre"] = ("genre", genre_field)
        if language_field is not None:
            extra_fields["language"] = ("language", language_field)

        return super(XNLI, cls).splits(
            text_field, label_field, extra_fields=extra_fields, root=root, train=None, validation=validation, test=test
        )

    @classmethod
    def iters(cls, *args, **kwargs):
        raise NotImplementedError("XNLI dataset does not support iters")
