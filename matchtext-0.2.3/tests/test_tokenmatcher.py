# -*- coding: utf-8 -*-


from matchtext.tokenmatcher import Node, TokenMatcher


ENTRIES = ["Some", "word", "to", "add", ["some", "word"], ["some", "word"]]


def test_tm_find1():
    tm = TokenMatcher()
    for i, e in enumerate(ENTRIES):
        tm.add(e, data=i, append=False)

    t1 = ["This", "contains", "Some", "text"]
    ms1 = tm.find(t1, all=False, skip=True)
    assert len(ms1) == 1
    m1 = ms1[0]
    assert m1.entrydata == 0
    assert m1.start == 2
    assert m1.end == 3
    assert m1.matcherdata is None


def test_tm_find2():
    tm = TokenMatcher(mapfunc=str.lower, matcherdata="x")
    for i, e in enumerate(ENTRIES):
        tm.add(e, data=i, append=True)
    t1 = ["this", "contains", "some", "word", "of", "text", "to", "add"]
    ms = tm.find(t1, all=True, skip=False)
    # print("Matches:", ms)
    assert len(ms) == 5
    m = ms[0]
    assert m.entrydata == [0]
    assert m.start == 2
    assert m.end == 3
    assert m.matcherdata == "x"
    m = ms[1]
    assert m.match == ["some", "word"]
    assert m.entrydata == [4, 5]
    assert m.start == 2
    assert m.end == 4
    assert m.matcherdata == "x"
    m = ms[2]
    assert m.match == ["word"]
    assert m.entrydata == [1]
    assert m.start == 3
    assert m.end == 4
    assert m.matcherdata == "x"


def test_tm_replace1():
    tm = TokenMatcher(mapfunc=str.lower)
    for i, e in enumerate(ENTRIES):
        tm.add(e, data=i, append=False)
    t1 = ["this", "contains", "some", "word", "of", "text", "to", "add"]
    rep = tm.replace(t1)
    assert rep == ["this", "contains", 5, "of", "text", 2, 3]


def test_tm_replace2():
    tm = TokenMatcher(mapfunc=str.lower)
    for i, e in enumerate(ENTRIES):
        tm.add(e, data=i, append=False)
    t1 = ["THIS", "CONTAINS", "SOME", "WORD", "OF", "TEXT", "TO", "ADD"]
    rep = tm.replace(t1, replacer=lambda x: x.match)
    assert rep == ["THIS", "CONTAINS", "some", "word", "OF", "TEXT", "to", "add"]
    assert t1 == ["THIS", "CONTAINS", "SOME", "WORD", "OF", "TEXT", "TO", "ADD"]


def test_tm_find3():
    tm = TokenMatcher()
    for i, e in enumerate(ENTRIES):
        tm.add(e, data=i, append=False)
    t1 = ["This", "contains", "Some", "text"]

    def mm(*args):
        return args

    ms1 = tm.find(t1, all=False, skip=True, matchmaker=mm)
    assert len(ms1) == 1
    m1 = ms1[0]
    assert m1 == (2, 3, ["Some"], 0, None)


def test_tm_find4():
    """
    Test finding 2 longest matches
    :return:
    """
    tm = TokenMatcher()
    for i, e in enumerate([["some", "word"], ["some", "word"]]):
        tm.add(e, data=i, append=True)
    t1 = ["this", "contains", "some", "word", "yes"]
    ms1 = tm.find(t1, all=True, skip=False)
    assert len(ms1) == 1
    m1 = ms1[0]
    assert m1.start == 2
    assert m1.end == 4
    assert m1.match == ["some", "word"]
    assert m1.entrydata == [0, 1]


def test_tm_find5():
    """
    Test finding 2 longest matches
    :return:
    """
    tm = TokenMatcher()
    for i, e in enumerate([["some", "word"], ["some", "word"], "word"]):
        tm.add(e, data=i, append=True)
    t1 = ["this", "contains", "some", "word", "yes"]
    ms1 = tm.find(t1, all=True, skip=False)
    assert len(ms1) == 2
    m1 = ms1[0]
    assert m1.start == 2
    assert m1.end == 4
    assert m1.match == ["some", "word"]
    assert m1.entrydata == [0, 1]
    m2 = ms1[1]
    assert m2.match == ["word"]


