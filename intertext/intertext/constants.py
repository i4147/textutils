# -*- coding: utf-8 -*-


import re

MATCH_HIERARCHY = [1, 2, 3, 4, 5]


DEFAULT_A_GRAMMAR = "ln,fn;"
DEFAULT_C_GRAMMAR = "a/y/t/r"
A_GRAMMARS = {
    "ln,fn;": "lastname, firstname;",
    "ln,fn,": "lastname, firstname,",
    "fn ln,": "firstname lastname,",
    "fn ln;": "firstname lastname;",
    "ln;": "lastname;",
    "ln,": "lastname,",
}
C_GRAMMARS = {
    "a/y/t/r": "author/year/title/rest",
    "a/t/y/r": "author/title/year/rest",
    "y/a/t/r": "year/author/title/rest",
    "y/t/a/r": "year/title/author/rest",
    "t/a/y/r": "title/author/year/rest",
    "t/y/a/r": "title/year/author/rest",
}

ZOT_TEMPLATE_TXT = {
    "contentType": "text/plain",
    "itemType": "attachment",
    "title": "",
    "accessDate": "",
    "linkMode": "linked_file",
    "charset": "",
    "relations": {},
    "note": "",
    "url": "",
    "path": "",
    "tags": [],
}

NOFIRSTNAME = "_firstname"

RE_QUOTATIONS_SINGLE = re.compile(
    "[\u0027\u2018\u2019\u201a\u201b\u2039\u203a\u300c\u300d\ufe41\ufe42\uff07\uff62\uff63]"
)

RE_QUOTATIONS_DOUBLE = re.compile(
    "[\u0022\u00ab\u00bb\u201c\u201d\u201e\u201f\u300e\u300f\u301d\u301e\u301f\ufe43\ufe44\uff02]"
)

RE_ESCAPE = re.compile(r"|".join([r"(\\)'", r'(\\)"']))
RE_CHAR = re.compile(r'[\'",/:)(.&%\[\]\\*+-]')
RE_LONELY_CHAR = re.compile(r"(?<=\b)" + r"[bcdefghjklmnopqrstuvwxyzBCDEFGHJKLMNOPQRSTUVWXYZ](?=\b)")
RE_NUM = re.compile(r"[\d]+")
RE_P_TAGS = re.compile(r"<p>|</p>| ( )")
RE_AMP = re.compile(r"&amp;")
RE_CIT_LINEBREAKS = re.compile(r"<br />|<br>|<br/>|\r|\v")
RE_LINEBREAKS = re.compile(r"<br />|<br>|<br/>|\r|\v|\n")
RE_DOUBLE_SPACE = re.compile(r"\s+")
RE_CLEAN_DOUBLELINEBREAK = re.compile(r"\n([\s]*\n)")
RE_EMPTY_END_OF_STRING = re.compile(r"\n[\s]*$")
RE_EMPTY_END_OF_LINE = re.compile(r"[ \t]+\n")
RE_FORTHCOMING = re.compile(
    r"forthcoming|Forthcoming|FORTHCOMING|"
    r"In Print|in print|IN PRINT"
)
RE_INTEXT_CITATION_CANDIDATE = re.compile(r"\([^()]*(?:19|20)\d\d[a-f]*[^()]*\)")
RE_DOI = re.compile(
    r"[dD][oO][iI]: *10[0-9./():<>;A-Za-z-]+|"
    r"http://dx.doi.org/10[0-9./():<>;A-Za-z-]+"
)


