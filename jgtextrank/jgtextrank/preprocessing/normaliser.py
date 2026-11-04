# -*- coding: utf-8 -*-


import string
import six
import unicodedata

from nltk.stem.porter import *
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

__author__ = "Jie Gao <j.gao@sheffield.ac.uk>"
__all__ = [
    "wordnet_lemmatizer",
    "punctutations",
    "punctuation_filter",
    "stemmer",
    "stem",
    "lemmatize",
    "normalize",
    "punctuation_filter_for_list",
    "remove_punctuations",
    "remove_digits",
    "punctuation_filter_for_word_level",
]

# global variables
WS = " "
COLLAPSE = re.compile(r"\s+")

CATEGORY_DEFAULTS = {
    "M": "",
}

wordnet_lemmatizer = WordNetLemmatizer()
punctutations = string.punctuation
punctuation_filter = lambda t: filter(lambda a: a not in string.punctuation, t)
stemmer = PorterStemmer()


def stem(word):
    return stemmer.stem(word)


def lemmatize(word, pos="n"):
    if not pos.strip():
        return word

    return wordnet_lemmatizer.lemmatize(word, pos=pos)


def get_wordnet_pos(nltk_pos_tag):
    if nltk_pos_tag.startswith("J"):
        return wordnet.ADJ
    elif nltk_pos_tag.startswith("V"):
        return wordnet.VERB
    elif nltk_pos_tag.startswith("N"):
        return wordnet.NOUN
    elif nltk_pos_tag.startswith("R"):
        return wordnet.ADV
    else:
        return ""


def normalize(
    text, lowercase=True, collapse=True, decompose=True, replace_categories=CATEGORY_DEFAULTS, lemma=False, pos_tag="n"
):
    if not isinstance(text, six.string_types):
        return

    if six.PY2 and not isinstance(text, six.text_type):
        text = text.decode("utf-8")

    if lowercase:
        text = text.lower()

    # if transliterate:
    #    # Perform unicode-based transliteration, e.g. of cyricllic
    #    # or CJK scripts into latin.
    #    text = unidecode(text)
    #    if six.PY2:
    #        text = unicode(text)

    if decompose:
        text = unicodedata.normalize("NFKD", text)

    characters = []
    for character in text:
        category = unicodedata.category(character)[0]
        character = replace_categories.get(category, character)
        characters.append(character)
    text = "".join(characters)
    # print(text)
    if collapse:
        text = COLLAPSE.sub(WS, text).strip(WS)

    if lemma:
        text = lemmatize(text, pos=get_wordnet_pos(pos_tag))

    return text


def punctuation_filter_for_list(tokens=list()):
    return [remove_punctuations(token) for token in tokens]


def remove_punctuations(raw_term):
    replace_all_punc_term_trans = raw_term.maketrans(string.punctuation, " " * len(string.punctuation))
    space_replace_punc_all_term = raw_term.translate(replace_all_punc_term_trans)
    space_replace_punc_all_term = " ".join(space_replace_punc_all_term.split())
    return space_replace_punc_all_term


def remove_digits(raw_term):
    remove_all_digits_term_trans = raw_term.maketrans(string.digits, " " * len(string.digits))
    remove_punc_raw_term = raw_term.translate(remove_all_digits_term_trans)
    remove_punc_raw_term = remove_punc_raw_term.strip()
    remove_punc_raw_term = " ".join(remove_punc_raw_term.split())
    return remove_punc_raw_term


def punctuation_filter_for_word_level(tokens=list()):
    filtered_tokens = punctuation_filter(tokens)
    punc_filtered_tokens = list()
    for token in filtered_tokens:
        punc_filtered_token = remove_punctuations(token)
        if " " in punc_filtered_token:
            punc_filtered_tokens.extend(punc_filtered_token.split(" "))
        else:
            punc_filtered_tokens.append("".join(punc_filtered_token))

    return punc_filtered_tokens
    # return [''.join(punctuation_filter(token)) for token in filtered_tokens]


if __name__ == "__main__":
    print(normalize("supporting", lemma=True, pos_tag="VBG"))

    print(normalize("inequations", lemma=True, pos_tag="n"))

    print(normalize("corresponding", lemma=True, pos_tag="JJ"))
