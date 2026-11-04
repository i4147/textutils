RESET = "\033[0m"
ATTRIBUTES = {"bold": 1, "dark": 2, "underline": 4, "blink": 5, "reverse": 7, "concealed": 8}
textcolors = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "dark_black": 90,
    "dark_red": 91,
    "dark_green": 92,
    "dark_yellow": 93,
    "dark_blue": 94,
    "dark_magenta": 95,
    "dark_cyan": 96,
    "dark_white": 97,
}
background_colors = {
    "black": 40,
    "red": 41,
    "green": 42,
    "yellow": 43,
    "blue": 44,
    "magenta": 45,
    "cyan": 46,
    "white": 47,
    "dark_black": 100,
    "dark_red": 101,
    "dark_green": 102,
    "dark_yellow": 103,
    "dark_blue": 104,
    "dark_magenta": 105,
    "dark_cyan": 106,
    "dark_white": 107,
}


def color(text, textColor=None, backgroundColor=None, attrs=None):
    result = str(text)

    fmt_str = "\033[%dm%s"
    if textColor is not None:
        result = fmt_str % (textcolors[textColor], result)

    if backgroundColor is not None:
        result = fmt_str % (background_colors[backgroundColor], result)

    if attrs is not None:
        for attr in attrs:
            result = fmt_str % (ATTRIBUTES[attr], result)

    result += RESET
    return result


def cprint(text, textColor=None, backgroundColor=None, attrs=None):
    result = str(text)

    fmt_str = "\033[%dm%s"
    if textColor is not None:
        result = fmt_str % (textcolors[textColor], result)

    if backgroundColor is not None:
        result = fmt_str % (background_colors[backgroundColor], result)

    if attrs is not None:
        for attr in attrs:
            result = fmt_str % (ATTRIBUTES[attr], result)

    result += RESET
    print(result)


def colorword(text, backgroundColor="black", bold=True, underline=False):

    text = str(text)
    words = text.split()
    count = 90
    if underline == False:
        if bold == True:
            for i in words:
                print(f"\033[1;{count};{background_colors[backgroundColor]}m" + i, end=" ")
                count += 1
                if count == 98:
                    count = 90
        if bold == False:
            for i in words:
                print(f"\033[0;{count};{background_colors[backgroundColor]}m" + i, end=" ")
                count += 1
                if count == 98:
                    count = 90
        if underline == True:
            if bold == True:
                for i in words:
                    print(f"\033[1;{count};{background_colors[backgroundColor]}m" + i, end=" ")
                    count += 1
                    if count == 98:
                        count = 90
            if bold == False:
                for i in words:
                    print(f"\033[0;{count};{background_colors[backgroundColor]}m" + i, end=" ")
                    count += 1
                    if count == 98:
                        count = 90
