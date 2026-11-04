import re

UNICODE_SNOB = False

TABLE_MARKER_FOR_PAD = "special_marker_for_table_padding"
ESCAPE_SNOB = False

LINKS_EACH_PARAGRAPH = False

BODY_WIDTH = 78

SKIP_INTERNAL_LINKS = True

INLINE_LINKS = True

PROTECT_LINKS = False
# WRAP_LINKS = True
WRAP_LINKS = True

WRAP_LIST_ITEMS = False

WRAP_TABLES = False

GOOGLE_LIST_INDENT = 36

BOLD_TEXT_STYLE_VALUES = ("bold", "700", "800", "900")

IGNORE_ANCHORS = False
IGNORE_MAILTO_LINKS = False
IGNORE_IMAGES = False
IMAGES_AS_HTML = False
IMAGES_TO_ALT = False
IMAGES_WITH_SIZE = False
IGNORE_EMPHASIS = False
MARK_CODE = False
BACKQUOTE_CODE_STYLE = False
DECODE_ERRORS = "strict"
DEFAULT_IMAGE_ALT = ""
PAD_TABLES = False

USE_AUTOMATIC_LINKS = True

RE_SPACE = re.compile(r"\s\+")

RE_ORDERED_LIST_MATCHER = re.compile(r"\d+\.\s")
RE_UNORDERED_LIST_MATCHER = re.compile(r"[-\*\+]\s")
RE_MD_CHARS_MATCHER = re.compile(r"([\\\[\]\(\)])")
RE_MD_CHARS_MATCHER_ALL = re.compile(r"([`\*_{}\[\]\(\)#!])")

RE_LINK = re.compile(r"(\[.*?\] ?\(.*?\))|(\[.*?\]:.*?)")

RE_TABLE = re.compile(r" \| ")

RE_MD_DOT_MATCHER = re.compile(
    r"""
    ^             # start of line
    (\s*\d+)      # optional whitespace and a number
    (\.)          # dot
    (?=\s)        # lookahead assert whitespace
    """,
    re.MULTILINE | re.VERBOSE,
)
RE_MD_PLUS_MATCHER = re.compile(
    r"""
    ^
    (\s*)
    (\+)
    (?=\s)
    """,
    flags=re.MULTILINE | re.VERBOSE,
)
RE_MD_DASH_MATCHER = re.compile(
    r"""
    ^
    (\s*)
    (-)
    (?=\s|\-)     # followed by whitespace (bullet list, or spaced out hr)
                  # or another dash (header or hr)
    """,
    flags=re.MULTILINE | re.VERBOSE,
)
RE_SLASH_CHARS = r"\`*_{}[]()#+-.!"
RE_MD_BACKSLASH_MATCHER = re.compile(
    r"""
    (\\)          # match one slash
    (?=[%s])      # followed by a char that requires escaping
    """
    % re.escape(RE_SLASH_CHARS),
    flags=re.VERBOSE,
)

UNIFIABLE = {
    "rsquo": "'",
    "lsquo": "'",
    "rdquo": '"',
    "ldquo": '"',
    "copy": "(C)",
    "mdash": "--",
    "nbsp": " ",
    "rarr": "->",
    "larr": "<-",
    "middot": "*",
    "ndash": "-",
    "oelig": "oe",
    "aelig": "ae",
    "agrave": "a",
    "aacute": "a",
    "acirc": "a",
    "atilde": "a",
    "auml": "a",
    "aring": "a",
    "egrave": "e",
    "eacute": "e",
    "ecirc": "e",
    "euml": "e",
    "igrave": "i",
    "iacute": "i",
    "icirc": "i",
    "iuml": "i",
    "ograve": "o",
    "oacute": "o",
    "ocirc": "o",
    "otilde": "o",
    "ouml": "o",
    "ugrave": "u",
    "uacute": "u",
    "ucirc": "u",
    "uuml": "u",
    "lrm": "",
    "rlm": "",
}

BYPASS_TABLES = False
IGNORE_TABLES = False


SINGLE_LINE_BREAK = False


OPEN_QUOTE = '"'
CLOSE_QUOTE = '"'

INCLUDE_SUP_SUB = False
