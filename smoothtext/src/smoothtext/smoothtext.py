from . import Backend
from . import Language
from . import ReadabilityFormula
from .internal.syllabifier import (
    SyllabifierEng,
    SyllabifierGer,
    SyllabifierTur,
    _is_consonant,
    _is_vowel,
    _asciify,
)
from .internal.tokenizer import NLTKTokenizer, StanzaTokenizer

import emoji
from emoji.unicode_codes import load_from_json as load_emoji_codes
import math
import logging

_Prepared: dict[Backend, dict[Language, bool]] = {}


def _prepare(backend: Backend, language: Language, skip_downloads: bool, **backend_kwargs) -> None:
    language = language.family()

    logging.debug(f"Preparing backend {backend} for language {language}...")

    if backend not in _Prepared:
        _Prepared[backend] = {}

    backend_languages = _Prepared[backend]
    if language in backend_languages:
        downloaded = backend_languages[language]
        if downloaded or not skip_downloads:
            logging.debug(f"Backend {backend} already prepared for language {language}. Skipping...")
            return

        logging.debug(f"Backend {backend} already prepared for language {language} but download required...")

    if skip_downloads:
        _Prepared[backend][language] = False
        logging.debug(f"Skipping downloads for backend {backend} and marking language {language} as prepared.")
        return

    if Backend.NLTK == backend:
        was_downloaded = False
        for language in backend_languages:
            if backend_languages[language]:
                was_downloaded = True
                break

        if was_downloaded:
            logging.debug(f"NLTK data already downloaded. Skipping...")
        else:
            import nltk

            for package in ("cmudict", "punkt", "punkt_tab", "wordnet"):
                if not nltk.download(package, **backend_kwargs):
                    logging.error("Failed to download NLTK data. Exiting...")
                    return

    elif Backend.Stanza == backend:
        import stanza

        stanza.download(
            lang=language.alpha2(),
            processors="tokenize, mwt, pos, lemma",
            **backend_kwargs,
        )

    _Prepared[backend][language] = True


