import re
import unicodedata


def normalize(text: str) -> str:

    text = text.replace("إ", "ا")
    text = text.replace("أ", "ا")
    text = text.replace("آ", "ا")
    text = text.replace("ٱ", "ا")
    text = text.replace("ه", "ة")
    text = text.replace("ة", "ه")
    # text = text.replace("","")

    return text
