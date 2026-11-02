class Style:
    Reset = "\33[0m"
    Bold = "\33[1m"
    Curl = "\33[4m"
    Blink = "\33[5m"
    OtherBlink = "\33[6m"
    Selected = "\33[7m"
    Italic = "\33[3m"


class Background:
    Reset = "\33[0m"
    Black = "\33[40m"
    Red = "\33[41m"
    Green = "\33[42m"
    Yellow = "\33[43m"
    Cyan = "\33[46m"
    Blue = "\33[44m"
    Violet = "\33[45m"
    White = "\33[47m"
    Grey = "\33[100m"
    LightRed = "\33[101m"
    LightGreen = "\33[102m"
    LightYellow = "\33[103m"
    LightBlue = "\33[104m"
    Pink = "\33[105m"
    LightCyan = "\33[106m"
    BetterWhite = "\33[107m"


class Color:
    Reset = "\33[0m"
    Black = "\33[30m"
    Red = "\33[31m"
    Green = "\33[32m"
    Yellow = "\33[33m"
    Cyan = "\33[36m"
    Blue = "\33[34m"
    Violet = "\33[35m"
    White = "\33[37m"
    Grey = "\33[90m"
    LightRed = "\33[91m"
    LightGreen = "\33[92m"
    LightYellow = "\33[93m"
    LightBlue = "\33[94m"
    Pink = "\33[95m"
    LightCyan = "\33[96m"
    BetterWhite = "\33[97m"


def RgbColorText(r, g, b, text):
    return "\033[38;2;{};{};{}m{}\033[38;2;255;255;255m".format(r, g, b, text)


def RgbColor(r, g, b):
    return "\033[38;2;{};{};{}m".format(r, g, b)
