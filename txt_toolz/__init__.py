from .strings import (
    to_snake_case,
    to_camel_case,
    normalize_whitespace,
    count_words,
    reverse,
    is_palindrome,
    strip_punctuation,
    dedent,
)
from .files import (
    read_text,
    write_text,
    append_text,
    read_lines,
    write_lines,
)
from .advanced import (
    tokenize,
    tokenize_sentences,
    ngrams,
    contains,
    find_all,
    simple_stem,
    stream_read,
)

__all__ = [
    "to_snake_case",
    "to_camel_case",
    "normalize_whitespace",
    "count_words",
    "reverse",
    "is_palindrome",
    "strip_punctuation",
    "dedent",
    "read_text",
    "write_text",
    "append_text",
    "read_lines",
    "write_lines",
    "tokenize",
    "tokenize_sentences",
    "ngrams",
    "contains",
    "find_all",
    "simple_stem",
    "stream_read",
]
from .nlp import (
    load_stopwords,
    remove_stopwords,
    token_freq,
    build_vocab,
    bow_vector,
    tf,
    idf,
    tfidf,
    cosine_similarity,
    extract_keywords,
)

__all__ += [
    "load_stopwords",
    "remove_stopwords",
    "token_freq",
    "build_vocab",
    "bow_vector",
    "tf",
    "idf",
    "tfidf",
    "cosine_similarity",
    "extract_keywords",
]
__all__ += [
    "tfidf_vector",
    "tfidf_matrix",
    "cosine_similarity_matrix",
    "search_similar",
    "vectorize_docs",
]
from .extra import (
    align,
    wrap,
    convert_camel_to_snake,
    remove_non_alphanumeric,
    remove_non_alphabetic,
    is_word,
    lcount_words,
    count_sentences,
)

__all__ += [
    "align",
    "wrap",
    "convert_camel_to_snake",
    "remove_non_alphanumeric",
    "remove_non_alphabetic",
    "is_word",
    "lcount_words",
    "count_sentences",
]
