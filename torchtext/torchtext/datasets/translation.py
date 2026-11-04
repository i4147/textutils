import os
import xml.etree.ElementTree as ET
import glob
import io
import codecs

from .. import data


class TranslationDataset(data.Dataset):
    @staticmethod
    def sort_key(ex):
        return data.interleave_keys(len(ex.src), len(ex.trg))

    def __init__(self, path, exts, fields, **kwargs):
        if not isinstance(fields[0], (tuple, list)):
            fields = [("src", fields[0]), ("trg", fields[1])]

        src_path, trg_path = tuple(os.path.expanduser(path + x) for x in exts)

        examples = []
        with (
            io.open(src_path, mode="r", encoding="utf-8") as src_file,
            io.open(trg_path, mode="r", encoding="utf-8") as trg_file,
        ):
            for src_line, trg_line in zip(src_file, trg_file):
                src_line, trg_line = src_line.strip(), trg_line.strip()
                if src_line != "" and trg_line != "":
                    examples.append(data.Example.fromlist([src_line, trg_line], fields))

        super(TranslationDataset, self).__init__(examples, fields, **kwargs)

    @classmethod
    def splits(cls, exts, fields, path=None, root=".data", train="train", validation="val", test="test", **kwargs):
        if path is None:
            path = cls.download(root)

        train_data = None if train is None else cls(os.path.join(path, train), exts, fields, **kwargs)
        val_data = None if validation is None else cls(os.path.join(path, validation), exts, fields, **kwargs)
        test_data = None if test is None else cls(os.path.join(path, test), exts, fields, **kwargs)
        return tuple(d for d in (train_data, val_data, test_data) if d is not None)


class Multi30k(TranslationDataset):
    urls = [
        "http://www.quest.dcs.shef.ac.uk/wmt16_files_mmt/training.tar.gz",
        "http://www.quest.dcs.shef.ac.uk/wmt16_files_mmt/validation.tar.gz",
        "http://www.quest.dcs.shef.ac.uk/wmt17_files_mmt/mmt_task1_test2016.tar.gz",
    ]
    name = "multi30k"
    dirname = ""

    @classmethod
    def splits(cls, exts, fields, root=".data", train="train", validation="val", test="test2016", **kwargs):

        if "path" not in kwargs:
            expected_folder = os.path.join(root, cls.name)
            path = expected_folder if os.path.exists(expected_folder) else None
        else:
            path = kwargs["path"]
            del kwargs["path"]

        return super(Multi30k, cls).splits(exts, fields, path, root, train, validation, test, **kwargs)


class IWSLT(TranslationDataset):
    base_url = "https://wit3.fbk.eu/archive/2016-01//texts/{}/{}/{}.tgz"
    name = "iwslt"
    base_dirname = "{}-{}"

    @classmethod
    def splits(
        cls,
        exts,
        fields,
        root=".data",
        train="train",
        validation="IWSLT16.TED.tst2013",
        test="IWSLT16.TED.tst2014",
        **kwargs,
    ):
        cls.dirname = cls.base_dirname.format(exts[0][1:], exts[1][1:])
        cls.urls = [cls.base_url.format(exts[0][1:], exts[1][1:], cls.dirname)]
        check = os.path.join(root, cls.name, cls.dirname)
        path = cls.download(root, check=check)

        train = ".".join([train, cls.dirname])
        validation = ".".join([validation, cls.dirname])
        if test is not None:
            test = ".".join([test, cls.dirname])

        if not os.path.exists(os.path.join(path, train) + exts[0]):
            cls.clean(path)

        train_data = None if train is None else cls(os.path.join(path, train), exts, fields, **kwargs)
        val_data = None if validation is None else cls(os.path.join(path, validation), exts, fields, **kwargs)
        test_data = None if test is None else cls(os.path.join(path, test), exts, fields, **kwargs)
        return tuple(d for d in (train_data, val_data, test_data) if d is not None)

    @staticmethod
    def clean(path):
        for f_xml in glob.iglob(os.path.join(path, "*.xml")):
            print(f_xml)
            f_txt = os.path.splitext(f_xml)[0]
            with codecs.open(f_txt, mode="w", encoding="utf-8") as fd_txt:
                root = ET.parse(f_xml).getroot()[0]
                for doc in root.findall("doc"):
                    for e in doc.findall("seg"):
                        fd_txt.write(e.text.strip() + "\n")

        xml_tags = ["<url", "<keywords", "<talkid", "<description", "<reviewer", "<translator", "<title", "<speaker"]
        for f_orig in glob.iglob(os.path.join(path, "train.tags*")):
            print(f_orig)
            f_txt = f_orig.replace(".tags", "")
            with (
                codecs.open(f_txt, mode="w", encoding="utf-8") as fd_txt,
                io.open(f_orig, mode="r", encoding="utf-8") as fd_orig,
            ):
                for l in fd_orig:
                    if not any(tag in l for tag in xml_tags):
                        fd_txt.write(l.strip() + "\n")


class WMT14(TranslationDataset):
    urls = [("https://drive.google.com/uc?export=download&id=0B_bZck-ksdkpM25jRUN2X2UxMm8", "wmt16_en_de.tar.gz")]
    name = "wmt14"
    dirname = ""

    @classmethod
    def splits(
        cls,
        exts,
        fields,
        root=".data",
        train="train.tok.clean.bpe.32000",
        validation="newstest2013.tok.bpe.32000",
        test="newstest2014.tok.bpe.32000",
        **kwargs,
    ):
        if "path" not in kwargs:
            expected_folder = os.path.join(root, cls.name)
            path = expected_folder if os.path.exists(expected_folder) else None
        else:
            path = kwargs["path"]
            del kwargs["path"]

        return super(WMT14, cls).splits(exts, fields, path, root, train, validation, test, **kwargs)
