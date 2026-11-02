from vncorenlp import VnCoreNLP

annotator = VnCoreNLP("/home/longnt/VnCoreNLP/VnCoreNLP-1.1.1.jar", annotators="wseg, ner, pos", max_heap_size="-Xmx2g")
import json
import os
from random import randint
import numpy as np


class LexicalReplacement:
    def __init__(self, path, replacement_rate=0.1):
        self.rate = replacement_rate
        with open(os.path.join(path, "vietnamese-wordnet-by-type.json"), "r") as f:
            self.wordnet = json.load(f)
        self.not_change_type = ["Np", "CH", "Nux", "M", "Mx", "L", "P", "R", "E", "Cc", "T", "X", "Nu", "Nc"]

    def random_select_synonym(self, synonym):
        return synonym[randint(0, len(synonym) - 1)]

    def augment(self, text):
        annotated = annotator.annotate(text)["sentences"]
        s = []
        for i in annotated:
            s += [w["form"].replace("_", " ").lower() for w in i]
        num_replace_word = int(np.ceil(len(s) * self.rate))
        to_augment_index = [randint(0, len(s) - 1) for i in range(num_replace_word)]
        all_word_annotated = []
        for i in annotated:
            all_word_annotated += i
        for index in to_augment_index:
            if all_word_annotated[index]["posTag"] not in self.not_change_type:
                wordnet_dict = self.wordnet[all_word_annotated[index]["posTag"]]
                w = s[index]
                if w in wordnet_dict:
                    s[index] = self.random_select_synonym(wordnet_dict[w]).strip()
        return " ".join(s)


class WordEmbeddingReplacement:
    def __init__(self, path, replacement_rate=0.1):
        self.rate = replacement_rate
        with open(os.path.join(path, "phow2v_NAV.json"), "r") as f:
            self.wordnet = json.load(f)
        self.not_change_type = ["Np", "CH", "Nux", "M", "Mx", "L", "P", "R", "E", "Cc", "T", "X", "Nu", "Nc"]

    def random_select_synonym(self, synonym):
        return synonym[randint(0, len(synonym) - 1)]

    def augment(self, text):
        annotated = annotator.annotate(text)["sentences"]
        s = []
        for i in annotated:
            s += [w["form"].replace("_", " ").lower() for w in i]
        num_replace_word = int(np.ceil(len(s) * self.rate))
        to_augment_index = [randint(0, len(s) - 1) for i in range(num_replace_word)]
        all_word_annotated = []
        for i in annotated:
            all_word_annotated += i
        for index in to_augment_index:
            if all_word_annotated[index]["posTag"] not in self.not_change_type:
                wordnet_dict = self.wordnet[all_word_annotated[index]["posTag"]]
                w = s[index]
                if w in wordnet_dict:
                    s[index] = self.random_select_synonym(wordnet_dict[w]).strip()
        return " ".join(s)


class SpellingErrorInjection:
    def __init__(self, replacement_rate=0.1):
        self.rate = replacement_rate
        self.vichar = "a脿谩岷Ｃａ骸膬岷贬函岷翅旱岷访⑨骇岷メ憨岷涵bcd膽e猫茅岷会航岷姑粊岷酷粌峄呩粐ghi矛铆峄壞┽粙lkmno貌贸峄徝滇粛么峄撫粦峄曖粭峄櫰♂粷峄涐粺峄♂唬pqrstu霉煤峄┽互瓢峄哗峄化峄眝xy峄趁结环峄贯坏"

    def augment(self, text):
        num_char_replacement = int(np.ceil(self.rate * len(text)))
        new_text = list(text)
        for i in range(num_char_replacement):
            random_index = randint(0, len(text) - 1)
            random_char = text[random_index]
            if random_char != " ":
                new_index = -1
                while new_index < 0:
                    new_index = random_index + randint(-3, 3)
                new_char = self.vichar[new_index]
            else:
                new_char = random_char
            new_text[random_index] = new_char
        return "".join(new_text)
