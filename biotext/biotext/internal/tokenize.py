import re


def tokenize(text_list):
    return [re.findall(r"\b\w+\b", text) for text in text_list]
