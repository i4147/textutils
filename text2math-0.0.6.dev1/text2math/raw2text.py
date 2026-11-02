__title__ = "text2math"
__author__ = "Steven Cutting"
__author_email__ = "steven.e.cutting@linux.com"
__created_on__ = "02/13/2016"
__copyright__ = "text2math Copyright (C) 2016  Steven Cutting"
import sys

try:
    import cytoolz as tlz
except ImportError:
    import toolz as tlz
c_map = tlz.curry(tlz.map)
try:
    import cchardet as chardet
except:
    import chardet
from unidecode import unidecode
import ftfy

if sys.version_info[0] < 3:
    _STRINGTYPES = (basestring,)
else:
    unicode = str
    _STRINGTYPES = (str, bytes)


def verify_unicode(text):
    assert isinstance(text, unicode)
    return text


def verify_bytestring(text):
    assert isinstance(text, _STRINGTYPES)
    assert not isinstance(text, unicode)
    return text


def clean_unicode(text):
    return ftfy.fix_text(text, normalization="NFKC")


def normize_text(text):
    return tlz.pipe(text, verify_unicode, unidecode, unicode)


def std_decode(text, encoding="utf-8", errors="strict"):
    return tlz.pipe(text, verify_bytestring, lambda txt: txt.decode(encoding=encoding, errors=errors))


def guess_encoding(text):
    return chardet.detect(text).get("encoding")


@tlz.curry
def adv_decode(text, encoding="utf-8", errors="strict"):
    if isinstance(text, unicode):
        return text
    else:
        try:
            return std_decode(text, encoding=encoding, errors=errors)
        except (UnicodeDecodeError, LookupError):
            guessed_encoding = guess_encoding(text)
            if (errors == "replace") and (encoding == guess_encoding):
                raise
            return std_decode(text, encoding=guessed_encoding, errors="replace")


def decode_and_fix(text, encoding="utf-8"):
    return tlz.pipe(text, adv_decode(encoding=encoding), clean_unicode, normize_text)
