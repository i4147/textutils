# -*- coding: utf-8 -*-

import jieba
import re

jieba.setLogLevel(log_level="ERROR")


def tokenize_words(text):
    output = []
    sentences = split_2_short_text(text, include_symbol=True)
    for sentence, idx in sentences:
        if is_chinese_string(sentence):
            output.extend(jieba.lcut(sentence))
        else:
            output.extend(whitespace_tokenize(sentence))
    return output


class Tokenizer(object):
    def __init__(self, lower=True):
        self.lower = lower

    def tokenize(self, text):
        res = []
        if len(text) == 0:
            return res

        if self.lower:
            text = text.lower()
        res = tokenize_words(text)
        return res


def split_2_short_text(text, include_symbol=True):
    re_han = re.compile("([\u4e00-\u9f5a-zA-Z0-9+#&]+)", re.U)
    result = []
    blocks = re_han.split(text)
    start_idx = 0
    for blk in blocks:
        if not blk:
            continue
        if include_symbol:
            result.append((blk, start_idx))
        else:
            if re_han.match(blk):
                result.append((blk, start_idx))
        start_idx += len(blk)
    return result


def is_chinese(uchar):
    return "\u4e00" <= uchar <= "\u9fa5"


def is_chinese_string(string):
    return all(is_chinese(c) for c in string)


def whitespace_tokenize(text):
    text = text.strip()
    if not text:
        return []
    tokens = text.split()
    return tokens


if __name__ == "__main__":
    a = "晚上一个人好孤单，想:找附近的人陪陪我."
    b = "unlabeled example, aug_copy_num is the index of the generated augmented. you don't know"

    t = Tokenizer()
    word_list_a = t.tokenize(a + b)
    print("VocabTokenizer-word:", word_list_a)
