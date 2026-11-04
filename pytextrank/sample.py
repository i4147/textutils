# -*- coding: utf-8 -*-

import pathlib
import sys

from icecream import ic
import spacy

import pytextrank


nlp = spacy.load("en_core_web_sm")

nlp.add_pipe("textrank")

text = pathlib.Path("dat/mih.txt").read_text()
doc = nlp(text)

tr = doc._.textrank
print("elapsed time: {:.2f} ms".format(tr.elapsed_time))

ic("pipeline", nlp.pipe_names)
nlp.analyze_pipes(pretty=True)
print("\n----\n")

for phrase in doc._.phrases:
    print("{:.4f} {:5d}  {}".format(phrase.rank, phrase.count, phrase.text))
    ic(phrase.chunks)


print("\n----\n")
print("dat/lee.txt:")

text = pathlib.Path("dat/lee.txt").read_text()
doc = nlp(text)

for phrase in doc._.phrases[:20]:
    ic(phrase)


print("\n----\n")
print("dat/gen.txt:")

text = pathlib.Path("dat/gen.txt").read_text()
doc = nlp(text)

for phrase in doc._.phrases[:10]:
    ic(phrase)

print("\n----\n")
print("stop words:")

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("textrank", config={"stopwords": {"word": ["NOUN"]}})

doc = nlp(text)

for phrase in doc._.phrases[:10]:
    ic(phrase)


tr = doc._.textrank
tr.write_dot(path="lemma_graph.dot")


print("\n----\n")
print("extractive summarization:")

for sent in tr.summary(limit_phrases=15, limit_sentences=5):
    ic(sent)


EXPECTED_PHRASES = [
    "grandmaster Lee Sedol",
    "Lee Sedol",
    "Deep Blue",
    "world chess champion Gary Kasparov",
    "chess",
    "Gary Kasparov",
    "the following year",
    "Kasparov",
]


print("\n----\n")
print("TopicRank:")

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("topicrank")

text = pathlib.Path("dat/lee.txt").read_text()
doc = nlp(text)

for phrase in doc._.phrases[: len(EXPECTED_PHRASES)]:
    ic(phrase)

tr = doc._.textrank


print("\n----\n")
print("PositionRank:")

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("positionrank")

text = pathlib.Path("dat/lee.txt").read_text()
doc = nlp(text)

for phrase in doc._.phrases[: len(EXPECTED_PHRASES)]:
    ic(phrase)

tr = doc._.textrank


print("\n----\n")
print("Biased TextRank:")

nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("biasedtextrank")

text = pathlib.Path("dat/lee.txt").read_text()
doc = nlp(text)

for phrase in doc._.phrases[: len(EXPECTED_PHRASES)]:
    ic(phrase)

tr = doc._.textrank

phrases = tr.change_focus(
    focus="It wasn't until the following year that Deep Blue topped Kasparov over the course of a six-game contest.",
    bias=10.0,
    default_bias=0.0,
)

print("\n----\n")
ic(EXPECTED_PHRASES)

for phrase in phrases[: len(EXPECTED_PHRASES)]:
    ic(phrase.text)
    ic(phrase.text in EXPECTED_PHRASES)
