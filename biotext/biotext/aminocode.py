"""
This module provides a class with static methods for encoding and decoding
text using aminocode.

methods:
- encode_string: Encodes a string using aminocode.
- decode_string: Decodes a string encoded with aminocode.
- encode_list: Encodes all strings in a list using aminocode.
- decode_list: Decodes all strings in a list encoded with aminocode.
"""

import re
import unicodedata


class aminocode:
    aminocode_table = {
        "a": "YA",
        "b": "E",
        "c": "C",
        "d": "D",
        "e": "YE",
        "f": "F",
        "g": "G",
        "h": "H",
        "i": "YI",
        "j": "I",
        "k": "K",
        "l": "L",
        "m": "M",
        "n": "N",
        "o": "YQ",
        "p": "P",
        "q": "Q",
        "r": "R",
        "s": "S",
        "t": "T",
        "u": "YV",
        "v": "V",
        "x": "W",
        "z": "A",
        "w": "YW",
        "y": "YY",
        ".": "YP",
        "9": "YD",
        " ": "YS",
    }

    aminocode_table_d = {
        "0": "YDA",
        "1": "YDQ",
        "2": "YDT",
        "3": "YDH",
        "4": "YDF",
        "5": "YDI",
        "6": "YDS",
        "7": "YDE",
        "8": "YDG",
        "9": "YDN",
    }

    aminocode_table_p = {
        ".": "YPE",
        ",": "YPC",
        ";": "YPS",
        "!": "YPW",
        "?": "YPQ",
        ":": "YPT",
    }

    @staticmethod
    def encode_string(input_string, detail="dp"):

        try:
            input_string = input_string.decode("utf-8")
        except (AttributeError, UnicodeDecodeError):
            pass

        input_string = unicodedata.normalize("NFKD", input_string)
        input_string = "".join([c for c in input_string if not unicodedata.combining(c)])

        input_string = input_string.lower()

        input_string = re.sub(r"\s", " ", input_string)

        c_dict = aminocode.aminocode_table.copy()

        if "d" in detail:
            c_dict.update(aminocode.aminocode_table_d)
        else:
            input_string = re.sub(r"\d", "9", input_string)

        if "p" in detail:
            c_dict.update(aminocode.aminocode_table_p)
        else:
            input_string = re.sub("[,;!?:]", ".", input_string)

        for i in "".join(set(input_string)):
            if i not in c_dict:
                c_dict[i] = "YK"

        for k, v in c_dict.items():
            input_string = input_string.replace(k, v)

        return input_string

    @staticmethod
    def decode_string(input_string, detail="dp"):

        c_dict = aminocode.aminocode_table.copy()
        if "d" in detail:
            c_dict.update(aminocode.aminocode_table_d)
        if "p" in detail:
            c_dict.update(aminocode.aminocode_table_p)

        c_dict = dict(sorted(c_dict.items(), key=lambda x: (len(x[1]), x[0]), reverse=True))
        input_string = input_string.replace("YK", "-")

        for k, v in c_dict.items():
            input_string = input_string.replace(v, k)

        decoded_string = input_string
        return decoded_string

    @staticmethod
    def encode_list(string_list, detail="dp", verbose=False):

        list_size = len(string_list)
        selectedEncoder = lambda x: aminocode.encode_string(x, detail=detail)

        encoded_list = []
        if verbose:
            print("Encoding text...")
        for c, i in enumerate(string_list):
            seq = selectedEncoder(i)
            encoded_list.append(seq)
            if verbose and (c + 1) % 10000 == 0:
                print(str(c + 1) + "/" + str(list_size))
        if verbose:
            print(str(list_size) + "/" + str(list_size))
        return encoded_list

    @staticmethod
    def decode_list(input_list, detail="dp", verbose=False):

        list_size = len(input_list)
        selectedEncoder = lambda x: aminocode.decode_string(x, detail=detail)

        decoded_list = []
        if verbose:
            print("Decoding text...")
        for c, i in enumerate(input_list):
            c += 1
            if verbose and (c + 1) % 10000 == 0:
                print(str(c + 1) + "/" + str(list_size))
            decoded_list.append(selectedEncoder(str(i)))
        if verbose:
            print(str(list_size) + "/" + str(list_size))

        return decoded_list