class SmoothText:
    __constants: dict[Language, tuple[float, float, float]] = {
        Language.English: (206.835, 1.015, 84.6),
        Language.German: (180.0, 1.0, 58.5),
        Language.Turkish: (198.825, 2.61, 40.175),
    }

    __reading_speed: tuple[float, float] = (238.0, 183.0)

    @staticmethod
    def prepare(
        backend: Backend | str | None = None,
        languages: Language | list[Language] | str | list[str] | None = None,
        skip_downloads: bool = False,
        silence_downloaders: bool = True,
        **backend_kwargs,
    ) -> None:

        if languages is None:
            languages = Language.values()
        else:
            languages = Language.parse_multiple(languages)
            if 0 == len(languages):
                logging.warning("No languages to enable. Defaulting to all languages.")
                languages = Language.values()

        if backend is None:
            backends = Backend.list_supported()
            if 0 == len(backends):
                logging.error("No backends to prepare. Exiting...")
                return

            backend = backends[0]
            logging.info(f"No backend specified. Defaulting to {backend}.")
        else:
            backend = Backend.parse(backend)
            if backend is None:
                logging.warning("No valid backend to prepare. Exiting...")

            if not Backend.is_supported(backend):
                logging.warning(f"Backend {backend} not supported. Exiting...")
                return

        logging.debug(f"Preparing {backend} for {languages}...")

        if silence_downloaders:
            if Backend.NLTK == backend:
                if "quiet" not in backend_kwargs:
                    backend_kwargs["quiet"] = True
            elif Backend.Stanza == backend:
                if "verbose" not in backend_kwargs:
                    backend_kwargs["verbose"] = False

                if "logging_level" not in backend_kwargs:
                    backend_kwargs["logging_level"] = logging.FATAL

        for language in languages:
            _prepare(backend, language, skip_downloads, **backend_kwargs)

    @staticmethod
    def is_ready(backend: Backend | str, language: Language | str) -> bool:

        return backend in _Prepared and language in _Prepared[backend]

    @property
    def backend(self) -> Backend:

        return self.__backend

    def __configure_backend(self, backend: Backend) -> None:
        if Backend.NLTK == backend:
            self.__tokenizer = NLTKTokenizer(self.__language.family().value.lower())

        if Backend.Stanza == backend:
            self.__tokenizer = StanzaTokenizer(self.__language.alpha2())

    @property
    def language(self) -> Language:

        return self.__language

    @language.setter
    def language(self, language: Language | str) -> None:

        language = Language.parse(language)
        if language is None:
            logging.fatal("Invalid language.")

        SmoothText.prepare(
            backend=self.__backend,
            languages=language,
            skip_downloads=False,
            silence_downloaders=True,
        )

        self.__configure_language(language)

    def __configure_language(self, language: Language) -> None:
        if Language.English == language:
            language = Language.English_US

        if Language.English == language.family():
            self.__syllabifier = SyllabifierEng(self.__backend, language)

        if Language.German == language:
            language = Language.German_DE

        if Language.German == language.family():
            self.__syllabifier = SyllabifierGer()

        if Language.Turkish == language:
            language = Language.Turkish_TR

        if Language.Turkish == language.family():
            self.__syllabifier = SyllabifierTur()

        self.__language = language
        self._constants = SmoothText.__constants[self.__language.family()]

        self.__configure_backend(self.__backend)

    def __init__(
        self,
        language: Language | str | None = None,
        backend: Backend | str | None = None,
    ) -> None:
        backend = Backend.parse(backend)
        language = Language.parse(language)

        if backend is None and language is None:
            raise RuntimeError("Both backend and language are invalid. Exiting...")

        SmoothText.prepare(
            backend=backend,
            languages=language,
            skip_downloads=False,
            silence_downloaders=True,
        )

        self.__backend = backend
        self.__configure_language(language)

    def __call__(self, *args, **kwargs):
        return self.compute_readability(*args, **kwargs)

    def sentencize(self, text: str) -> list[str]:
        return self.__tokenizer.sentencize(text)

    def count_sentences(self, text: str) -> int:
        return len(self.sentencize(text))

    def tokenize(self, text: str, split_sentences: bool = False) -> list[str] | list[list[str]]:
        return self.__tokenizer.tokenize(text, split_sentences)

    @staticmethod
    def __filter_words(tokens: list[str]) -> list[str]:
        return [word for word in tokens if any(c.isalnum() for c in word)]

    @staticmethod
    def __count_words(tokens: list[str]) -> int:
        num_words: int = 0

        for token in tokens:
            for c in token:
                if c.isalnum():
                    num_words += 1
                    break

        return num_words

    def count_words(self, text: str) -> int:
        tokens = self.tokenize(text, False)
        return SmoothText.__count_words(tokens)

    def word_frequencies(self, text: str, lemmatize: bool = True) -> dict[str, int]:
        if Backend.NLTK == self.__backend and Language.English != self.language.family() and lemmatize:
            logging.warning(
                f"Lemmatization is not supported for {self.language} when using {self.backend}. Disabling..."
            )

            lemmatize = False

        return self.__tokenizer.word_frequencies(text, lemmatize)

    def syllabify(
        self, word: str, tokenize: bool = False, sentencize: bool = False
    ) -> list[str] | list[list[str]] | list[list[list[str]]]:
        if not tokenize and not sentencize:
            return self.__syllabifier.syllabify(word)

        tokens = self.tokenize(text=word, split_sentences=sentencize)
        if not sentencize:
            res: list[list[str]] = []

            for token in tokens:
                res.append(self.__syllabifier.syllabify(token))

            return res
        else:
            res: list[list[list[str]]] = []
            for sentence in tokens:
                words: list[list[str]] = []

                for token in sentence:
                    words.append(self.__syllabifier.syllabify(token))

                res.append(words)

            return res

    def count_syllables(self, word: str, tokenize: bool = True) -> int:
        if tokenize or " " in word:
            tokens: list[str] = self.tokenize(text=word, split_sentences=False)
            return sum([self.count_syllables(word=token, tokenize=False) for token in tokens])

        return self.__syllabifier.count(word.lower().strip())

    def syllable_frequencies(self, text: str) -> dict[int, int]:
        frequencies: dict[int, int] = {}

        tokens: list[str] = self.tokenize(text=text, split_sentences=False)

        for token in tokens:
            token = token.lower().strip()
            syllables: int = self.__syllabifier.count(token)

            if 0 == syllables:
                continue

            if syllables not in frequencies:
                frequencies[syllables] = 0

            frequencies[syllables] += 1

        return frequencies

    @staticmethod
    def count_consonants(text: str) -> int:
        count: int = 0

        text = _asciify(text)
        for c in text:
            if _is_consonant(c):
                count += 1

        return count

    @staticmethod
    def count_vowels(text: str) -> int:
        count: int = 0

        text = _asciify(text)
        for c in text:
            if _is_vowel(c):
                count += 1

        return count

    def demojize(self, text: str, delimiters: tuple[str, str] = ("(", ")")) -> str:
        _emojis: list[str] = emoji.distinct_emoji_list(text)
        if 0 == len(_emojis):
            return text

        for _emoji in _emojis:
            _str = (
                delimiters[0]
                + emoji.demojize(
                    string=_emoji,
                    delimiters=("", ""),
                    language=self.__language.alpha2(),
                ).replace("_", " ")
                + delimiters[1]
            )

            text = text.replace(_emoji, _str)

        return text

    @staticmethod
    def __test_formula_langauge(formula: ReadabilityFormula, language: Language) -> bool:
        if not formula.supports(language):
            logging.warning(
                f"Language and readability formula mismatch. {formula} cannot be used to measure the readability of texts in {language}."
            )

            return False

        return True

    def __compute_1(self, text: str) -> tuple[float, float]:

        total_words: int = 0
        total_syllables: int = 0
        num_sentences: int = 0

        sentences: list[list[str]] = self.tokenize(text=text, split_sentences=True)

        for sentence in sentences:
            words: list[str] = SmoothText.__filter_words(sentence)

            if 0 == len(words):
                continue

            num_sentences += 1
            total_words += len(words)
            for word in words:
                total_syllables += self.count_syllables(word=word, tokenize=False)

        if 0 == num_sentences:
            return 0.0, 0.0

        return (float(total_syllables) / float(total_words)), (float(total_words) / float(num_sentences))

    def __compute_2(self, text: str) -> tuple[float, float, int, dict[int, int]]:

        total_words: int = 0
        total_syllables: int = 0
        num_sentences: int = 0
        syllable_frequencies: dict[int, int] = {3: 0, 4: 0, 5: 0, 6: 0}

        sentences: list[list[str]] = self.tokenize(text=text, split_sentences=True)

        for sentence in sentences:
            words: list[str] = SmoothText.__filter_words(sentence)

            if 0 == len(words):
                continue

            num_sentences += 1
            total_words += len(words)
            for word in words:
                word_syllable_count = self.count_syllables(word=word, tokenize=False)
                total_syllables += word_syllable_count

                if 3 <= word_syllable_count:
                    if word_syllable_count > 6:
                        word_syllable_count = 6

                    syllable_frequencies[word_syllable_count] += 1

        if 0 == num_sentences:
            return 0.0, 0.0, 0, {}

        return (
            (float(total_syllables) / float(total_words)),
            (float(total_words) / float(num_sentences)),
            num_sentences,
            syllable_frequencies,
        )

    def __compute_3(self, text: str) -> tuple[float, float, float, float]:

        total_words: int = 0
        num_sentences: int = 0

        num_long_words: int = 0
        num_mono_syllable_words: int = 0
        num_multi_syllable_words: int = 0

        sentences: list[list[str]] = self.tokenize(text=text, split_sentences=True)

        for sentence in sentences:
            words: list[str] = SmoothText.__filter_words(sentence)

            if 0 == len(words):
                continue

            num_sentences += 1
            total_words += len(words)

            for word in words:
                word = word.lower().strip()
                if 6 <= len(word):
                    num_long_words += 1

                word_syllable_count = self.__syllabifier.count(word)
                if 1 == word_syllable_count:
                    num_mono_syllable_words += 1
                elif 3 <= word_syllable_count:
                    num_multi_syllable_words += 1

        if 0 == num_sentences:
            return 0.0, 0.0, 0.0, 0.0

        return (
            float(total_words) / float(num_sentences),
            float(num_long_words) / float(total_words) * 100.0,
            float(num_mono_syllable_words) / float(total_words) * 100.0,
            float(num_multi_syllable_words) / float(total_words) * 100.0,
        )

    def __compute_4(self, text: str) -> tuple[int, int, int]:

        num_characters: int = 0
        num_words: int = 0
        num_sentences: int = 0

        sentences: list[list[str]] = self.tokenize(text=text, split_sentences=True)

        for sentence in sentences:
            words: list[str] = SmoothText.__filter_words(sentence)

            if 0 == len(words):
                continue

            num_sentences += 1
            num_words += len(words)

            for word in words:
                for c in word:
                    if c.isalnum():
                        num_characters += 1

        return num_characters, num_words, num_sentences

    def __automated_readability_index(self, text: str) -> float:
        num_characters, num_words, num_sentences = self.__compute_4(text)
        if 0 == num_sentences:
            return 0.0

        return (
            (0.5 * (float(num_words) / float(num_sentences)))
            + (4.71 * (float(num_characters) / float(num_words)))
            - 21.43
        )

    def automated_readability_index(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Automated_Readability_Index, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__automated_readability_index(text=text)

    def __flesch_reading_ease(self, text: str) -> float:
        avg_word_syllables, avg_sentence_length = self.__compute_1(text)
        return (
            self._constants[0] - (self._constants[1] * avg_sentence_length) - (self._constants[2] * avg_word_syllables)
        )

    def flesch_reading_ease(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Flesch_Reading_Ease, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__flesch_reading_ease(text=text)

    def atesman(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Atesman, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__flesch_reading_ease(text=text)

    def __flesch_kincaid_grade(self, text: str) -> float:
        avg_word_syllables, avg_sentence_length = self.__compute_1(text)
        return (0.39 * avg_sentence_length) + (11.8 * avg_word_syllables) - 15.9

    def flesch_kincaid_grade(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Flesch_Kincaid_Grade, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__flesch_kincaid_grade(text=text)

    def __flesch_kincaid_grade_simplified(self, text: str) -> float:
        avg_word_syllables, avg_sentence_length = self.__compute_1(text)
        return (0.4 * avg_sentence_length) + (12.0 * avg_word_syllables) - 16.0

    def flesch_kincaid_grade_simplified(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Flesch_Kincaid_Grade_Simplified, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__flesch_kincaid_grade_simplified(text=text)

    def __wiener_sachtextformel(self, text: str, version: int) -> float:
        SL, IW, ES, MS = self.__compute_3(text)

        if 1 == version:
            return 0.1935 * MS + 0.1672 * SL + 0.1297 * IW - 0.0327 * ES - 0.875

        if 2 == version:
            return 0.2007 * MS + 0.1682 * SL + 0.1373 * IW - 2.779

        if 3 == version:
            return 0.2963 * MS + 0.1905 * SL - 1.1144

        if 4 == version:
            return 0.2744 * MS + 0.2656 * SL - 1.693

        return 0.0

    def wiener_sachtextformel(self, text: str, demojize: bool = False, version: int = 3) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Wiener_Sachtextformel, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__wiener_sachtextformel(text=text, version=version)

    def wiener_sachtextformel_1(self, text: str, demojize: bool = False) -> float:
        return self.wiener_sachtextformel(text=text, demojize=demojize, version=1)

    def wiener_sachtextformel_2(self, text: str, demojize: bool = False) -> float:
        return self.wiener_sachtextformel(text=text, demojize=demojize, version=2)

    def wiener_sachtextformel_3(self, text: str, demojize: bool = False) -> float:
        return self.wiener_sachtextformel(text=text, demojize=demojize, version=3)

    def wiener_sachtextformel_4(self, text: str, demojize: bool = False) -> float:
        return self.wiener_sachtextformel(text=text, demojize=demojize, version=4)

    def __bezirci_yilmaz(self, text: str) -> float:
        _, avg_sentence_length, num_sentences, syllable_frequencies = self.__compute_2(text)

        score: float = 0.0
        score += (float(syllable_frequencies.get(3, 0)) / float(num_sentences)) * 0.84
        score += (float(syllable_frequencies.get(4, 0)) / float(num_sentences)) * 1.5
        score += (float(syllable_frequencies.get(5, 0)) / float(num_sentences)) * 3.5
        score += (float(syllable_frequencies.get(6, 0)) / float(num_sentences)) * 26.25

        return math.sqrt(avg_sentence_length * score)

    def bezirci_yilmaz(self, text: str, demojize: bool = False) -> float:
        if not SmoothText.__test_formula_langauge(ReadabilityFormula.Bezirci_Yilmaz, self.__language):
            return 0.0

        if demojize:
            text = self.demojize(text)

        return self.__bezirci_yilmaz(text=text)

    def compute_readability(self, text: str, formula: ReadabilityFormula, demojize: bool = False) -> float:
        if not formula.supports(self.__language):
            logging.warning(
                f"Language and readability formula mismatch. {formula} cannot be used to measure the readability of texts in {self.__language}."
            )
            return 0.0

        if demojize:
            text = self.demojize(text=text)

        if ReadabilityFormula.Atesman == formula or ReadabilityFormula.Flesch_Reading_Ease == formula:
            return self.__flesch_reading_ease(text=text)

        if ReadabilityFormula.Automated_Readability_Index == formula:
            return self.__automated_readability_index(text=text)

        if ReadabilityFormula.Bezirci_Yilmaz == formula:
            return self.__bezirci_yilmaz(text=text)

        if ReadabilityFormula.Flesch_Kincaid_Grade == formula:
            return self.__flesch_kincaid_grade(text=text)

        if ReadabilityFormula.Flesch_Kincaid_Grade_Simplified == formula:
            return self.__flesch_kincaid_grade_simplified(text=text)

        if ReadabilityFormula.Wiener_Sachtextformel == formula:
            return self.__wiener_sachtextformel(text=text, version=3)

        if ReadabilityFormula.Wiener_Sachtextformel_1 == formula:
            return self.__wiener_sachtextformel(text=text, version=1)

        if ReadabilityFormula.Wiener_Sachtextformel_2 == formula:
            return self.__wiener_sachtextformel(text=text, version=2)

        if ReadabilityFormula.Wiener_Sachtextformel_3 == formula:
            return self.__wiener_sachtextformel(text=text, version=3)

        if ReadabilityFormula.Wiener_Sachtextformel_4 == formula:
            return self.__wiener_sachtextformel(text=text, version=4)

        return 0.0

    def __reading_time(self, text: str, words_per_minute: float, round_up: bool) -> float:
        seconds: float = float(self.count_words(text=text)) / words_per_minute * 60.0
        return math.ceil(seconds) if round_up else seconds

    def reading_time(self, text: str, words_per_minute: float, round_up: bool = True) -> float:
        if 1.0 > words_per_minute:
            words_per_minute = 1.0

        return self.__reading_time(text=text, words_per_minute=words_per_minute, round_up=round_up)

    def silent_reading_time(self, text: str, words_per_minute: float = 238.0, round_up: bool = True) -> float:
        return self.reading_time(text=text, words_per_minute=words_per_minute, round_up=round_up)

    def reading_aloud_time(self, text: str, words_per_minute: float = 183.0, round_up: bool = True) -> float:
        return self.reading_time(text=text, words_per_minute=words_per_minute, round_up=round_up)