def test_tm_replace3():
    tm = TokenMatcher()
    tm.add(["this", "and", "that"], "ENTRY1")
    tm.add(["she", "and", "he"], "ENTRY2")
    tm.add(["other", "stuff"], "ENTRY3")
    tokens = ["because", "this", "and", "that", "should", "also"]
    ms1 = tm.find(tokens)
    assert len(ms1) == 1
    m1 = ms1[0]
    assert m1.match == ["this", "and", "that"]  # note: the ignored token is NOT part of the result match!
    assert m1.start == 1
    assert m1.end == 4
    assert tokens[1:4] == ["this", "and", "that"]  # note: but the range fits the original tokens!
    assert tm.replace(["and", "also"]) == ["and", "also"]
    assert tm.replace(tokens) == ["because", "ENTRY1", "should", "also"]
    assert tm.replace(["other", "stuff"]) == ["ENTRY3"]
    assert tm.replace(["and", "other", "stuff"]) == ["and", "ENTRY3"]
    assert tm.replace(["word1", "word2", "other", "word3"]) == ["word1", "word2", "other", "word3"]
    assert tm.replace(["word1", "word2", "stuff", "word3"]) == ["word1", "word2", "stuff", "word3"]
    assert tm.replace(["word1", "word2", "and", "word3"]) == ["word1", "word2", "and", "word3"]
    assert tm.replace(["this", "and", "that", "other", "stuff"]) == ["ENTRY1", "ENTRY3"]


def test_tm_find6():
    """
    Test ignoring tokens
    :return:
    """

    def ign1(x):
        return x == "and"

    tm = TokenMatcher(ignorefunc=ign1)
    tm.add(["this", "and", "that"], "ENTRY1")
    tm.add(["she", "and", "he"], "ENTRY2")
    tm.add(["other", "stuff"], "ENTRY3")
    tokens = ["because", "this", "and", "that", "should", "also"]
    ms1 = tm.find(tokens)
    assert len(ms1) == 1
    m1 = ms1[0]
    assert m1.match == ["this", "that"]  # note: the ignored token is NOT part of the result match!
    assert m1.start == 1
    assert m1.end == 4
    assert tokens[m1.start : m1.end] == ["this", "and", "that"]  # note: but the range fits the original tokens!
    assert tm.replace(tokens) == ["because", "ENTRY1", "should", "also"]


def test_tm_replace4():
    def ign1(x):
        return x == "and"

    tm = TokenMatcher(ignorefunc=ign1)
    tm.add(["this", "and", "that"], "ENTRY1")
    tm.add(["she", "and", "he"], "ENTRY2")
    tm.add(["other", "stuff"], "ENTRY3")
    assert tm.replace(["and", "also"]) == ["and", "also"]
    assert tm.replace(["because", "this", "and", "that", "should", "also"]) == ["because", "ENTRY1", "should", "also"]
    assert tm.replace(["other", "stuff"]) == ["ENTRY3"]
    assert tm.replace(["and", "other", "stuff"]) == ["and", "ENTRY3"]
    assert tm.replace(["word1", "word2", "other", "word3"]) == ["word1", "word2", "other", "word3"]
    assert tm.replace(["word1", "word2", "stuff", "word3"]) == ["word1", "word2", "stuff", "word3"]
    assert tm.replace(["word1", "word2", "and", "word3"]) == ["word1", "word2", "and", "word3"]
    assert tm.replace(["this", "and", "that", "other", "stuff"]) == ["ENTRY1", "ENTRY3"]


def test_tmp_repr1():
    tm = TokenMatcher()
    tm.add(["this", "and", "that"], "ENTRY1")
    tm.add(["she", "and", "he"], "ENTRY2")
    tm.add(["other", "stuff"], "ENTRY3")
    assert (
        Node.dict_repr(tm.nodes)
        == """[('this', Node(is_match=None,data=None,nodes=[('and', Node(is_match=None,data=None,nodes=[('that', Node(is_match=True,data=ENTRY1,nodes=None))]))])), ('she', Node(is_match=None,data=None,nodes=[('and', Node(is_match=None,data=None,nodes=[('he', Node(is_match=True,data=ENTRY2,nodes=None))]))])), ('other', Node(is_match=None,data=None,nodes=[('stuff', Node(is_match=True,data=ENTRY3,nodes=None))]))]"""
    )
