import random
from typing import Any
from pathlib import Path
from rich.console import Console
from pycooltext.chars import CHARS


def vprint(x: Any, verbose: bool = True) -> None:
    if verbose:
        Console().print(x)


def colorize(text: str) -> str:
    text = list(text)
    colorized_text = list()
    for i in text:
        random_color = random.choice([
            "blue3",
            "blue1",
            "deep_sky_blue4",
            "dodger_blue3",
            "dodger_blue2",
            "deep_sky_blue3",
            "dark_red",
        ])
        colorized_text.append(f"[{random_color}]{i}[/{random_color}]")
    return "".join(colorized_text)


def cooltext(text: str) -> None:
    text = text.upper()
    assert len(set(text).difference(set(CHARS.keys()))) == 0
    unordered_text = list()
    for char in text:
        unordered_text.append(CHARS[char])
    ordered_text = [[], [], [], [], []]
    for char in unordered_text:
        splitchar = char.split("\n")
        for i in range(5):
            ordered_text[i].append(splitchar[i])
    for i in range(5):
        ordered_text[i].append("\n")
        ordered_text[i] = "".join(ordered_text[i])
    ordered_text = "".join(ordered_text)
    colored_text = colorize(ordered_text)
    print()
    vprint(colored_text)
