import nltk
import string
import pandas as pd
import numpy as np


def _clean_string(text):

    stopwords = nltk.corpus.stopwords.words("english")

    for punctuation in string.punctuation:
        text = text.replace(punctuation, f" {punctuation} ")

    tokenized_text = nltk.word_tokenize(text)

    text_clean = [word for word in tokenized_text if word not in stopwords]
    text_clean = [word for word in text_clean if word not in string.punctuation]

    cleaned_text = " ".join(text_clean).lower()

    return cleaned_text


def _clean_numpy(text_array):

    arr_shape = text_array.shape
    cleaned_text_array = text_array.copy().reshape((-1,))

    print("Cleaning text")

    for i in range(len(cleaned_text_array)):
        cleaned_text_array[i] = _clean_string(cleaned_text_array[i])

        percent_done = (i / len(cleaned_text_array)) * 100
        print("%.3f%% done" % percent_done, end="\r")

    cleaned_text_array = cleaned_text_array.reshape(arr_shape)

    return cleaned_text_array


def _clean_pandas(text_series):

    if type(text_series) is pd.core.series.Series:
        text_array = text_series.to_numpy()
        cleaned_text_array = _clean_numpy(text_array)

        return pd.Series(cleaned_text_array)

    elif type(text_series) is pd.core.frame.DataFrame:
        text_array = text_series.to_numpy()
        cleaned_text_array = _clean_numpy(text_array)

        return pd.DataFrame(cleaned_text_array)


def important_text(text_data):

    if type(text_data) is str:
        return _clean_string(text_data)

    elif type(text_data) is np.ndarray:
        return _clean_numpy(text_data)

    elif isinstance(text_data, (pd.core.frame.DataFrame, pd.core.series.Series)):
        return _clean_pandas(text_data)


def _string_lexicon(text):

    lex = set(nltk.word_tokenize(text))

    return lex


def _numpy_lexicon(text_array):

    text_array_copy = text_array.copy().reshape((-1,))

    print("Creating lexicon")

    lex = set()
    for i in range(len(text_array_copy)):
        lex = lex.union(_string_lexicon(text_array_copy[i]))

        percent_done = (i / len(text_array_copy)) * 100
        print("%.3f%% done" % percent_done, end="\r")

    return lex


def _pandas_lexicon(text_series):

    lex = _numpy_lexicon(text_series.to_numpy())

    return lex


def lexicon(text_data):

    if type(text_data) is str:
        return _string_lexicon(text_data)

    elif type(text_data) is np.ndarray:
        return _numpy_lexicon(text_data)

    elif isinstance(text_data, (pd.core.frame.DataFrame, pd.core.series.Series)):
        return _pandas_lexicon(text_data)


def _string_bagger(text, lex):

    bag = dict.fromkeys(lex, [])
    word_freq = dict.fromkeys(lex, 0)

    tokens = nltk.word_tokenize(text)

    for word in tokens:
        word_freq[word] += 1

    for word in bag:
        bag[word] = bag[word][:]
        bag[word].append(word_freq[word])

    return bag


def _numpy_bagger(text_array, lex):

    text_array_copy = text_array.copy().reshape((-1,))

    bag = dict.fromkeys(lex, [])

    print(f"Bagging {len(text_array_copy)} items")

    for i in range(len(text_array_copy)):
        word_freq = dict.fromkeys(lex, 0)
        tokens = nltk.word_tokenize(text_array_copy[i])

        for word in tokens:
            word_freq[word] += 1

        for word in bag:
            bag[word] = bag[word][:]
            bag[word].append(word_freq[word])

        percent_done = (i / len(text_array_copy)) * 100
        print("%.3f%% done" % percent_done, end="\r")

    return bag


def _pandas_bagger(text_series, lex):

    bag = _numpy_bagger(text_series.to_numpy(), lex)

    return bag


def text_bag(text_data, lex):

    if type(text_data) is str:
        return _string_bagger(text_data, lex)

    elif type(text_data) is np.ndarray:
        return _numpy_bagger(text_data, lex)

    elif isinstance(text_data, (pd.core.frame.DataFrame, pd.core.series.Series)):
        return _pandas_bagger(text_data, lex)
