from abc import abstractclassmethod
import string
import os
import glob
from pathlib import Path
from nltk import tokenize
import re
import time


class TextLoader(object):
    def __init__(self) -> None:
        super().__init__()
        self.file_list = []
        self.absolute_file_list = []
        self.corpus = Corpus()

    def load_from_directory(self, path, extension):
        start = time.time()
        if extension[0] == ".":
            extension = "*" + extension
        else:
            extension = "*." + extension
        self.file_list = glob.glob(os.path.join(path, extension))
        print("Found %s file(s).\nParsing... " % len(self.file_list))
        for f in self.file_list:
            self.absolute_file_list.append(Path(f).resolve())
        for f in self.absolute_file_list:
            print("Parsing %s" % f, end="\r")
            self.corpus.add_document(f)
        print("")
        print("Parsed %s file(s) in %s seconds." % (len(self.file_list), str(round(time.time() - start, 2))))

    def print_summary(self):
        if len(self.corpus.documents) != 0:
            self.corpus.print_summary()
        else:
            print("Empty corpus. Load files using load_from_directory() function.")


class Corpus(object):
    def __init__(self) -> None:
        super().__init__()
        self.documents = []

    def add_document(self, absolute_path):
        self.documents.append(Document(absolute_path))

    def print_summary(self):
        n_paragraphs = 0
        n_sentences = 0
        n_words = 0
        n_documents = len(self.documents)
        print("")
        print("{:<25} {:<15} {:<15} {:<15}".format("Filename", "Words", "Sentences", "Paragraphs"))
        print(
            "{:<25} {:<15} {:<15} {:<15}".format(
                "-------------------------", "---------------", "---------------", "---------------"
            )
        )
        for d in self.documents:
            n_paragraphs += len(d.paragraphs)
            n_sentences += len(d.sentences)
            n_words += len(d.words)
            d.print_summary()
        print("{:<25} {:<15,} {:<15,} {:<15,}".format("SUM", int(n_words), int(n_sentences), int(n_paragraphs)))
        print(
            "{:<25} {:<15,} {:<15,} {:<15,}".format(
                "AVERAGE", int(n_words / n_documents), int(n_sentences / n_documents), int(n_paragraphs / n_documents)
            )
        )


class Document(object):
    def __init__(self, path) -> None:
        super().__init__()
        self.path = path
        self.filename = os.path.basename(self.path)
        with open(self.path) as reader:
            self.contents = reader.read().strip()
        self.sentences = tokenize.sent_tokenize(self.contents)
        self.sentences = [sentence.strip() for sentence in self.sentences]
        self.paragraphs = re.split("[\n]{2,}", self.contents)
        self.paragraphs = [sentence.strip() for sentence in self.paragraphs]
        self.words = str.split(self.contents)
        self.words_stripped = [w.translate(str.maketrans("", "", string.punctuation)) for w in self.words]

    def print_summary(self):
        (self.filename[:12] + "..." + self.filename[-10:] if len(self.filename) > 25 else self.filename)
        print(
            "{:<25} {:<15,} {:<15,} {:<15,}".format(
                (self.filename[:12] + "..." + self.filename[-10:] if len(self.filename) > 25 else self.filename),
                len(self.words),
                len(self.sentences),
                len(self.paragraphs),
            )
        )


class Text(str):
    def __init__(self) -> None:
        super().__init__()
        self.corpus = []
