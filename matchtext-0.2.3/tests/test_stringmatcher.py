# -*- coding: utf-8 -*-

import sys

from matchtext.stringmatcher import StringMatcher


def test_sm_find1():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his"]):
        sm.add(e, data=i, append=False)
    assert sm["this"] == 0
    assert sm["his"] == 4
    assert sm.get("this") == 0
    assert sm.get("asasas", "x") == "x"
    assert sm.get("asaasa") is None
    t1 = "this is a word"
    ms1 = sm.find(t1, all=True, skip=True)
    assert len(ms1) == 2
    m1 = ms1[0]
    assert m1.entrydata == 0
    assert m1.start == 0
    assert m1.end == 4
    assert m1.match == "this"
    assert m1.matcherdata is None
    m2 = ms1[1]
    assert m2.entrydata == 1
    assert m2.match == "word"
    assert m2.start == 10


def test_sm_find2():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his"]):
        sm.add(e, data=i, append=False)

    t1 = "this is a word"
    ms1 = sm.find(t1, all=True, skip=False)
    assert len(ms1) == 3
    m1 = ms1[0]
    assert m1.entrydata == 0
    assert m1.start == 0
    assert m1.end == 4
    assert m1.match == "this"
    assert m1.matcherdata is None
    m2 = ms1[1]
    assert m2.entrydata == 4
    assert m2.match == "his"
    assert m2.start == 1
    m3 = ms1[2]
    assert m3.entrydata == 1
    assert m3.match == "word"
    assert m3.start == 10


def test_sm_find3():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his"]):
        sm.add(e, data=i, append=False)

    t1 = "thisis a word"
    ms1 = sm.find(t1, all=True, skip=False)
    assert len(ms1) == 4
    m1 = ms1[0]
    assert m1.entrydata == 0
    assert m1.start == 0
    assert m1.end == 4
    assert m1.match == "this"
    assert m1.matcherdata is None
    m2 = ms1[1]
    assert m2.entrydata == 3
    assert m2.match == "thisis"
    assert m2.start == 0
    m3 = ms1[2]
    assert m3.entrydata == 4
    assert m3.match == "his"
    assert m3.start == 1
    m4 = ms1[3]
    assert m4.entrydata == 1
    assert m4.match == "word"
    assert m4.start == 9


def test_sm_find4():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his"]):
        sm.add(e, data=i, append=False)

    t1 = "thisis a word"
    ms1 = sm.find(t1, all=False, skip=True)
    assert len(ms1) == 2
    m1 = ms1[0]
    assert m1.entrydata == 3
    assert m1.match == "thisis"
    assert m1.start == 0
    m2 = ms1[1]
    assert m2.entrydata == 1
    assert m2.match == "word"
    assert m2.start == 9


def test_sm_find5():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his", "word"]):
        sm.add(e, data=i, append=True)

    t1 = "thisis a word"
    ms1 = sm.find(t1, all=False, skip=True)
    assert len(ms1) == 2
    m1 = ms1[0]
    assert m1.entrydata == [3]
    assert m1.match == "thisis"
    assert m1.start == 0
    m2 = ms1[1]
    assert m2.entrydata == [1, 5]
    assert m2.match == "word"
    assert m2.start == 9


def test_sm_find6():
    def f_ign(x):
        return x in "io"

    sm = StringMatcher(ignorefunc=f_ign)
    for i, e in enumerate(["this", "word", "words", "thisis", "his", "word"]):
        sm.add(e, data=i, append=True)
    # print(f"!!!!!!!!!!!DEBUG: nodes: ", file=sys.stderr)
    # sm._root.print_node()
    # print(file=sys.stderr)

    # In the following "thoss" should match because o gets ignored and and i got ignored for "thisis" so
    # we really match "thss"
    t1 = "thoss a wiiiiiiiird"
    ms1 = sm.find(t1, all=False, skip=True)
    assert len(ms1) == 2
    m1 = ms1[0]
    assert m1.entrydata == [3]
    assert m1.match == "thoss"
    assert m1.start == 0
    assert m1.end == 5
    m2 = ms1[1]
    assert m2.entrydata == [1, 5]
    assert m2.match == "wiiiiiiiird"
    assert m2.start == 8
    assert m2.end == 19


def test_sm_replace1():
    sm = StringMatcher()
    for i, e in enumerate(["this", "word", "words", "thisis", "his"]):
        sm.add(e, data=i, append=False)
    t1 = "thisis a word"
    rep = sm.replace(t1)
    assert rep == "3 a 1"
