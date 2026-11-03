import re
import random
from artext import utils
from artext.utils import log
class WordNoiser():
    def __init__(self):
        self.vowel_pairs = re.compile(r'([aeiou][aeiou])')
        self.consonant_pairs = re.compile(r'(gh)|(ng)|(gn)|(th)|(ou)|(sc)')
    def noise_word(self, word):
        rand = random.random()
        wlen = len(word)
        if wlen > 7 and rand <= 0.25:
            injections = 3
        elif wlen > 5 and rand <= 0.50:
            injections = 2
        else:
            injections = 1
        uword = word
        rand = random.random()
        if rand >= 0.75:
            rand = random.random()
            if rand <= 0.75:
                uword = uword.lower()
            else:
                uword = uword.capitalize()
        for _ in range(injections):
            rand = random.random()
            if rand <= 0.20:
                uword = self.drop_char(uword)
            elif rand <= 0.45:
                uword = self.add_char(uword)
            elif rand <= 0.55:
                uword = self.repeat_char(uword)
            elif rand <= 0.85:
                uword = self.flip_chars(uword)
            elif rand <= 0.95:
                uword = self.swap_chars(uword)
            else:
                pass
        if word == uword:
            return self.noise_word(word)
        return uword
    def drop_char(self, word):
        pos = utils.rand_index(word)
        if pos == 0:
            pos += 1
        uword = word[:pos] + word[pos+1:]
        log.debug("[drop char] {} -> {}: %s".format(word, uword))
        return uword
    def add_char(self, word):
        pos = utils.rand_index(word)
        addition = random.choice(list(word+'aeiou'))
        uword = word[:pos] + addition + word[pos:]
        log.debug("[add char] {} -> {}: %s".format(word, uword))
        return uword
    def repeat_char(self, word):
        pos = utils.rand_index(word)
        uword = word[:pos] + word[pos] + word[pos:]
        log.debug("[repeat char] {} -> {}: %s".format(word, uword))
        return uword
    def flip_chars(self, word):
        uword = self.flip_vowel_pairs(word)
        if not uword:
            uword = self.flip_consonant_pairs(word)
            if not uword:
                uword = self.flip_rand_pairs(word)
        log.debug("[flip char] {} -> {}: %s".format(word, uword))
        return uword
    def flip_vowel_pairs(self, word):
        vowels = self.vowel_pairs.findall(word)
        if not len(vowels):
            return None
        if len(vowels) > 1:
            vowels = random.sample(vowels, 1)
        pair = vowels[0]
        uword = word.replace(pair, pair[::-1], 1)
        return uword
    def flip_consonant_pairs(self, word):
        idxs = [m.start() for m in self.consonant_pairs.finditer(word)]
        if not len(idxs):
            return None
        if len(idxs) > 1:
            idxs = random.sample(idxs, 1)
        idx = idxs[0]
        uword = word[:idx] + word[idx+1] + word[idx] + \
            (word[idx+2:] if len(word) > idx+1 else '')
        return uword
    def flip_rand_pairs(self, word):
        pos = utils.rand_index(word)
        i, j = (pos - 1, pos) if pos > 0 else (pos, pos + 1)
        uword = word[:i] + word[j] + word[i] + word[j + 1:]
        return uword
    def swap_chars(self, word):
        i, j = utils.rand_index(word), utils.rand_index(word)
        if i > j:
            i, j = j, i
        uword = word[:i] + word[j] + word[i + 1:j] + word[i] + word[j + 1:]
        log.debug("[swap char] {} -> {}: %s".format(word, uword))
        return uword
