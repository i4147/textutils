"""Tests for `preprocess` package."""
# pylint: disable=redefined-outer-name

from kedatatext.preprocessing import (
    CleaningParams,
    clean_sentence_indonesia,
    clean_sentences_indonesia,
)
import pytest


@pytest.fixture
def clean_params():
    """Fixture to create a CleaningParams object."""
    return CleaningParams()


def test_clean_sentence_indonesia(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentence_indonesia_no_stemming(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.use_stemming = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentence_indonesia_no_remove_stopwords(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_stopwords = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "mereka lihat ini"


def test_clean_sentence_indonesia_no_remove_retweet(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_retweet = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "rt lihat"


def test_clean_sentence_indonesia_no_remove_urls(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_urls = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat httpsexamplecom"


def test_clean_sentence_indonesia_no_remove_mentions(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_mentions = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "canggih lihat"


def test_clean_sentence_indonesia_no_remove_hashtags(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_hashtags = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentence_indonesia_no_remove_numbers(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_numbers = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentence_indonesia_no_remove_extra_ws(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_extra_whitespace = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentence_indonesia_no_remove_punkt(clean_params):
    text = "RT @canggih: Mereka lihat ini: https://example.com"
    clean_params.remove_punctuation = False
    cleaned_text = clean_sentence_indonesia(text, clean_params)
    assert cleaned_text == "lihat"


def test_clean_sentences_indonesia(clean_params):
    text = ["RT @canggih: Mereka lihat ini: https://example.com"]
    cleaned_text = clean_sentences_indonesia(text, clean_params)
    assert cleaned_text == ["lihat"]
