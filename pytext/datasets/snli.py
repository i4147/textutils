from .. import data


class ShiftReduceField(data.Field):
    def __init__(self):

        super(ShiftReduceField, self).__init__(
            preprocessing=lambda parse: ["reduce" if t == ")" else "shift" for t in parse if t != "("]
        )

        self.build_vocab([["reduce"], ["shift"]])


class ParsedTextField(data.Field):
    def __init__(self, eos_token="<pad>", lower=False):

        super(ParsedTextField, self).__init__(
            eos_token=eos_token,
            lower=lower,
            preprocessing=lambda parse: [t for t in parse if t not in ("(", ")")],
            postprocessing=lambda parse, _, __: [list(reversed(p)) for p in parse],
        )


class SNLI(data.TabularDataset):
    urls = ["http://nlp.stanford.edu/projects/snli/snli_1.0.zip"]
    dirname = "snli_1.0"
    name = "snli"

    @staticmethod
    def sort_key(ex):
        return data.interleave_keys(len(ex.premise), len(ex.hypothesis))

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
        path = cls.download(root)

        if parse_field is None:
            return super(SNLI, cls).splits(
                path,
                root,
                train,
                validation,
                test,
                format="json",
                fields={
                    "sentence1": ("premise", text_field),
                    "sentence2": ("hypothesis", text_field),
                    "gold_label": ("label", label_field),
                },
                filter_pred=lambda ex: ex.label != "-",
            )
        return super(SNLI, cls).splits(
            path,
            root,
            train,
            validation,
            test,
            format="json",
            fields={
                "sentence1_binary_parse": [("premise", text_field), ("premise_transitions", parse_field)],
                "sentence2_binary_parse": [("hypothesis", text_field), ("hypothesis_transitions", parse_field)],
                "gold_label": ("label", label_field),
            },
            filter_pred=lambda ex: ex.label != "-",
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
