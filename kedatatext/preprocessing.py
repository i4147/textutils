import re
import string
from typing import List
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

factory = StemmerFactory()
stemmer = factory.create_stemmer()


class CleaningParams(object):
    to_lower: bool = True
    remove_punctuation: bool = True
    remove_stopwords: bool = True
    remove_numbers: bool = True
    remove_urls: bool = True
    remove_mentions: bool = True
    remove_hashtags: bool = True
    remove_retweet: bool = True
    remove_extra_whitespace: bool = True
    use_stemming: bool = True


def clean_sentence_indonesia(text: str, clean_params: CleaningParams) -> str:
    if clean_params.remove_retweet and text.startswith("RT "):
        text = text[3:].strip()
    if clean_params.remove_urls:
        text = re.sub(r"http\S+", "", text)
    if clean_params.remove_mentions:
        text = re.sub("@[A-Za-z0-9]+", "", text)
    if clean_params.remove_hashtags:
        text = re.sub("#", "", text)
    if clean_params.remove_numbers:
        text = re.sub(r"\d+", "", text)
    if clean_params.to_lower:
        text = text.lower()
    if clean_params.remove_extra_whitespace:
        text = " ".join(text.split())
    if clean_params.remove_punctuation:
        text = text.translate(str.maketrans("", "", string.punctuation))
    if clean_params.remove_stopwords:
        stop_words = set(stopwords.words("indonesian"))
        word_tokens = word_tokenize(text)
        filtered_sentence = [word for word in word_tokens if word not in stop_words]
        text = " ".join(filtered_sentence)
    if clean_params.use_stemming:
        text = stemmer.stem(text)
    return text


def clean_sentences_indonesia(
    list_of_texts: list[str],
    clean_params: CleaningParams,
) -> list[str]:
    return [clean_sentence_indonesia(text, clean_params) for text in list_of_texts]
