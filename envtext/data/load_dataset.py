from collections import defaultdict, Counter
from ..utils.json_ops import read_json, read_jsonL
from ..utils.txt_ops import txt_generator
import random
import pandas as pd
import numpy as np
from .load_train_dataset import LoadDataset


class LoadJson(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        js = read_json(path)

        if not cls().has_split(js):
            new_js = {train: defaultdict(list), valid: defaultdict(list)}
            keys = list(js.keys())
            for values in zip(*(js[kk] for kk in keys)):
                if random.random() < split:
                    for k, v in zip(keys, values):
                        new_js[train][k].append(v)
                else:
                    for k, v in zip(keys, values):
                        new_js[valid][k].append(v)
            js = new_js

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, False)


class LoadJson2(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        js = read_json(path)

        if not cls().has_split(js):
            new_js = {"train": defaultdict(list), "valid": defaultdict(list)}
            for k, v in js.items():
                for vv in v:
                    if random.random() < split:
                        new_js["train"][k].append(vv)
                    else:
                        new_js["valid"][k].append(vv)
            js = new_js

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, True)


class LoadJsonL(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        flag = {"dataset": None}
        for idx, line in enumerate(read_jsonL(path)):
            if idx == 0:
                if dataset in line.keys():
                    flag["dataset"] = 1
                    js = {train: defaultdict(list), valid: defaultdict(list), test: defaultdict(list)}
                else:
                    flag["dataset"] = 0
                    js = {"train": defaultdict(list), "valid": defaultdict(list)}

            if flag["dataset"]:
                js[line[dataset]][text].append(line[text])
                js[line[dataset]][label].append(line[label])
            else:
                if random.random() < split:
                    js["train"][text].append(line[text])
                    js["train"][label].append(line[label])
                else:
                    js["valid"][text].append(line[text])
                    js["valid"][label].append(line[label])

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, False)


class LoadText(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        js = {"train": defaultdict(list), "valid": defaultdict(list), "test": defaultdict(list)}
        flag = {"format": 0, "dataset": None}
        for idx, line in enumerate(txt_generator(path)):
            words = line.split(sep)
            if idx == 0:
                if line in [train, valid, test]:
                    flag["format"] = 1
                elif len(words) == 3:
                    flag["format"] = 2
                elif len(words) == 2:
                    flag["format"] = 3
                else:
                    assert 0, "数据集一行中只允许2-3个片段，但是现在有{}个".format(len(words))

            if flag["format"] == 1:
                if line in [train, valid, test]:
                    flag["dataset"] = line
                    continue
                else:
                    assert len(words) == 2, "第一类数据集一行中只允许2个片段，但是第{}行有{}个".format(idx, len(words))
                    js[flag["dataset"]][text].append(words[0])
                    js[flag["dataset"]][label].append(words[1])
            elif flag["format"] == 2:
                assert len(words) == 3, "第二类数据集一行中只允许3个片段，但是第{}行有{}个".format(idx, len(words))
                js[words[2]][text].append(words[0])
                js[words[2]][label].append(words[1])
            elif flag["format"] == 3:
                assert len(words) == 2, "第三类数据集一行中只允许2个片段，但是第{}行有{}个".format(idx, len(words))
                if random.random() < split:
                    js["train"][text].append(words[0])
                    js["train"][label].append(words[1])
                else:
                    js["valid"][text].append(words[0])
                    js["valid"][label].append(words[1])

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, False)


class LoadText2(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        js = {"train": defaultdict(list), "valid": defaultdict(list), "test": defaultdict(list)}
        datasets = {"train": defaultdict(list), "valid": defaultdict(list), "test": defaultdict(list)}
        flag = {"format": 0, "dataset": None, "is_text": False, "text": ""}
        for idx, line in enumerate(txt_generator(path)):
            if idx == 0:
                if line in [train, valid, test]:
                    flag["format"] = 1
                    flag["is_text"] = False
                else:
                    flag["is_text"] = True

            if flag["format"] == 1:
                if line in [train, valid, test]:
                    flag["dataset"] = line
                    flag["is_text"] = False
                    continue
                elif flag["is_text"]:
                    js[flag["dataset"]][text].append(line)
                else:
                    js[flag["dataset"]][label].append(line)
            else:
                if flag["is_text"]:
                    flag["text"] = line
                else:
                    if random.random() < split:
                        js["train"][text].append(flag["text"])
                        js["train"][label].append(line)
                    else:
                        js["valid"][text].append(flag["text"])
                        js["valid"][label].append(line)

            flag["is_text"] = False if flag["is_text"] else True

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, False)


class LoadExcel(LoadDataset):
    @classmethod
    def load_dataset(
        cls,
        path,
        task,
        split=0.5,
        sep=" ",
        dataset="dataset",
        train="train",
        valid="valid",
        test="test",
        text="text",
        label="label",
    ):
        if isinstance(path, str):
            suffix = path.split(".")[-1]
            if suffix in ["xlsx", "xls"]:
                df = pd.read_excel(path)
            elif path.split(".")[-1] == "csv":
                df = pd.read_csv(path)
            else:
                assert 0, "数据集后缀应该是.csv或.xlsx或.xls，但是是{}".format(suffix)
        elif isinstance(path, pandas.core.frame.DataFrame):
            df = path
        else:
            assert 0, "path输入应该是字符串str或者pandas.core.frame.DataFrame，但是是{}".format(type(path))

        js = {train: defaultdict(list), valid: defaultdict(list), test: defaultdict(list)}
        datasets = {"train": defaultdict(list), "valid": defaultdict(list), "test": defaultdict(list)}
        mapping = {train: "train", valid: "valid", test: "test"}

        if dataset in df.columns:
            for index in df.index:
                if np.isnan(df.loc[index, label]):
                    js[test][text].append(df.loc[index, text])
                elif df.loc[index, dataset] == train:
                    js[train][text].append(df.loc[index, text])
                    js[train][label].append(df.loc[index, label])
                elif df.loc[index, dataset] == valid:
                    js[valid][text].append(df.loc[index, text])
                    js[valid][label].append(df.loc[index, label])
                elif df.loc[index, dataset] == test:
                    js[test][text].append(df.loc[index, text])
                    js[test][label].append(df.loc[index, label])
                else:
                    assert 0, "dataset一列下的元素只能是{},{},{}中的一个，但是现在是{}".format(
                        train, valid, test, df.loc[index, dataset]
                    )
        else:
            for index in df.index:
                if np.isnan(df.loc[index, label]):
                    js[test][text].append(df.loc[index, text])
                elif random.random() < split:
                    js[train][text].append(df.loc[index, text])
                    js[train][label].append(df.loc[index, label])
                else:
                    js[valid][text].append(df.loc[index, text])
                    js[valid][label].append(df.loc[index, label])

        return cls().generate_datasets(js, task, train, valid, test, text, label, sep, False)
