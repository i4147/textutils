import torch
import torch.nn as nn
from torch.autograd import Variable
import collections


class strLabelConverterForAttention(object):
    def __init__(self, alphabet, sep):
        self._scanned_list = False
        self._out_of_list = ""
        self._ignore_case = True
        self.sep = sep
        self.alphabet = alphabet.split(sep)

        self.dict = {}
        for i, item in enumerate(self.alphabet):
            self.dict[item] = i

    def scan(self, text):
        # print(text)
        text_tmp = text
        text = []
        for i in range(len(text_tmp)):
            text_result = ""
            for j in range(len(text_tmp[i])):
                chara = text_tmp[i][j].lower() if self._ignore_case else text_tmp[i][j]
                if chara not in self.alphabet:
                    if chara in self._out_of_list:
                        continue
                    else:
                        self._out_of_list += chara
                        file_out_of_list = open("out_of_list.txt", "a+")
                        file_out_of_list.write(chara + "\n")
                        file_out_of_list.close()
                        print('" %s " is not in alphabet...' % chara)
                        continue
                else:
                    text_result += chara
            text.append(text_result)
        text_result = tuple(text)
        self._scanned_list = True
        return text_result

    def encode(self, text, scanned=True):
        self._scanned_list = scanned
        if not self._scanned_list:
            text = self.scan(text)

        if isinstance(text, str):
            text = [self.dict[char.lower() if self._ignore_case else char] for char in text]
            length = [len(text)]
        elif isinstance(text, collections.Iterable):
            length = [len(s) for s in text]
            text = "".join(text)
            text, _ = self.encode(text)
        return (torch.LongTensor(text), torch.LongTensor(length))

    def decode(self, t, length):
        if length.numel() == 1:
            length = length[0]
            assert t.numel() == length, "text with length: {} does not match declared length: {}".format(
                t.numel(), length
            )
            return "".join([self.alphabet[i] for i in t])
        else:
            assert t.numel() == length.sum(), "texts with length: {} does not match declared length: {}".format(
                t.numel(), length.sum()
            )
            texts = []
            index = 0
            for i in range(length.numel()):
                l = length[i]
                texts.append(self.decode(t[index : index + l], torch.LongTensor([l])))
                index += l
            return texts


class averager(object):
    def __init__(self):
        self.reset()

    def add(self, v):
        if isinstance(v, Variable):
            count = v.data.numel()
            v = v.data.sum()
        elif isinstance(v, torch.Tensor):
            count = v.numel()
            v = v.sum()

        self.n_count += count
        self.sum += v

    def reset(self):
        self.n_count = 0
        self.sum = 0

    def val(self):
        res = 0
        if self.n_count != 0:
            res = self.sum / float(self.n_count)
        return res


def loadData(v, data):
    v.data.resize_(data.size()).copy_(data)
