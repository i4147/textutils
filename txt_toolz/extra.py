l
import re
from textwrap import wrap as _wrap

_first_cap_re = re.compile("(.)([A-Z][a-z]+)")
_all_cap_re = re.compile("([a-z0-9])([A-Z])")
ENDINGS = [".", "!", "?", ";"]


def align(text, width, side="left"):
    if side.lower()[0] == "c":
        return text.center(width)
    elif side.lower()[0] == "r":
        return text.rjust(width)
    else:
        return text.ljust(width)


def convert_camel_to_snake(string, remove_non_alphanumeric=True):
    if remove_non_alphanumeric:
        string = remove_non_alpha(string, replace_with="_", keep_underscore=True)
    s1 = _first_cap_re.sub(r"\1_\2", string)
    result = _all_cap_re.sub(r"\1_\2", s1).lower()
    result = re.sub(pattern=r"\s*_+", repl="_", string=result)
    return result


def count_sentences(text):
    text = text.strip()
    if len(text) == 0:
        return 0
    split_result = None
    for ending in ENDINGS:
        separator = f"{ending} "
        if split_result is None:
            split_result = text.split(separator)
        else:
            split_result = [y for x in split_result for y in x.split(separator)]
    last_is_sentence = text[-1] in ENDINGS
    return len(split_result) - 1 + last_is_sentence


def is_word(s):
    if not isinstance(s, str):
        raise TypeError(f"{s} if of type {type(s)}")
    return any([character.isalpha() for character in s])


def count_words(text):
    if not isinstance(text, str):
        raise TypeError(f"{text} if of type {type(text)}")
    return len([s for s in text.split() if is_word(s)])


def remove_non_alphanumeric(s, replace_with="_", keep_underscore=True):
    s = str(s)
    s = re.sub(r"&+", "&", s)
    s = s.replace(" & ", " and ")
    s = s.replace("_&_", "_and_")
    s = s.replace("&", " and ")
    if keep_underscore:
        return re.sub(r"[\W]+", replace_with, s, flags=re.UNICODE)
    else:
        return re.sub(r"[\W_]+", replace_with, s, flags=re.UNICODE)


def remove_non_alphabetic(s):
    return "".join([i for i in s if i.isalpha()])


def wrap(
    text,
    max_width,
    align="left",
    indentation="",
    prefix="",
    suffix="",
    left_margin=0,
    right_margin=0,
):
    remaining_width = max_width - len(indentation) - len(prefix) - len(suffix) - left_margin - right_margin
    inside_width = max_width - len(prefix) - len(suffix)
    return "\n".join([
        prefix
        + align_text(
            text=f"{' ' * left_margin}{indentation}{line}{' ' * right_margin}",
            width=inside_width,
            side=align,
        )
        + suffix
        for line in _wrap(text=text, width=remaining_width)
    ])
