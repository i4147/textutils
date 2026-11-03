from dataclasses import dataclass
from typing import Literal


@dataclass
class NormalizerConfig:
    lang: Literal["auto", "de", "en", "es", "fr", "id", "ja", "ko", "pt", "ru", "tl", "vi", "zh"] = "auto"
    operator: Literal["tn", "itn"] = "tn"
    traditional_to_simple: bool = False
    full_to_half: bool = False
    remove_interjections: bool = False
    remove_puncts: bool = False
    tag_oov: bool = False
    enable_0_to_9: bool = False
    remove_erhua: bool = False