YEAR = r"\d\d\d\d"
RECENTYEAR = r"(?:19|20)\d\d"
MODERNYEAR = r"(?:15|16|17|18|19|20)\d\d"
DAYOFMONTH = r"(?:0*[1-9]|1\d|2\d|30|31)\.*"
MONTH = (
    r"(?:[Jj][aA][nN][uU]*[aA]*[rR]*[yY]*|"
    r"[fF][eE][bB][rR]*[uU]*[aA]*[rR]*[yY]*|"
    "[mM][aA][rR][cC]*[hH]*|[mM][äÄ][rR][zZ]*|"
    r"[aA][pP][rR][iI]*[lL]*|"
    r"[mM][aA][yY]|[mM][aA][iI]|"
    r"[jJ][uU][nN][eE]*|[jJ][uU][nN][iI]*|"
    r"[jJ][uU][lL][yY]*|[jJ][uU][lL][iI]*|"
    r"[aA][uU][gG][uU]*[sS]*[tT]*|"
    r"[sS][eE][pP][tT]*[eE]*[mM]*[bB]*[eE]*[rR]*|"
    r"[oO][cC][tT][oO]*[bB]*[eE]*[rR]*|[oO][kK][tT][oO]*[bB]*[eE]*[rR]*|"
    r"[nN][oO][vV][eE]*[mM]*[bB]*[eE]*[rR]*|"
    r"[dD][eE][cC][eE]*[mM]*[bB]*[eE]*[rR]*|[dD][eE][zZ][eE]*[mM]*[bB]*[eE]*[rR]*)"
)
DATE_MY = r" ".join([MONTH, RECENTYEAR])
DATE_DMY = r" ".join([DAYOFMONTH, MONTH, RECENTYEAR])
DATE_DMY_NUM = r"(?:0*[1-9]|1\d|2\d|30|31)(?:/|-)(?:0*[1-9]|1[012])(?:/|-)(?:19|20)\d\d"
DATE_MDY = r" ".join([MONTH, DAYOFMONTH + r",*", RECENTYEAR])
DATE_YMD = r" ".join([RECENTYEAR, MONTH, DAYOFMONTH])
DATE_YMD_NUM = r"(?:19|20)\d\d(?:/|-)(?:0*[1-9]|1[012])(?:/|-)(?:0*[1-9]|1\d|2\d|30|31)"
DATE_ALL = r"|".join([DATE_MY, DATE_DMY, DATE_YMD, DATE_MDY, DATE_YMD_NUM, DATE_DMY_NUM])

RE_DATE_MY = re.compile(r"\b" + DATE_MY + r"\b")
RE_DATE_DMY = re.compile(r"\b" + DATE_DMY + r"\b")
RE_DATE_MDY = re.compile(r"\b" + DATE_MDY + r"\b")
RE_DATE_ALL = re.compile(r"\b" + DATE_ALL + r"\b")
RE_MONTH = re.compile(r"\b" + MONTH + r"\b")
RE_YEAR = re.compile(r"\b" + YEAR + r"\b")
RE_RECENTYEAR = re.compile(r"\b" + RECENTYEAR + r"\b")
RE_DAYOFMONTH = re.compile(r"\b" + DAYOFMONTH + r"\b")

RE_VALID_DATE = re.compile("^" + YEAR + "|" + DATE_ALL + "$")


ACCENTS_LOWER = "àáâãäåæčçèéêëìíîïñòóôõöøœšùúûüýÿžß"
ACCENTS_UPPER = "ÀÁÂÃÄÅÆÇÈÉÊËÌÍÎÏÑÒÓÔÕÖØŒŠÚÛÜÙÝŸŽ"

FIRSTNAME = "[a-zA-Z{0}{1}][-a-zA-Z \.{0}{1}]*".format(ACCENTS_LOWER, ACCENTS_UPPER)
LASTNAME = "[a-zA-Z'{0}{1}][-a-zA-Z' {0}{1}]*".format(ACCENTS_LOWER, ACCENTS_UPPER)
NAME = "{}(, {})?".format(LASTNAME, FIRSTNAME)

RE_FIRSTNAME = re.compile("^{}$".format(FIRSTNAME))
RE_LASTNAME = re.compile("^{}$".format(LASTNAME))
RE_NAME = re.compile("^{}$".format(NAME))
