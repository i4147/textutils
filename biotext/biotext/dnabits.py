"""
This module provides a class with static methods for encoding and decoding
text using dnabits.

methods:
- encode_string: Encodes a string using dnabits.
- decode_string: Decodes a string encoded with dnabits.
- encode_list: Encodes all strings in a list using dnabits.
- decode_list: Decodes all strings in a list encoded with dnabits.
- str_to_bin: Converts a string to a binary representation.
- bin_to_str: Converts a binary representation to a string.
"""


class dnabits:
    @staticmethod
    def encode_string(input_string):

        input_string = dnabits.str_to_bin(input_string)

        text_0 = input_string[0::2]
        text_1 = input_string[1::2]

        binary_pairs = zip(text_0, text_1)
        dna_chars = {"00": "A", "01": "G", "10": "C", "11": "T"}
        encoded_string = "".join(dna_chars[b0 + b1] for b0, b1 in binary_pairs)

        return encoded_string

    @staticmethod
    def decode_string(input_string):

        dna_to_bin = {"A": "00", "G": "01", "C": "10", "T": "11"}

        binary_string = "".join(dna_to_bin[char] for char in input_string)

        decoded_string = "".join(dnabits.bin_to_str(binary_string[i : i + 8]) for i in range(0, len(binary_string), 8))

        return decoded_string

    @staticmethod
    def encode_list(string_list, verbose=False):

        list_size = len(string_list)
        selectedEncoder = lambda x: dnabits.encode_string(x)

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
    def decode_list(input_list, output_file=None, verbose=False):

        list_size = len(input_list)
        selectedEncoder = lambda x: dnabits.decode_string(x)

        decoded_list = []
        if verbose:
            print("Decoding text...")
        for c, i in enumerate(input_list):
            c += 1
            if verbose and (c + 1) % 10000 == 0:
                print(str(c + 1) + "/" + str(list_size))
            decoded_list.append((selectedEncoder(str(i))))
        if verbose:
            print(str(list_size) + "/" + str(list_size))

        return decoded_list

    @staticmethod
    def str_to_bin(string):
        return "".join(f"{ord(char):08b}"[::-1] for char in string)

    @staticmethod
    def bin_to_str(string):
        res = ""
        for idx in range(int(len(string) / 8)):
            cstr = string[idx * 8 : (idx + 1) * 8]
            cstr = cstr[::-1]
            tmp = chr(int(cstr, 2))
            res += tmp
        return res
