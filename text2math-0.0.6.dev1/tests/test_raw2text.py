# -*- coding: utf-8 -*-
__title__ = "text2math"
__author__ = "Steven Cutting"
__author_email__ = "steven.e.cutting@linux.com"
__created_on__ = "02/13/2016"
__copyright__ = "text2math Copyright (C) 2016  Steven Cutting"

from operator import eq

import pytest

try:
    import cytoolz as tlz
except ImportError:
    import toolz as tlz
c_eq = tlz.curry(eq)

from text2math import raw2text

from utils import osx_xfail

# TODO (steven_c) Find out why km/h test fails only on OSX.


# @pytest.mark.parametrize("string,expected",
#                          [("<p>foo<\p><li>bar<\li>", "foobar"),
#                           ])
# def test__remove_html_bits(string, expected):
#     assert(tlz.pipe(string,
#                     raw2text.remove_html_bits,
#                     c_eq(expected)))


def test__verify_unicode_fail():
    with pytest.raises(AssertionError):
        raw2text.verify_unicode(b"not unicode")


def test__verify_unicode_pass():
    raw2text.verify_unicode("unicode")


@pytest.mark.parametrize(
    "wrong_arg",
    [
        ("not bytestring"),
        (2344352),
        ([b"sfsddf", b"sfsdf"]),
        ([b"sfsddf"]),
    ],
)
def test__verify_bytestring_fail(wrong_arg):
    with pytest.raises(AssertionError):
        raw2text.verify_bytestring(wrong_arg)


def test__verify_bytestring_pass():
    raw2text.verify_bytestring(b"bytestring")


# Examples from https://github.com/LuminosoInsight/python-ftfy
@pytest.mark.parametrize(
    "string,expected",
    [
        ("This text should be in â€œquotesâ€\x9d.", 'This text should be in "quotes".'),
        # expected to fail on OSX
        osx_xfail(("30 \U0001d5c4\U0001d5c6/\U0001d5c1", "30 km/h")),
        ("uÌˆnicode", "ünicode"),
        ("HTML entities &lt;3", "HTML entities <3"),
        ("<em>HTML entities in HTML &lt;3</em>", "<em>HTML entities in HTML &lt;3</em>"),
        ("Broken text&hellip; it&#x2019;s ﬂubberiﬁc!", "Broken text... it's flubberific!"),
        ("™", "TM"),
        ("H₂O", "H2O"),
    ],
)
def test__clean_unicode(string, expected):
    assert tlz.pipe(string, raw2text.clean_unicode, c_eq(expected))


# Examples from https://pypi.python.org/pypi/Unidecode/
@pytest.mark.parametrize(
    "string,expected",
    [
        ("ko\u017eu\u0161\u010dek", "kozuscek"),
        # expected to fail on OSX
        osx_xfail(("30 \U0001d5c4\U0001d5c6/\U0001d5c1", "30 km/h")),
        ("\u5317\u4eb0", "Bei Jing "),
    ],
)
def test__normize_text(string, expected):
    assert tlz.pipe(string, raw2text.normize_text, c_eq(expected))


@pytest.mark.parametrize(
    "string,encoding,expected",
    [
        ("foo".encode("utf-8"), "utf-8", "foo"),
        ("foo".encode("ascii"), "ascii", "foo"),
        ("foo".encode("utf-32"), "utf-32", "foo"),
        ("ünicode".encode("iso-8859-2"), "iso-8859-2", "ünicode"),
        ("ünicode".encode("utf-8"), "utf-8", "ünicode"),
    ],
)
def test__std_decode(string, encoding, expected):
    assert tlz.pipe(string, lambda txt: raw2text.std_decode(txt, encoding=encoding), c_eq(expected))


@pytest.mark.parametrize(
    "string,acceptable",
    [
        ("foo".encode("utf-8"), ("utf-8", "ascii")),
        ("foo".encode("ascii"), ("ascii",)),
        ("ünicode".encode("utf-8"), ("utf-8", "iso-8859-2")),
    ],
)
def test__guess_encoding(string, acceptable):
    guessed = tlz.pipe(string, raw2text.guess_encoding, lambda txt: txt.lower())
    assert guessed in acceptable


@pytest.mark.parametrize(
    "string,encoding,expected",
    [
        ("foo".encode("utf-8"), "utf-8", "foo"),
        ("foo".encode("ascii"), "ascii", "foo"),
        ("foo".encode("utf-32"), "utf-32", "foo"),
        ("ünicode".encode("utf-8"), "utf-8", "ünicode"),
        ("ünicode".encode("utf-32"), "utf-32", "ünicode"),
        ("foo".encode("ascii"), "utf-8", "foo"),
        ("ünicode".encode("utf-8"), "utf-8", "ünicode"),
        ("ünicode".encode("iso-8859-2"), "utf-8", "ünicode"),
    ],
)
def test__adv_decode(string, encoding, expected):
    decoded = raw2text.adv_decode(string, encoding=encoding)
    assert decoded == expected


@pytest.mark.parametrize(
    "string,expected",
    [
        ("ko\u017eu\u0161\u010dek".encode("utf-8"), "kozuscek"),
        osx_xfail(("30 \U0001d5c4\U0001d5c6/\U0001d5c1".encode("utf-8"), "30 km/h")),  # Find out why it fails on OSX.
        ("\u5317\u4eb0".encode("utf-8"), "Bei Jing "),
        ("Broken text&hellip; it&#x2019;s ﬂubberiﬁc!".encode("utf-8"), "Broken text... it's flubberific!"),
        ("™".encode("utf-8"), "TM"),
        ("H₂O".encode("utf-8"), "H2O"),
        ("Broken text&hellip; it&#x2019;s ﬂubberiﬁc!".encode("utf-16"), "Broken text... it's flubberific!"),
        ("™".encode("utf-16"), "TM"),
        ("H₂O".encode("utf-16"), "H2O"),
        ("foo".encode("iso-8859-2"), "foo"),
        ("foo".encode("windows-1250"), "foo"),
        ("foo".encode("IBM850"), "foo"),
    ],
)
def test__decode_and_fix(string, expected):
    decoded = raw2text.decode_and_fix(string)
    assert decoded == expected
