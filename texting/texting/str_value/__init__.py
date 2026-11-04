def v1(word):
    return (ord(word[0].lower()) & 0x7F) << 21


def v2(word):
    word = word.lower()
    return ((ord(word[0]) & 0x7F) << 21) + ((ord(word[1]) & 0x7F) << 14)


def v3(word):
    word = word.lower()
    return ((ord(word[0]) & 0x7F) << 21) + ((ord(word[1]) & 0x7F) << 14) + ((ord(word[2]) & 0x7F) << 7)


def v4(word):
    word = word.lower()
    return (
        ((ord(word[0]) & 0x7F) << 21)
        + ((ord(word[1]) & 0x7F) << 14)
        + ((ord(word[2]) & 0x7F) << 7)
        + (ord(word[3]) & 0x7F)
    )


def str_value(word):
    if not isinstance(word, str):
        return None
    size = len(word)
    if not size:
        return None
    if size >= 8:
        return (v4(word[:4]) << 2) + v4(word[-4:])
    if size == 7:
        return (v4(word[:4]) << 2) + v3(word[-3:])
    if size == 6:
        return (v4(word[:4]) << 2) + v2(word[-2:])
    if size == 5:
        return (v4(word[:4]) << 2) + v1(word[-1:])
    if size == 4:
        return v4(word) << 2
    if size == 3:
        return v3(word) << 2
    if size == 2:
        return v2(word) << 2
    if size == 1:
        return v1(word) << 2
