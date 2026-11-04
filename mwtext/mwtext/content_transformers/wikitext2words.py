from .content_transformer import ContentTransformer
from . import util
import re

PLAIN_PROTO = [r"bitcoin", r"geo", r"magnet", r"mailto", r"news", r"sips?", r"tel", r"urn"]
SLASHED_PROTO = [
    r"",
    r"ftp",
    r"ftps",
    r"git",
    r"gopher",
    r"https?",
    r"ircs?",
    r"mms",
    r"nntp",
    r"redis",
    r"sftp",
    r"ssh",
    r"svn",
    r"telnet",
    r"worldwind",
    r"xmpp",
]
ADDRESS = r"[^\s/$.?#].[^\s]*"

URL_RE = r"(" + r"(" + "|".join(PLAIN_PROTO) + r")\:|" + r"((" + "|".join(SLASHED_PROTO) + r")\:)?\/\/" + r")" + ADDRESS

STRIP_WIKITEXT_REs = [
    r"<!--.*?-->",
    r"{{.*?}}",
    r"&[a-z]+;",
    r"<ref[^<>]*>[^<]*<\/ref>",
    r"<[^>]*>",
    r"\[" + URL_RE + r"\]",
    URL_RE,
    r"\{\{[^\}]+\}\}",
    r"\{\|[^\}\|]+\|\}",
    r"(^|\n);+[^\n]+",
    r"\n\s*\|[^\n]+",
    r"'''?",
]

NUMBER_RE = r"\b[0-9][0-9\.\,]*(e[0-9]+)?s?\b"

REPLACE_REs = [
    (re.compile(r"(^|\n)==+[^=]+==+"), "\n\n"),
    (re.compile(r"\[" + URL_RE + r"( ([^\]]+))?\]"), r"\5"),
    (re.compile(r"\[\[([^\]\|]+)\]\]"), r"\1"),
    (re.compile(r"\[\[([^\]\|]+)\|([^\]]+)\]\]"), r"\2"),
    (re.compile(NUMBER_RE), "anumber"),
]

PARAGRAPH_SPLIT_RE = r"(\n|\n\r|\r\n)\s*(\n|\n\r|\r\n)+"

devangari_word = r"\u0901-\u0963"
arabic_word = r"\u0601-\u061A" + r"\u061C-\u0669" + r"\u06D5-\u06EF"
bengali_word = r"\u0980-\u09FF"
combined_word = devangari_word + arabic_word + bengali_word

WORD_RE = (
    r"([^\W\d]|["
    + combined_word
    + r"])"
    + r"[\w"
    + combined_word
    + r"]*"
    + r"([\'’]([\w"
    + combined_word
    + r"]+|(?=($|\s))))*"
)

CJK_RE = (
    r"["
    + r"\u4E00-\u62FF"
    + r"\u6300-\u77FF"
    + r"\u7800-\u8CFF"
    + r"\u8D00-\u9FCC"
    + r"\u3400-\u4DFF"
    + r"\U00020000-\U000215FF"
    + r"\U00021600-\U000230FF"
    + r"\U00023100-\U000245FF"
    + r"\U00024600-\U000260FF"
    + r"\U00026100-\U000275FF"
    + r"\U00027600-\U000290FF"
    + r"\U00029100-\U0002A6DF"
    + r"\uF900-\uFAFF"
    + r"\U0002F800-\U0002FA1F"
    + r"\u3041-\u3096"
    + r"\u30A0-\u30FF"
    + r"\u3400-\u4DB5"
    + r"\u4E00-\u9FCB"
    + r"\uF900-\uFA6A"
    + r"\u2E80-\u2FD5"
    + r"\uFF5F-\uFF9F"
    + r"\u31F0-\u31FF"
    + r"\u3220-\u3243"
    + r"\u3280-\u337F"
    r"]"
)
WORD_OR_CJK_RE = re.compile(WORD_RE + "|" + CJK_RE)

PARAGRAPH_SPLIT_RE = r"(\n|\n\r|\r\n)\s*(\n|\n\r|\r\n)+"

HIDDEN_LINK_NAMESPACES = ["Category", "Image"]


class Wikitext2Words(ContentTransformer):
    def __init__(self, hidden_link_namespace_names):
        forbidden_link_re = r"\[\[(" + "|".join(hidden_link_namespace_names).lower() + r"):[^\]]+\]\]"
        self.strip_regex = re.compile("|".join(STRIP_WIKITEXT_REs + [forbidden_link_re]))
        self.replace_regexs = [(re.compile(p), r) for p, r in REPLACE_REs]

    def transform(self, content):
        return list(self._extract_words(content))

    @classmethod
    def from_siteinfo(cls, siteinfo, *args, **kwargs):
        hidden_link_namespace_names = util.generate_non_link_namespace_names(siteinfo)
        return cls(hidden_link_namespace_names, *args, **kwargs)

    def _extract_words(self, text):
        stripped_text = re.sub(self.strip_regex, "", text.lower())

        for replace_regex, replacement in self.replace_regexs:
            stripped_text = re.sub(replace_regex, replacement, stripped_text)

        for match in re.finditer(WORD_OR_CJK_RE, stripped_text):
            yield match.group(0)
