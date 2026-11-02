class ANSI:
    STOP = 0
    CODE = ""

    def __init__(self, text: str):
        self.text = str(text)

    def __repr__(self):
        return f"\033[{self.CODE}m{self.text}\033[{self.STOP}m"

    def __add__(self, other):
        return str(self) + str(other)

    def __radd__(self, other):
        return str(other) + str(self)


class RGB(ANSI):
    def __init__(self, text, r, g=None, b=None):
        self.text = str(text)
        self.r = r
        self.g = g
        self.b = b

    def __repr__(self):
        if self.g is not None and self.b is not None:
            return f"\033[{self.CODE};2;{self.r};{self.g};{self.b}m{self.text}\033[{self.STOP}m"
        else:
            return f"\033[{self.CODE};5;{self.r}m{self.text}\033[{self.STOP}m"


class Reset(ANSI):
    CODE = 0
    STOP = 0


class Bold(ANSI):
    CODE = 1
    STOP = 22


class Faint(ANSI):
    CODE = 2
    STOP = 22


class Italic(ANSI):
    CODE = 3
    STOP = 23


class Underline(ANSI):
    CODE = 4
    STOP = 24


class SlowBlink(ANSI):
    CODE = 5
    STOP = 25


class FastBlink(ANSI):
    CODE = 6
    STOP = 25


class Invert(ANSI):
    CODE = 7
    STOP = 27


class Conceal(ANSI):
    CODE = 8
    STOP = 28


class Strikethrough(ANSI):
    CODE = 9
    STOP = 29


class DoubleUnderline(ANSI):
    CODE = 21
    STOP = 24


class ProportionalSpacing(ANSI):
    CODE = 26
    STOP = 50


class Overline(ANSI):
    CODE = 53
    STOP = 55


class UnderlineColor(ANSI):
    CODE = 58
    STOP = 59


class Superscript(ANSI):
    CODE = 73
    STOP = 75


class Subscript(ANSI):
    CODE = 74
    STOP = 75


class Font0(ANSI):
    CODE = 10
    STOP = 10


class Font1(ANSI):
    CODE = 11
    STOP = 10


class Font2(ANSI):
    CODE = 12
    STOP = 10


class Font3(ANSI):
    CODE = 13
    STOP = 10


class Font4(ANSI):
    CODE = 14
    STOP = 10


class Font5(ANSI):
    CODE = 15
    STOP = 10


class Font6(ANSI):
    CODE = 16
    STOP = 10


class Font7(ANSI):
    CODE = 17
    STOP = 10


class Font8(ANSI):
    CODE = 18
    STOP = 10


class Font9(ANSI):
    CODE = 19
    STOP = 10


class FrakturFont(ANSI):
    CODE = 20
    STOP = 10


class Black(ANSI):
    CODE = 30
    STOP = 39


class Red(ANSI):
    CODE = 31
    STOP = 39


class Green(ANSI):
    CODE = 32
    STOP = 39


class Yellow(ANSI):
    CODE = 33
    STOP = 39


class Blue(ANSI):
    CODE = 34
    STOP = 39


class Magenta(ANSI):
    CODE = 35
    STOP = 39


class Cyan(ANSI):
    CODE = 36
    STOP = 39


class White(ANSI):
    CODE = 37
    STOP = 39


class BrightBlack(ANSI):
    CODE = 90
    STOP = 39


class BrightRed(ANSI):
    CODE = 91
    STOP = 39


class BrightGreen(ANSI):
    CODE = 92
    STOP = 39


class BrightYellow(ANSI):
    CODE = 93
    STOP = 39


class BrightBlue(ANSI):
    CODE = 94
    STOP = 39


class BrightMagenta(ANSI):
    CODE = 95
    STOP = 39


class BrightCyan(ANSI):
    CODE = 96
    STOP = 39


class BrightWhite(ANSI):
    CODE = 97
    STOP = 39


class RGBColor(RGB):
    CODE = 38
    STOP = 39


class BgBlack(ANSI):
    CODE = 40
    STOP = 49


class BgRed(ANSI):
    CODE = 41
    STOP = 49


class BgGreen(ANSI):
    CODE = 42
    STOP = 49


class BgYellow(ANSI):
    CODE = 43
    STOP = 49


class BgBlue(ANSI):
    CODE = 44
    STOP = 49


class BgMagenta(ANSI):
    CODE = 45
    STOP = 49


class BgCyan(ANSI):
    CODE = 46
    STOP = 49


class BgWhite(ANSI):
    CODE = 47
    STOP = 49


class BgBrightBlack(ANSI):
    CODE = 100
    STOP = 49


class BgBrightRed(ANSI):
    CODE = 101
    STOP = 49


class BgBrightGreen(ANSI):
    CODE = 102
    STOP = 49


class BgBrightYellow(ANSI):
    CODE = 103
    STOP = 49


class BgBrightBlue(ANSI):
    CODE = 104
    STOP = 49


class BgBrightMagenta(ANSI):
    CODE = 105
    STOP = 49


class BgBrightCyan(ANSI):
    CODE = 106
    STOP = 49


class BgBrightWhite(ANSI):
    CODE = 107
    STOP = 49


class RGBBgColor(RGB):
    CODE = 48
    STOP = 49


class Framed(ANSI):
    CODE = 51
    STOP = 54


class Encircled(ANSI):
    CODE = 52
    STOP = 54


class IdeogramUnderline(ANSI):
    CODE = 60
    STOP = 65


class IdeogramDoubleUnderline(ANSI):
    CODE = 61
    STOP = 65


class IdeogramOverline(ANSI):
    CODE = 62
    STOP = 65


class IdeogramDoubleOverline(ANSI):
    CODE = 63
    STOP = 65


class IdeogramStressMarking(ANSI):
    CODE = 64
    STOP = 65
