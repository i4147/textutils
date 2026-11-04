from texting.enum.regexes import CAPWORD, INILOW, WORD


def camel_to_snake(phrase, de="-"):
    ph = ""
    try:
        iterator = CAPWORD.finditer(phrase)
        if (ms := INILOW.match(phrase)) or (ms := iterator.__next__()):
            wd = ms.group()
            ph = wd.lower()
        for ms in iterator:
            wd = ms.group()
            ph += de + wd.lower()
    except StopIteration:
        pass
    return ph


def snake_to_camel(dashed, de=""):
    ph = ""
    try:
        iterator = WORD.finditer(dashed)
        if ms := iterator.__next__():
            wd = ms.group()
            ph = wd.lower()
        for ms in iterator:
            wd = ms.group()
            ph += de + wd.title()
    except StopIteration:
        pass
    return ph


def snake_to_pascal(dashed, de=""):
    return de.join([ms.group().title() for ms in WORD.finditer(dashed)])
