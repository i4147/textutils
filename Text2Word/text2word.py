import nltk
from nltk.corpus import stopwords
from nltk.stem.porter import *
import re
from bs4 import BeautifulSoup
import numpy as np


class performtext2word:
    def __init__(self):

        pass

    def review_to_words(self, review):

        nltk.download("stopwords", quiet=True)
        stemmer = PorterStemmer()
        text = BeautifulSoup(review, "html.parser").get_text()
        text = re.sub(r"[^a-zA-Z0-9]", " ", text.lower())
        words = text.split()
        words = [w for w in words if w not in stopwords.words("english")]
        words = [PorterStemmer().stem(w) for w in words]

        return words

    def preprocess_data(self, data_train, data_test):

        words_train = [review_to_words(review) for review in data_train]
        words_test = [review_to_words(review) for review in data_test]

        return words_train, words_test

    def build_dict(self, data_train, vocab_size=5000):

        word_count = {}

        wordlist = []
        [wordlist.append(word) for list in train_X for word in list]
        uniquewordlist = []
        freqlist = []

        for word in wordlist:
            if word not in uniquewordlist:
                uniquewordlist.append(word)
                freqlist.append(1)
            else:
                freqlist[uniquewordlist.index(word)] = freqlist[uniquewordlist.index(word)] + 1

        word_count["word"] = uniquewordlist
        word_count["freq"] = freqlist

        sorted_words = None
        sorted_freqlist, sorted_words = zip(*sorted(zip(freqlist, uniquewordlist), reverse=True))

        word_dict = {}
        for idx, word in enumerate(sorted_words[: vocab_size - 2]):
            word_dict[word] = idx + 2

        return word_dict, freqlist

    def extract_BoW_features(self, data_train, data_test, vocabulary_size=5000):

        vectorizer = CountVectorizer(max_features=vocabulary_size, preprocessor=lambda x: x, tokenizer=lambda x: x)
        features_train = vectorizer.fit_transform(words_train).toarray()

        features_test = vectorizer.transform(words_test).toarray()

        return features_train, features_test, vocabulary
