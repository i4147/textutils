from dataclasses import dataclass
from typing import Literal


@dataclass
class NormalizerConfig:
    """Configuration for text normalization."""

    lang: Literal["auto", "en", "zh"] = "auto"
    """Language of the input text ('auto' for automatic detection)."""

    operator: Literal["tn", "itn"] = "tn"
    """Normalization operator: 'tn' (text normalization) or 'itn' (inverse text normalization)."""

    fix_contractions: bool = False
    """Whether to fix English contractions (e.g., "don't" -> "do not")."""

    traditional_to_simple: bool = False
    """Convert traditional Chinese characters to simplified Chinese."""

    full_to_half: bool = False
    """Convert full-width characters (e.g., "Ａ") to half-width (e.g., "A")."""

    remove_interjections: bool = False
    """Remove interjections (e.g., "um", "ah")."""

    remove_puncts: bool = False
    """Remove all punctuation marks."""

    tag_oov: bool = False
    """Tag out-of-vocabulary words with a special marker."""

    enable_0_to_9: bool = False
    """Convert numbers to words (e.g., "1" -> "one") during ITN."""

    remove_erhua: bool = False
    """Remove 'erhua' suffixes in Chinese (e.g., "哪儿" -> "哪")."""
