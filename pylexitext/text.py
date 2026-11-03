from functools import lru_cache
from random import randint
import re
import string
from typing import List
import networkx as nx
import nltk
from nltk import pos_tag, word_tokenize
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from nltk.stem import WordNetLemmatizer
import numpy as np
from . import (
    plots as plt,
    text_bean as bean,
)


class Text:
    def __init__(self, text, language="english", pre_process=True):
        self.__accepted_languages = ["english"]
        if language not in self.__accepted_languages:
            msg = "language not supported"
            raise TypeError(msg)
        if type(text) is not str:
            msg = "Entry must be an String"
            raise TypeError(msg)
        self.raw_text = text
        self.text = text
        self.language = language
        if pre_process:
            self.__generate_stop_words()
            self.__extract_features()

    def __repr__(self):
        return self.describe()

    def __str__(self):
        return self.raw_text

    def set_lang(self, language="english"):
        self.language = language
        if self.language != language:
            self.__generate_stop_words()
            self.__extract_features()

    @lru_cache(maxsize=128)
    def describe(self, verbose=False):
        description = {
            "text_size": self.text_size,
            "total_words": self.total_words,
            "char_count": self.char_count,
            "non_stop_words": self.stopwords_text,
            "stop_words": self.is_stopwords_text,
            "stop_words_number": self.number_stopwords,
            "unique_terms": self.unique_terms,
            "unique_words": self.text_uniques_number,
            "sentences": self.text_sentences,
            "number_senteces": self.text_sentences_number,
            "lexical_diversity": self.lexical_diversity,
            "frequency_distribution": self.fdist,
            "total_syllables": self.total_syllables,
            "total_polysyllables": self.total_polysyllables,
            "flesch_reading_ease_score": self.flesch_reading_ease_score,
            "flesch_kincaid_grade_level_score": self.flesch_kincaid_grade_level_score,
            "smog_score": self.smog_score,
            "gunning_fog_index_score": self.gunning_fog_index_score,
        }
        if verbose:
            print(description)
        return description

    @lru_cache(maxsize=128)
    def __generate_stop_words(self):
        self.stopwords_set = set(stopwords.words(self.language))
        self.stopwords_set.add(".")

    @lru_cache(maxsize=256)
    def __extract_features(self):
        self.text = self.text.lower()
        self.sentences = re.split(r' *[\.\?!][\'"\)\]]*[ |\n](?=[A-z])', self.text)
        self.total_sentences = self.senteces_count()
        self.text_size = len(self.text)
        self.words = Text.noise_removal(self.text).split(" ")
        self.total_words = len(self.words)
        self.char_count = len(self.text.replace(" ", ""))
        self.stopwords_text = [word for word in self.words if word not in self.stopwords_set]
        self.is_stopwords_text = [word for word in self.words if word in self.stopwords_set]
        self.unique_terms = set(self.stopwords_text)
        self.text_uniques_number = len(self.unique_terms)
        self.text_sentences = self.text.split(".")
        self.text_sentences_number = len(self.text_sentences)
        self.number_stopwords = len(set(self.is_stopwords_text))
        self.lexical_diversity = len(set(self.stopwords_text)) / len(self.stopwords_text) * 100
        self.fdist = FreqDist(self.stopwords_text)
        self.total_syllables = 0
        self.total_polysyllables = 0
        self.total_complex_words = 0
        for y in self.words:
            syllable_count_temp = bean.syllable_count(y)
            self.total_syllables += syllable_count_temp
            if syllable_count_temp >= 3:
                self.total_polysyllables += 1
                self.total_complex_words += 1
        self.flesch_reading_ease_score = self.flesch_reading_ease()
        self.flesch_kincaid_grade_level_score = self.flesch_kincaid_grade_level()
        self.smog_score = self.smog()
        self.gunning_fog_index_score = self.gunning_fog_index()

    @lru_cache(maxsize=128)
    def topics_extraction(self):
        pass

    @lru_cache(maxsize=128)
    def word_frequency_plot(self) -> None:
        plt.word_frequency_plot(self.fdist)
        pass

    @lru_cache(maxsize=128)
    def lexical_tree(self, size=(30, 24), **kwargs):
        pass

    @lru_cache(maxsize=128)
    def lexical_graph(self) -> dict:
        lexical_graph = {}
        for sentence in self.sentences:
            text_nodes = Text.noise_removal(sentence).split(" ")
            for index, word in enumerate(text_nodes):
                if word not in lexical_graph:
                    lexical_graph[word] = []
                if index + 1 < len(text_nodes) and text_nodes[index + 1] not in lexical_graph[word]:
                    lexical_graph[word].append(text_nodes[index + 1])
        return lexical_graph

    def lexical_graph_plot(self, size=(30, 24), dpi=80, **kwargs) -> None:
        graph = self.lexical_graph()
        plt.lexical_graph(graph, size, dpi, kwargs)

    @lru_cache(maxsize=256)
    def rearrange_text(self) -> str:
        print("This function is under development, and is not meant to be used as oficially ready.")
        text_lexical_graph = self.lexical_graph()
        possible_roots = re.findall(r"[A-Z][a-zA-Z]+", self.raw_text)
        if possible_roots:
            root = possible_roots[randint(0, len(possible_roots) - 1)].lower()
        else:
            root = self.raw_text.split(" ")[0].lower()
        new_text = [root, " "]

        def dfs(root, graph, len_text, memoize, visited=set()):
            for v in graph[root.lower()]:
                if len(memoize) < len_text:
                    memoize.extend([v, " "])
                    dfs(v, graph, len_text, memoize)
                else:
                    memoize.pop()
                    memoize.extend(["."])

        dfs(root, text_lexical_graph, len(self.raw_text.split(" ")), new_text)
        return "".join(new_text)

    @lru_cache(maxsize=256)
    def summarize(self, top_n=3, verbose=False) -> str:
        stop_words = stopwords.words(self.language)
        summarize_text = []
        sentences = bean.read_text(self.raw_text)
        sentence_similarity_martix = bean.build_similarity_matrix(sentences, stop_words)
        sentence_similarity_graph = nx.from_numpy_array(sentence_similarity_martix)
        scores = nx.pagerank(sentence_similarity_graph)
        ranked_sentence = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        for i in range(top_n):
            summarize_text.append(" ".join(ranked_sentence[i][1]))
        self.summary = ". ".join(summarize_text)
        if verbose:
            print(self.summary)
        return self.summary

    @lru_cache(maxsize=128)
    def sentiment_analysis(self, verbose=False, method="vader") -> dict:
        if method == "vader":
            from .sentiment import sentiment

            return sentiment.vader_sentiment_analysis(self.text, verbose)
        else:
            pass
        return None

    def named_entity_recognition(self):
        pass

    @lru_cache(maxsize=128)
    def senteces_count(self) -> int:
        self.total_sentences = 0
        for sentece in self.sentences:
            if len(Text.remove_punctuation(text=sentece).split(" ")) > 2:
                self.total_sentences += 1
        return max(1, self.total_sentences)

    @lru_cache(maxsize=256)
    def speech_tagging(self, embedded=False):
        tokens = word_tokenize(self.text)
        self.pos = pos_tag(tokens)
        embedded_pos = []
        if embedded:
            for word, tag in self.pos:
                embedded_word = word + "_" + tag
                embedded_pos.append(embedded_word)
            return embedded_pos
        return self.pos

    @lru_cache(maxsize=128)
    def stemming(self) -> str:
        stemmer = nltk.porter.PorterStemmer()
        self.stemmed_text = " ".join([stemmer.stem(word) for word in self.text.split()])
        return self.stemmed_text

    @lru_cache(maxsize=256)
    def normalization(self) -> str:
        cleaned_text = ""
        lemmatizer = WordNetLemmatizer()
        for word in self.stopwords_text:
            cleaned_text = cleaned_text + " " + lemmatizer.lemmatize(word)
        normalizad_text = cleaned_text[1:]
        stemmer = nltk.porter.PorterStemmer()
        self.normalizad_text = " ".join([stemmer.stem(word) for word in normalizad_text.split()])
        return self.normalizad_text

    @lru_cache(maxsize=128)
    def topics_modeling(self):
        pass

    @lru_cache(maxsize=256)
    def ngrams_extraction(self, n=3) -> list:
        out = []
        for i in range(len(self.words) - n + 1):
            out.append(self.words[i : i + n])
        return out

    @lru_cache(maxsize=256)
    def bigrams_extraction(self) -> list:
        self.bigrams = self.ngrams_extraction(n=2)
        return self.bigrams

    @lru_cache(maxsize=128)
    def avg_sentence_length(self) -> int:
        return round(float(self.total_words / self.total_sentences))

    @lru_cache(maxsize=128)
    def term_frequency(self) -> list:
        terms = []
        for term in self.unique_terms:
            result = {term: (self.words.count(term) / self.text_size) * 100}
            terms.append(result)
        self.terms_frequency = terms
        return self.terms_frequency

    @lru_cache(maxsize=128)
    def text_similarity(self, text) -> float:
        return bean.levenshtein_distance(self.raw_text, text)

    @lru_cache(maxsize=128)
    def flesch_reading_ease(self) -> float:
        return (
            206.835
            - (1.015 * (self.total_words / self.text_sentences_number))
            - (84.7 * (self.total_syllables / self.total_words))
        )

    @lru_cache(maxsize=128)
    def flesch_kincaid_grade_level(self) -> float:
        return (
            (0.39 * (self.total_words / self.text_sentences_number))
            + (11.8 * (self.total_syllables / self.total_words))
            - 15.59
        )

    @lru_cache(maxsize=128)
    def smog(self) -> float:
        return (1.0430 * (np.sqrt(self.total_polysyllables * (30 / self.text_sentences_number)))) + 3.1291

    @lru_cache(maxsize=128)
    def gunning_fog_index(self) -> float:
        return 0.4 * (self.total_words / self.total_sentences) + 100 * (self.total_complex_words / self.total_words)

    @staticmethod
    def split_by(text="") -> list:
        text_chunks = []
        return text_chunks

    @staticmethod
    def remove_numbers(text="") -> str:
        pattern = r"[^a-zA-z.,!?/:;\"\'\s]"
        return re.sub(pattern, "", text)

    @staticmethod
    def remove_punctuation(text="") -> str:
        output = "".join([c for c in text if c not in string.punctuation])
        return output

    @staticmethod
    def remove_extra_whitespace_tabs(text) -> str:
        pattern = r"^\s*|\s\s*"
        return re.sub(pattern, " ", text).strip()

    @staticmethod
    def remove_non_unicode(text) -> str:
        return "".join([i if ord(i) < 128 else "" for i in text])

    @staticmethod
    def noise_removal(text) -> str:
        text = Text.remove_numbers(text)
        text = Text.remove_punctuation(text)
        text = Text.remove_extra_whitespace_tabs(text)
        text = Text.remove_non_unicode(text)
        text = text.lower()
        return text

    @staticmethod
    def sentence_similarity(sentence1, sentence2, percentage_base=False) -> float:
        output = bean.levenshtein_distance(sentence1, sentence2)
        if percentage_base:
            return round(output * 100, 2)
        return output
