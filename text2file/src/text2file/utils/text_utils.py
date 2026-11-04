import random
import re
import string
import textwrap
from typing import List, Tuple


def wrap_text(text: str, width: int = 80, **kwargs) -> str:
    kwargs.setdefault("replace_whitespace", True)
    kwargs.setdefault("drop_whitespace", True)
    kwargs.setdefault("break_long_words", True)
    kwargs.setdefault("break_on_hyphens", True)

    return textwrap.fill(text, width=width, **kwargs)


def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...", words: bool = False) -> str:
    if not text or len(text) <= max_length:
        return text

    if words:
        truncated = text[:max_length]
        if " " in truncated:
            last_space = truncated.rfind(" ")
            if last_space > 0:
                truncated = truncated[:last_space]
    else:
        truncated = text[:max_length]

    return truncated + ellipsis if len(truncated) < len(text) else truncated


def slugify(
    text: str,
    separator: str = "-",
    lowercase: bool = True,
    ascii_only: bool = True,
    allow_unicode: bool = False,
) -> str:
    import unicodedata

    if ascii_only and not allow_unicode:
        text = unicodedata.normalize("NFKD", text)
        text = text.encode("ascii", "ignore").decode("ascii")

    text = re.sub(r"[\s_]+", separator, text)

    if allow_unicode:
        text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    else:
        text = re.sub(r"[^\w\-]", "", text)

    text = re.sub(rf"[{re.escape(separator)}]+", separator, text)

    text = text.strip(separator)

    if lowercase:
        text = text.lower()

    return text


def generate_random_string(length: int = 10, chars: str = string.ascii_letters + string.digits) -> str:
    return "".join(random.choice(chars) for _ in range(length))


def count_words(text: str) -> int:
    if not text.strip():
        return 0
    return len([word for word in re.split(r"\s+", text) if word])


def count_characters(text: str, include_whitespace: bool = True) -> int:
    if not include_whitespace:
        text = re.sub(r"\s+", "", text)
    return len(text)


def count_sentences(text: str) -> int:
    if not text.strip():
        return 0

    sentences = re.split(r"(?<![A-Z][a-z]\.)(?<=\S[.!?])\s+", text)
    return len([s for s in sentences if s.strip()])


def count_paragraphs(text: str) -> int:
    if not text.strip():
        return 0
    paragraphs = re.split(r"\n\s*\n", text)
    return len([p for p in paragraphs if p.strip()])


def remove_extra_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_html_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def extract_emails(text: str) -> List[str]:
    email_regex = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    return re.findall(email_regex, text)


def extract_urls(text: str) -> List[str]:
    url_regex = r'https?://[^\s\n"]+'
    return re.findall(url_regex, text)


def extract_hashtags(text: str) -> List[str]:
    return re.findall(r"#(\w+)", text)


def extract_mentions(text: str) -> List[str]:
    return re.findall(r"@(\w+)", text)


def generate_lorem_ipsum(
    paragraphs: int = 3,
    sentences_per_paragraph: int = 3,
    words_per_sentence: Tuple[int, int] = (5, 15),
    start_with_lorem: bool = True,
) -> str:
    lorem_words = [
        "lorem",
        "ipsum",
        "dolor",
        "sit",
        "amet",
        "consectetur",
        "adipiscing",
        "elit",
        "sed",
        "do",
        "eiusmod",
        "tempor",
        "incididunt",
        "ut",
        "labore",
        "et",
        "dolore",
        "magna",
        "aliqua",
        "ut",
        "enim",
        "ad",
        "minim",
        "veniam",
        "quis",
        "nostrud",
        "exercitation",
        "ullamco",
        "laboris",
        "nisi",
        "ut",
        "aliquip",
        "ex",
        "ea",
        "commodo",
        "consequat",
        "duis",
        "aute",
        "irure",
        "dolor",
        "in",
        "reprehenderit",
        "in",
        "voluptate",
        "velit",
        "esse",
        "cillum",
        "dolore",
        "eu",
        "fugiat",
        "nulla",
        "pariatur",
        "excepteur",
        "sint",
        "occaecat",
        "cupidatat",
        "non",
        "proident",
        "sunt",
        "in",
        "culpa",
        "qui",
        "officia",
        "deserunt",
        "mollit",
        "anim",
        "id",
        "est",
        "laborum",
    ]

    result = []

    if start_with_lorem and paragraphs > 0:
        lorem_start = (
            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
            "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. "
            "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris."
        )
        result.append(lorem_start)
        paragraphs -= 1

    for _ in range(paragraphs):
        paragraph = []
        for _ in range(sentences_per_paragraph):
            word_count = random.randint(*words_per_sentence)
            sentence_words = random.sample(lorem_words, min(word_count, len(lorem_words)))
            if sentence_words:
                sentence_words[0] = sentence_words[0].capitalize()
            sentence = " ".join(sentence_words) + "."
            paragraph.append(sentence)

        result.append(" ".join(paragraph))

    return "\n\n".join(result)
