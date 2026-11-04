from .load_dataset import *
from collections import defaultdict
from ..files import FileConfig


def sampler_dataset(dataset, p=0.5):
    import random

    sampled_dataset = {"train": defaultdict(list), "valid": defaultdict(list), "test": defaultdict(list)}
    for k, v in dataset.items():
        keys = list(v.keys())
        for values in zip(*(v[kk] for kk in keys)):
            if random.random() < p:
                for kk, vv in zip(keys, values):
                    sampled_dataset[k][kk].append(vv)

    return sampled_dataset


def _unify_task(task):
    if task.lower() in [0, "cls", "classification", "classify"]:
        return "CLS"
    elif task.lower() in [1, "reg", "regression", "regressor", "sa", "sentitive analysis"]:
        return "REG"
    elif task.lower() in [2, "ner", "namely entity recognition"]:
        return "NER"
    elif task.lower() in [2, "key", "kw", "key word", "keyword", "keywords", "key words"]:
        return "KW"
    elif task.lower() in [3, "mcls", "multi-class", "multiclass", "multiclasses", "mc", "multi-choice", "multichoice"]:
        return "MCLS"
    elif task.lower() in [4, "cluener", "clue_ner", "clue ner"]:
        return "CLUENER"


def load_dataset(
    path,
    task=None,
    format=None,
    sampler=1,
    split=0.5,
    label_as_key=False,
    sep=" ",
    dataset="dataset",
    train="train",
    valid="valid",
    test="test",
    text="text",
    label="label",
):
    #     kwargs = {'task':task,'split':split,'sep':sep,'dataset':dataset,'train':train,'valid':valid,'test':test,'label':label}
    config = FileConfig()

    if path.lower() in config.datasets_names:
        info = config.datasets_info[config.datasets_names[path.lower()]]
        task = info["task"]
        format = info["format"]
        path = info["path"]

    task = _unify_task(task)

    if task == "CLUENER":
        format = "jsonL"

    if format is None:
        if path.split(".")[-1] == "json":
            try:
                datasets, config = LoadJson.load_dataset(
                    path, task, split, sep, dataset, train, valid, test, text, label
                )
            except:
                datasets, config = LoadJson2.load_dataset(
                    path, task, split, sep, dataset, train, valid, test, text, label
                )
        elif path.split(".")[-1] == "csv":
            datasets, config = LoadExcel.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
        else:
            try:
                datasets, config = LoadText.load_dataset(
                    path, task, split, sep, dataset, train, valid, test, text, label
                )
            except:
                datasets, config = LoadText2.load_dataset(
                    path, task, split, sep, dataset, train, valid, test, text, label
                )

    elif format == "json" and not label_as_key:
        datasets, config = LoadJson.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    elif format == "json2" or (format == "json" and label_as_key):
        datasets, config = LoadJson2.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    elif format == "jsonL":
        datasets, config = LoadJsonL.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    elif format == "text":
        datasets, config = LoadText.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    elif format == "text2":
        datasets, config = LoadText2.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    elif format == "excel":
        datasets, config = LoadExcel.load_dataset(path, task, split, sep, dataset, train, valid, test, text, label)
    else:
        raise NotImplemented

    if sampler and 0 < sampler < 1:
        datasets = sampler_dataset(datasets, sampler)

    return datasets, config
