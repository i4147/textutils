"""Text processing utilities for Linux."""

from .distance import levenshtein_distance, levenshtein_similarity, lcs_distance, lcs_similarity
from .files import TextFile, iter_text_files, search_files
from .transform import SimpleSentenceTokenizer, SpongeString, leetspeak

__all__ = ["levenshtein_distance", "levenshtein_similarity", "lcs_distance", "lcs_similarity", "TextFile", "iter_text_files", "search_files", "SimpleSentenceTokenizer", "SpongeString", "leetspeak"]
