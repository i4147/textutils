import os
import argparse
import json
from pycontractions import Contractions
from aiotext.lemmatize import lemmatize
import re
import string
from aiotext.splitToSentences import split_into_sentences
import regex


class Cleaner:
    def __init__(
        self,
        options={
            "expand_contractions": True,
            "strip_text_in_brackets": False,
            "combine_concatenations": False,
            "w2v_path": None,
            "api_key": "word2vec-google-news-300",
        },
    ):
        self.options = options

        if options["expand_contractions"]:
            print("Loading contractions dataset (this will take a while the first time)")

            self.cont = Contractions(w2v_path=options["w2v_path"], api_key=options["api_key"])
            print("Contractions dataset downloaded")

            print("Training contractions model (this will take a while)")
            self.cont.load_models()
            print("Contraction model successfully trained")

    def expand_contractions(self, text):
        text = text.replace("’", "'")
        expanded_text = list(self.cont.expand_texts([text], precise=True))
        return expanded_text[0]

    def strip_brackets(self, text):

        brace_open_type = ""
        brace_pair = {"(": ")", "[": "]", "{": "}"}
        open_brace_list = list(brace_pair.keys())

        res = ""
        for c in text:
            if len(brace_open_type) == 0:
                if c in open_brace_list:
                    brace_open_type = c
                else:
                    res += c
            else:
                if brace_pair[brace_open_type] == c:
                    brace_open_type = ""

        return res

    def combine_concatenations(self, text):
        if self.options["combine_concatenations"]:
            text = regex.sub(r"\p{Pd}+", "", text)
        else:
            text = regex.sub(r"\p{Pd}+", " ", text)

        return text

    def split_sentences(self, text):
        return split_into_sentences(text)

    def remove_non_english(self, sentences):
        # stripped = re.sub('[^a-zA-Z\s]*', '', stripped)

        # stripped = re.sub('[ ]{2,}',' ', stripped)

        stripped_sentences = []
        for sentence in sentences:
            cleaned = re.sub("[ ]{2,}", " ", re.sub("[^a-zA-Z\s]*", "", sentence))
            if len(cleaned) != 0:
                stripped_sentences.append(cleaned)

        return stripped_sentences

    def tokenize_sentences(self, sentences):
        tokenized_sentences = []
        for sentence in sentences:
            tokenized_sentences.append(sentence.split())
        return tokenized_sentences

    def lemmatize_sentences(self, tokenized_sentences):
        lemmatized_sentences = []
        for sentence in tokenized_sentences:
            lemmatized_sentences.append(lemmatize(sentence))
        return lemmatized_sentences

    def clean(self, text):
        text = text.lower()

        if self.options["expand_contractions"]:
            text = self.expand_contractions(text)

        if self.options["strip_text_in_brackets"]:
            text = self.strip_brackets(text)

        text = self.combine_concatenations(text)
        sentences = self.split_sentences(text)
        cleaned_sentences = self.remove_non_english(sentences)
        tokenized_cleaned_sentences = self.tokenize_sentences(cleaned_sentences)
        lemmatized_tokenized_sentences = self.lemmatize_sentences(tokenized_cleaned_sentences)

        return lemmatized_tokenized_sentences
