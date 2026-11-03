from __future__ import division
from collections import defaultdict
import string
import re
import numpy as np


class CountProbPair:
    def __init__(self):
        self.count = 0
        self.prob = 0.0


class Markov:
    def __init__(self, n=2):
        self.word_dict = defaultdict(lambda: defaultdict(CountProbPair))
        self.word_dict[("",)][""].prob = 0.0
        self.word_dict[("",)][""].count = 0
        self.n = n

    def add_to_dict(self, text):
        n = self.n
        sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!)\s", text)
        for sentence in sentences:
            sentence = sentence.replace('"', "")
            words = sentence.strip().split()
            if len(words) == 0:
                continue
            self.word_dict[("",)][words[0]].count += 1
            for j in range(1, n + 1):
                for i in range(len(words) - 1):
                    if i + j >= len(words):
                        continue
                    word = tuple(words[i : i + j])
                    self.word_dict[word][words[i + j]].count += 1
                self.word_dict[tuple(words[len(words) - j : len(words)])][""].count += 1
        for word in self.word_dict:
            wordsum = 0
            for nextword in self.word_dict[word]:
                wordsum += self.word_dict[word][nextword].count
            if wordsum != 0:
                for nextword in self.word_dict[word]:
                    self.word_dict[word][nextword].prob = self.word_dict[word][nextword].count / wordsum

    def create_sentence(self, start=("",)):
        sentence = list(start)
        nxt = self.next_word(start)
        while nxt:
            sentence.append(nxt)
            nxt = self.next_word(sentence[-self.n :])
        return " ".join(sentence)

    def next_word(self, previous_words):
        previous_words = tuple(previous_words)
        if previous_words != ("",):
            while previous_words not in self.word_dict:
                previous_words = tuple(previous_words[1:])
                if not previous_words:
                    return ""
        frequencies = self.word_dict[previous_words]
        inv = [(v.prob, k) for k, v in frequencies.items()]
        p, w = zip(*inv)
        return np.random.choice(w, 1, p)[0]

    def create_sentences(self, num, start=("",)):
        par = ""
        for _ in range(num):
            par = par + self.create_sentence(start)
        return par
