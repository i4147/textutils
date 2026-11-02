import importlib
from .ANSI_effects import *


def demo_all() -> None:
    all_classes = [
        "Reset",
        "Bold",
        "Faint",
        "Italic",
        "Underline",
        "SlowBlink",
        "FastBlink",
        "Invert",
        "Conceal",
        "Strikethrough",
        "Font0",
        "Font1",
        "Font2",
        "Font3",
        "Font4",
        "Font5",
        "Font6",
        "Font7",
        "Font8",
        "Font9",
        "FrakturFont",
        "DoubleUnderline",
        "ProportionalSpacing",
        "Black",
        "Red",
        "Green",
        "Yellow",
        "Blue",
        "Magenta",
        "Cyan",
        "White",
        "RGBColor",
        "BgBlack",
        "BgRed",
        "BgGreen",
        "BgYellow",
        "BgBlue",
        "BgMagenta",
        "BgCyan",
        "BgWhite",
        "RGBBgColor",
        "Framed",
        "Encircled",
        "Overline",
        "UnderlineColor",
        "IdeogramUnderline",
        "IdeogramDoubleUnderline",
        "IdeogramOverline",
        "IdeogramDoubleOverline",
        "IdeogramStressMarking",
        "Superscript",
        "Subscript",
        "BrightBlack",
        "BrightRed",
        "BrightGreen",
        "BrightYellow",
        "BrightBlue",
        "BrightMagenta",
        "BrightCyan",
        "BrightWhite",
        "BgBrightBlack",
        "BgBrightRed",
        "BgBrightGreen",
        "BgBrightYellow",
        "BgBrightBlue",
        "BgBrightMagenta",
        "BgBrightCyan",
        "BgBrightWhite",
    ]
    module = importlib.import_module(".ANSI_effects", __package__)
    print("fansi_text demo")
    print("===============")
    for name in all_classes:
        func = getattr(module, name)
        if callable(func):
            if name in ["RGBColor", "RGBBgColor"]:
                text = name + "(text, 172, 100, 112)"
                result = func(text, 172, 100, 112)
            else:
                result = func(name + "()")
            print(result)
