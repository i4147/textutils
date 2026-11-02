import re
import unicodedata as udat
import string
import sys
from .unicodes_codes import *
from .stopwords import *

PY2 = int(sys.version[0]) == 2
if PY2:
    from unidecode import unidecode

    TEXT_TYPE = unicode
    BINARY_TYPE = str
    STR_TYPES = (str, unicode)
    IS_CHAR = list(unicode(string.ascii_letters, "utf-8"))
else:
    TEXT_TYPE = str
    BINARY_TYPE = bytes
    unicode = str
    STR_TYPES = (str,)
    IS_CHAR = list(string.ascii_letters)
    basestring = (str, bytes)
    unidecode = str
MAP_CHARS = dict()
MAP_CHARS.update({ord(" "): " "})
for c in IS_CHAR:
    MAP_CHARS.update({ord(unicode(c)): c})
ENCODE = "utf-8"
STR_PUNC = list(string.punctuation)
REGEX_HTML = re.compile(r"<[^>]*>")
REGEX_MENTIONS = re.compile(r"\S*[@](?:\[[^\]]+\]|\S+)")
REGEX_TAGS = re.compile(r"\S*[#](?:\[[^\]]+\]|\S+)")
REGEX_SMILES = re.compile(r"([j|h][aeiou]){3,}")
REGEX_VOWELS = re.compile(r"([aeiou])\1+")
REGEX_CONSONANTS = re.compile(r"([b-df-hj-np-tv-z])\1+")
REGEX_SPACES = re.compile(r" +")
REGEX_URLS = re.compile(
    r"(www|http|https)(?:[a-zA-Z]|[0-9]|[$-_@.&+]|\
[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)
MAP_TILDE = [
    ord("Á"),
    ord("É"),
    ord("Í"),
    ord("Ó"),
    ord("Ú"),
    ord("Ñ"),
    ord("À"),
    ord("È"),
    ord("Ì"),
    ord("Ò"),
    ord("Ù"),
    ord("ç"),
    ord("á"),
    ord("é"),
    ord("í"),
    ord("ó"),
    ord("ú"),
    ord("ñ"),
    ord("à"),
    ord("è"),
    ord("ì"),
    ord("ò"),
    ord("ù"),
    ord("ü"),
    ord("ä"),
    ord("ë"),
    ord("ï"),
    ord("ö"),
    ord("ü"),
    ord("ÿ"),
    ord("Ç"),
]
REGEX_EMOJIS = re.compile("[\U0001f600-\U0001f64f]", re.UNICODE)


class ReTexto:
    @classmethod
    def __init__(self, text):
        self.text = self.is_unicode(text.rstrip())

    @classmethod
    def __repr__(self):
        return self.text

    @staticmethod
    def is_unicode(v, encoding="utf-8"):
        if isinstance(encoding, basestring):
            encoding = ((encoding,),) + (("windows-1252",), (ENCODE, "ignore"))
        if isinstance(v, BINARY_TYPE):
            for e in encoding:
                try:
                    return v.decode(*e)
                except Exception:
                    pass
            return v
        return unicode(v)

    @classmethod
    def remove_html(self, by=""):
        try:
            self.text = re.sub(REGEX_HTML, by, self.text)
            return self
        except Exception as e:
            raise Exception("STR_EXCEPTION")

    @classmethod
    def remove_mentions(self, by=""):
        try:
            self.text = re.sub(REGEX_MENTIONS, by, self.text)
            return self
        except Exception as e:
            raise Exception("STR_EXCEPTION")

    @classmethod
    def remove_tags(self, by=""):
        try:
            self.text = re.sub(REGEX_TAGS, by, self.text)
            return self
        except Exception as e:
            raise Exception("STR_EXCEPTION")

    @classmethod
    def remove_smiles(self, by=""):
        try:
            self.text = re.sub(REGEX_SMILES, by, self.text)
            return self
        except Exception as e:
            raise Exception("STR_EXCEPTION")

    @classmethod
    def remove_punctuation(self, by=""):
        l_text = []
        l_unicodes = set(UNICODE_EMOJI.keys())
        for char in list(self.text):
            if not (char in STR_PUNC):
                l_text.append(char)
                continue
            l_text.append(by)
        self.text = "".join(l_text)
        return self

    @classmethod
    def remove_nochars(self, preserve_tilde=False):
        chars = MAP_CHARS.keys()
        if preserve_tilde:
            chars = list(chars) + MAP_TILDE
        l_char = set(chars)
        l_text = []
        for char in list(self.is_unicode(self.text)):
            if ord(char) in l_char:
                l_text.append(char)
                continue
        self.text = "".join(l_text)
        return self

    @classmethod
    def remove_stopwords(self, lang=None):
        l_text = []
        sw = stopwords(lang)
        for char in self.split_words():
            if not (self.is_unicode(char) in sw):
                l_text.append(char)
        self.text = " ".join(l_text)
        return self

    @classmethod
    def convert_specials(self):
        self.text = unidecode(self.is_unicode(self.text))
        return self

    @classmethod
    def convert_emoji(self):
        text = self.text
        if PY2:
            if not isinstance(text, unicode):
                text = text.decode("utf-8")
            r = re.sub(REGEX_EMOJIS, lambda m: emoji_name(m), text)
            r = r.encode(ENCODE)
        else:
            r = re.sub(REGEX_EMOJIS, lambda m: emoji_name(m), text)
        self.text = r
        return self

    @classmethod
    def remove_url(self, by=""):
        self.text = re.sub(REGEX_URLS, "", self.text)
        return self

    @classmethod
    def remove_duplicate_consonants(self):
        self.text = re.sub(REGEX_CONSONANTS, r"\1", self.text)
        return self

    @classmethod
    def remove_duplicate(self, r="a-z"):
        p = re.compile(r"([%s])\1+" % r)
        self.text = re.sub(p, r"\1", self.text)
        return self

    @classmethod
    def remove_duplicate_vowels(self):
        self.text = re.sub(REGEX_VOWELS, r"\1", self.text)
        return self

    @classmethod
    def remove_multispaces(self):
        self.text = re.sub(REGEX_SPACES, " ", self.text)
        return self

    @classmethod
    def strip_accents(self):
        accents = set(map(udat.lookup, ("COMBINING ACUTE ACCENT", "COMBINING GRAVE ACCENT")))
        txt = [c for c in udat.normalize("NFD", self.text) if c not in accents]
        self.text = udat.normalize("NFC", "".join(txt))
        return self

    @classmethod
    def split_words(self, uniques=False):
        lspl = self.text.split()
        if uniques:
            seen = set()
            lspl = [x for x in lspl if x not in seen and not seen.add(x)]
        return lspl

    @classmethod
    def lower(self):
        self.text = self.text.lower()
        return self
