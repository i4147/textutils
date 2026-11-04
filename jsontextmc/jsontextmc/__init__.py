# coding=utf-8
# encoding=utf-8
# pylint: disable=W0311

from __future__ import annotations

import re

__version__: str = "3.1.0"


def tokenize(sectioned: str, separator: str = "\xa7") -> list[str]:
    return re.split(
        rf"(?P<r>{separator}[x#][0-9a-f]{{6}}|{separator}[0-9a-frk-o])",
        sectioned,
        flags=re.IGNORECASE | re.UNICODE,
    )


COLORS: dict[str:str] = {
    "0": "black",
    "1": "dark_blue",
    "2": "dark_green",
    "3": "dark_aqua",
    "4": "dark_red",
    "5": "dark_purple",
    "6": "gold",
    "7": "gray",
    "8": "dark_gray",
    "9": "blue",
    "a": "green",
    "b": "aqua",
    "c": "red",
    "d": "light_purple",
    "e": "yellow",
    "f": "white",
    "r": "reset",
}

COLORS_REVERSED: dict[str:str] = {v: k for k, v in COLORS.items()}

FORMATS: dict[str:str] = {
    "k": "obfuscated",
    "l": "bold",
    "m": "strikethrough",
    "n": "underlined",
    "o": "italic",
}

FORMATS_REVERSED: dict[str:str] = {v: k for k, v in FORMATS.items()}

ACCEPTED_FORMATS: str = "0123456789abcdefklmnorx#ABCDEFKLMNORX"


def to_json(
    text: str,
    separator: str = "\xa7",
    strict: bool = False,
    inherit_parent: bool = True,
) -> dict | list | str:
    exported: list = []
    settings: dict = {"color": None, "format": []}
    for part in [x for x in tokenize(text, separator) if x]:
        if len(part) == 2 or len(part) == 8:
            if len(part) == 8 and part[1] in "x#X" and all(c in "0123456789abcdefABCDEF" for c in part[2:8]):
                settings["color"] = f"#{part[2:8].lower()}"
            elif part[1] in "rR":
                settings = {"color": "reset", "format": []}

            elif part[1] in "0123456789abcdefABCDEF":
                settings["color"] = COLORS[part[1].lower()]
            elif part[1] in "klmnoKLMNO":
                if not (strict and not settings["color"]):
                    settings["format"].append(FORMATS[part[1].lower()])

        else:
            if settings["color"] or settings["format"]:
                temp: dict = {"text": part}
                if settings["color"]:
                    temp["color"] = settings["color"]
                if settings["format"]:
                    for option in settings["format"]:
                        temp[option] = True
                exported.append(temp)
            else:
                exported.append(part)
            if not inherit_parent:
                settings = {"color": None, "format": []}
    if len(exported) == 1:
        return exported[0]
    return exported


def from_json(text: dict | list | str, separator: str = "\xa7") -> str:
    exported: str = ""
    if isinstance(text, (dict, list)):
        if isinstance(text, dict):
            text: list = [text]
        for entry in text:
            if len(entry.keys()) >= 2 and "text" in entry:
                if "color" in entry:
                    exported += separator + COLORS_REVERSED[entry["color"].lower()]
                for option in FORMATS_REVERSED.keys():
                    if option in entry:
                        exported += separator + FORMATS_REVERSED[option]
            if "text" in entry:
                exported += entry["text"]
    elif isinstance(text, str):
        return text
    return exported
