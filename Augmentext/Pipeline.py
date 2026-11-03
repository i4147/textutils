import string
import random
from textblob import TextBlob
import re
from .Operations import ICDToText, ICDFromText, MeSH, ReplaceNumbers
from .Operations import ReplaceWordsWithNumbers, SNOMED, SwapWords
from .Operations import Misspeller, Operation
from .TextOperations import TextLoader

TYPES = ["character", "word", "sentence", "paragraph", "document", "corpus"]


class Pipeline(object):
    def __init__(self, path, extension="txt") -> None:
        super().__init__()
        self.textloader = TextLoader()
        self.textloader.load_from_directory(path, extension=extension)
        self.operations = []

    def sample(self, n, type="sentence"):
        if len(self.operations) <= 0:
            raise Exception("Current pipeline does not have any operations.")
        if type == "sentence":
            pass
        elif type == "paragraph":
            pass
        else:
            raise Exception(
                "Cannot understand '%s'. The 'type' parameter must be one of: %s." % (type, ", ".join(TYPES))
            )
        samples_generated = 0
        samples = []
        while samples_generated < n:
            r_document = random.randint(0, len(self.textloader.corpus.documents) - 1)
            r_sentence = random.randint(0, len(self.textloader.corpus.documents[r_document].sentences) - 1)
            text = self.textloader.corpus.documents[r_document].sentences[r_sentence]
            if len(self.operations) <= 0:
                raise Exception("Cannot sample without any operations.")
            else:
                for operation in self.operations:
                    if random.random() <= operation.probability:
                        text = operation.perform_operation(text)
            samples.append(text)
            samples_generated += 1
        return samples

    def generator(self, type):
        return 0

    def add_operation(self, operation):
        if Operation in operation.__class__.__bases__:
            if 0.0 < operation.probability <= 1.0:
                self.operations.append(operation)
            else:
                raise Exception("The probability parameter must be > 0 and <= 1")
        else:
            raise Exception("The operation must have a parent type Operation.")

    def _levenshtein_distance(self, s, t):
        if s == "":
            return len(t)
        if t == "":
            return len(s)
        if s[-1] == t[-1]:
            cost = 0
        else:
            cost = 1
        distance = min([
            self._levenshtein_distance(s[:-1], t) + 1,
            self._levenshtein_distance(s, t[:-1]) + 1,
            self._levenshtein_distance(s[:-1], t[:-1]) + cost,
        ])
        return distance

    def add_swap_word_list(self, swap_words):
        if len(swap_words) != 0:
            self.swap_words = swap_words
        return 0

    def add_regular_expressions(self, regex_list):
        return 0

    def swap_random_words(self, probability):
        self.operations.append(SwapWords(probability=probability))

    def swap_random_characters(self, probability):
        self.operations.append(SwapWords(probability=probability))

    def snomed_synonym_swap(self, probability):
        self.operations.append(SNOMED(probability=probability))

    def icd_to_text(self, probability):
        self.operations.append(ICDToText(probability=probability))

    def icd_from_text(self, probability):
        self.operations.append(ICDFromText(probability=probability))

    def misspell_random_word(self, probability, aggressive=True):
        self.operations.append(Misspeller(probability=probability, aggressive=aggressive))

    def auto_abbreviate(self, probability, words_per_sentence):
        return 0

    def mesh_synonyms(self, probability):
        self.operations.append(MeSH(probability=probability))

    def word2vec_synonyms(self, probability):
        pass

    def abbreviate(self, probability, abbreviation_list):
        pass

    def expand_abbreviations(self, probability):
        return 0

    def convert_units(self, probability):
        return 0

    def to_upper(self, probability=1.0):
        return 0

    def to_lower(self, probability=1.0):
        return 0

    def convert_words_to_numbers(self, probability):
        return 0

    def convert_numbers_to_words(self, probability, replace_all_integers=False):
        test_str = "here is some text 3 with some numbers 5 in there 9."
        return re.sub(r"\d+", "", test_str)

    def remove_units(self, probability, user_defined=None):
        if user_defined is None:
            print("Call with default list.")
        else:
            print("Call with user defined list.")
        pass

    def remove_numbers(self, probability, from_num, to_num):
        pass

    def remove_random_word(self, probability):
        pass

    def replace_numbers(self, probability):
        self.operations.append(ReplaceNumbers(probability=probability))

    def replace_written_numbers(self, probability):
        self.operations.append(ReplaceWordsWithNumbers(probability=probability))

    def remove_punctuation(self, probability, punctuation_stop_words=None):
        test_string = "Here, in this string (encoded) are some [5] common chars."
        test_string.translate(str.maketrans("", "", string.punctuation))
        return 0

    def strip_whitespace(self, probability=1.0):
        test_string = " some text    "
        return test_string.strip()

    def remove_stop_words(self, probability):
        return 0

    def stem_words(self, probability):
        return 0

    def lemmatise(self, probability):
        return 0

    def remove_frequent_words(self, probability):
        return 0

    def remove_rare_words(self, probability):
        return 0

    def spell_correct(self, probability):
        t = "apendix"
        t_corrected = TextBlob.correct(t)
        return t_corrected.string


class Corpus(object):
    def __init__(self, documents, paragraphs, sentences, words, characters):
        print("Init of Corpus class.")
        self.documents = documents
        self.paragraphs = paragraphs
        self.sentences = sentences
        self.words = words
        self.characters = characters

    def document_count(self):
        return len(self.documents)

    def paragraph_count(self):
        return len(self.paragraphs)

    def sentence_count(self):
        return len(self.sentences)

    def word_count(self):
        return len(self.words)

    def character_count(self):
        return len(self.characters)

    def summary(self):
        summary_text = "some text"
        return summary_text
