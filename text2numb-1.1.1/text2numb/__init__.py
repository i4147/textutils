version = "1.1.1"
author = "PigeonNation (+ Others >> See code for more)"
import string
from base64 import b16encode, b16decode
import sys

max_before_setup = sys.get_int_max_str_digits()
digs = string.digits + string.ascii_letters


def setup(maxdigits=900000000):
    sys.set_int_max_str_digits(maxdigits)


setup()


def _int2base(x, base):
    global digs
    """Convert an integer to a base ranging from 2-36. Used only by the program converting to base 16. See code for Credits. """
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1
    x *= sign
    digits = []
    while x:
        digits.append(digs[x % base])
        x = x // base
    if sign < 0:
        digits.append("-")
    digits.reverse()
    return "".join(digits)


def _enc_num(string):
    es = string.encode()
    bes = b16encode(es)
    ees = bes.decode()
    return int(ees, 16)


def _dec_num(integer):
    vf = _int2base(integer, 16)
    vf = vf.upper()
    vf = vf.encode()
    bs = b16decode(vf)
    return bs.decode()


def text2numb(string):
    return _enc_num(string)


def numb2text(integer):
    return _dec_num(integer)


__all__ = {
    "setup": setup,
    "text2numb": text2numb,
    "numb2text": numb2text,
    "max_before_setup": max_before_setup,
    "digs": digs,
    "version": version,
    "author": author,
}


def test():
    print("# ======= TESTING ======= #")
    print("Int2Base Test:", _int2base(14, 9))
    print("Input String:\t\t Hello, world!")
    num = text2numb("Hello, world!")
    print("Number Generated:\t", num)
    txt = numb2text(num)
    print("Final Result\t\t", txt)
    print()
    print("Text == Input? ")
    if txt == "Hello, world!":
        print("Checked ... True!!")
    else:
        print("Error! Text != Input!")
    print("# ======= TESTING ======= #")
    print()
    print("# ======= STATS ======= #")
    print("Variables:")
    print("MaxBF:   ", max_before_setup)
    print("Digs:    ", digs)
    print("Version: ", version)
    print("Author:  ", author)
    print("# ======= STATS ======= #")
    print()
    print("Final Result: ----------  ")
    print()
    print("😀😀 Yay! 👍👍 ")
    print("Run Succeeded!")
    print("------------------------  ")


if __name__ == "__main__":
    test()
