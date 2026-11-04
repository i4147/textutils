import re

import regex

from metext.utils.uri import URI, IPv4address, IPv6address, pchar

RE_MD5 = re.compile(r"\b(?!^[\d]*$)(?!^[a-fA-F]*$)([a-f\d]{32}|[A-F\d]{32})\b")
RE_SHA1 = re.compile(r"\b(?:[a-f0-9]{40}|[A-F0-9]{40})\b")
RE_SHA224 = re.compile(r"\b(?:[a-f0-9]{56}|[A-F0-9]{56})\b")
RE_SHA256 = re.compile(r"\b(?:[a-f0-9]{64}|[A-F0-9]{64})\b")
RE_SHA384 = re.compile(r"\b(?:[a-f0-9]{96}|[A-F0-9]{96})\b")
RE_SHA512 = re.compile(r"\b(?:[a-f0-9]{128}|[A-F0-9]{128})\b")

RE_URL = re.compile(
    "(?:(?:(?:https?|ftp):)//)(?:\\S+(?::\\S*)?@)?(?:(?!(?:10|127)(?:\\.\\d{1,3}){3})(?!(?:169\\.254|192\\.168)(?:\\.\\d{1,3}){2})(?!172\\.(?:1[6-9]|2\\d|3[0-1])(?:\\.\\d{1,3}){2})(?:[1-9]\\d?|1\\d\\d|2[01]\\d|22[0-3])(?:\\.(?:1?\\d{1,2}|2[0-4]\\d|25[0-5])){2}(?:\\.(?:[1-9]\\d?|1\\d\\d|2[0-4]\\d|25[0-4]))|(?:(?:[a-z0-9][a-z0-9_-]{0,62})?[a-z0-9]\\.)+(?:[a-z]{2,}\\.?))(?::\\d{2,5})?(?:[/?#]"
    + pchar
    + "*)?",
    re.IGNORECASE,
)
RE_URN = re.compile(
    r"\b(?=(?:urn|URN):)urn:[a-z0-9][a-z0-9-]{0,31}:[a-z0-9()+,\-.:=@;$_!*'%/?#]+\b",
    re.IGNORECASE,
)
RE_DATA_URI = re.compile(
    r"\b(?=(?:data|DATA):)(?:data|DATA):(?:[-\w]+/[-+\w.]+)?(?:(?:;?[\w]+=[-\w]+)*)(?:;base64,(?:[A-Za-z0-9+/=_-]*)|,(?:%[0-9A-Fa-f][0-9A-Fa-f]|['!$&(-.0-;=@-Z_a-z~ ])*)\b",
)
RE_MAGNET_URI = re.compile(
    r"\b(?=(?:magnet|MAGNET):){}\b".format(URI),
    re.VERBOSE,
)

RE_EMAIL = re.compile(r"\b(?=[A-Za-z][A-Za-z0-9._%+-]+@)[A-Za-z0-9._%+-]+(?<![._%-])@[A-Za-z0-9.-]+\.[A-Za-z]{2,10}\b")
RE_URL_FORM_FIELDS = re.compile(r"^(?:[a-zA-Z][0-9a-zA-Z._-]*=[ -~]*&?)+", re.MULTILINE)

RE_ISBN10 = re.compile(
    r"""
#(?:ISBN(?:-10)?:?\ ?)?     # Optional ISBN/ISBN-10 identifier.
(?=                       # Basic format pre-checks (lookahead):
  \b[0-9X]{10}\b             #   Require 10 digits/Xs (no separators).
 |                        #  Or:
  \b(?=(?:[0-9]+[-\ ]){3})  #   Require 3 separators
  [-\ 0-9X]{13}\b          #     out of 13 characters total.
)                         # End format pre-checks.
[0-9]{1,5}[-\ ]?          # 1-5 digit group identifier.
[0-9]+[-\ ]?[0-9]+[-\ ]?  # Publisher and title identifiers.
[0-9X]                    # Check digit.
""",
    re.VERBOSE | re.IGNORECASE,
)
RE_ISBN13 = re.compile(
    r"""
#(?:ISBN(?:-13)?:?\ ?)?     # Optional ISBN/ISBN-13 identifier.
(?=                       # Basic format pre-checks (lookahead):
  \b[0-9]{13}\b              #   Require 13 digits (no separators).
 |                        #  Or:
  \b(?=(?:[0-9]+[-\ ]){4})  #   Require 4 separators
  [-\ 0-9]{17}\b           #     out of 17 characters total.
)                         # End format pre-checks.
97[89][-\ ]?              # ISBN-13 prefix.
[0-9]{1,5}[-\ ]?          # 1-5 digit group identifier.
[0-9]+[-\ ]?[0-9]+[-\ ]?  # Publisher and title identifiers.
[0-9]                     # Check digit.
""",
    re.VERBOSE | re.IGNORECASE,
)
RE_ISBN = re.compile(
    r"""
#(?:ISBN(?:-1[03])?:?\ ?)?  # Optional ISBN/ISBN-10/ISBN-13 identifier.
(?=                       # Basic format pre-checks (lookahead):
  \b[0-9X]{10}\b             #   Require 10 digits/Xs (no separators).
 |                        #  Or:
  \b(?=(?:[0-9]+[-\ ]){3})  #   Require 3 separators
  [-\ 0-9X]{13}\b          #     out of 13 characters total.
 |                        #  Or:
  \b97[89][0-9]{10}\b        #   978/979 plus 10 digits (13 total).
 |                        #  Or:
  \b(?=(?:[0-9]+[-\ ]){4})  #   Require 4 separators
  [-\ 0-9]{17}\b           #     out of 17 characters total.
)                         # End format pre-checks.
(?:97[89][-\ ]?)?         # Optional ISBN-13 prefix.
[0-9]{1,5}[-\ ]?          # 1-5 digit group identifier.
[0-9]+[-\ ]?[0-9]+[-\ ]?  # Publisher and title identifiers.
[0-9X]                    # Check digit.
""",
    re.VERBOSE | re.IGNORECASE,
)

RE_ISSN = re.compile(r"\b[0-9]{4}-[0-9]{3}[0-9xX]\b")

RE_DOI = re.compile(r"\b(?=10[.])10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![\"&\'<>])[-._();/:a-zA-Z0-9])+\b")

RE_BASE32 = re.compile(
    r"\b(?=[A-Z2-7]{16,})(?:[A-Z2-7]{8})*(?:[A-Z2-7]{2}={6}|[A-Z2-7]{4}={4}|[A-Z2-7]{5}={3}|[A-Z2-7]{7}=)?"
)
# RE_BASE64 = re.compile(
#     r"\b(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?(?!\w)"
# )  # https://www.rise4fun.com/Bek/tutorial/base64

RE_BASE64 = re.compile(
    r"\b(?=[A-Za-z0-9+/]{8,})(?:(?:[A-Za-z0-9+/]{76}(?:\r\n|\\r\\n|\n|\\n|\r|\\r)|[A-Za-z0-9+/]{64}(?:\r\n|\\r\\n|\n|\\n|\r|\\r)|[A-Za-z0-9+/]{4})*)(?:[A-Za-z0-9+/][AQgw]==|[A-Za-z0-9+/]{2}[AEIMQUYcgkosw048]=)?(?![A-Za-z0-9+/])"
)

PATTERN_BTC_BASE58 = r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,42}\b"
PATTERN_BTC_SEGWIT = r"\b(?:[bB][cC])1[a-zA-HJ-NP-Z0-9]{25,39}\b"
PATTERN_BIP32_XPRV = r"\bxprv[a-km-zA-HJ-NP-Z1-9]{107,108}\b"
PATTERN_BIP32_XPUB = r"\bxpub[a-km-zA-HJ-NP-Z1-9]{107,108}\b"
PATTERN_BCH = r"\b(?:(?:bitcoincash:)?[qp][a-z0-9]{41}|(?:BITCOINCASH:)?[QP][A-Z0-9]{41})\b"
PATTERN_ETH = r"\b0x[0-9a-f]{40,42}\b"
PATTERN_ADA_V1 = r"\b(?:Ddz[0-9a-zA-Z]{80,120}|Ae2tdPwUPE[0-9a-zA-Z]{46,53})\b"
PATTERN_ADA_SHELLEY = r"\b(?:addr[0-9a-zA-Z]{52,99}|stake[0-9a-zA-Z]{54,99}|[0-9a-zA-Z]{99,103})\b"

RE_BTC = re.compile("{}|{}".format(PATTERN_BTC_SEGWIT, PATTERN_BTC_BASE58))
RE_BTC_WIF = re.compile(r"\b(?:[59][a-km-zA-HJ-NP-Z1-9]{50}|[LKc][a-km-zA-HJ-NP-Z1-9]{51})\b")
RE_BTC_PRIVKEY = re.compile(r"\b[0-9a-fA-f]{64}\b")
RE_BIP32_XPRV = re.compile(PATTERN_BIP32_XPRV)
RE_BIP32_XPUB = re.compile(PATTERN_BIP32_XPUB)
RE_BIP32_XKEY = re.compile(r"(?=\bxp)(?:{}|{})".format(PATTERN_BIP32_XPRV, PATTERN_BIP32_XPUB))
RE_LTC = re.compile(r"\b(?:[LM3][a-km-zA-HJ-NP-Z1-9]{26,33}|(?:ltc|LTC)1[a-zA-HJ-NP-Z0-9]{25,70})\b")
RE_XRP = re.compile(r"\br[0-9a-zA-Z]{24,34}\b")
RE_ETH = re.compile(PATTERN_ETH, re.IGNORECASE)
RE_USDT = re.compile(r"{}|{}".format(PATTERN_BTC_BASE58, PATTERN_ETH), re.IGNORECASE)
RE_LINK = RE_ETH
RE_BCH = re.compile(PATTERN_BCH)
RE_BCH_WITH_LEGACY = re.compile(r"{}|{}".format(PATTERN_BTC_BASE58, PATTERN_BCH))
RE_ADA = re.compile(r"{}|{}".format(PATTERN_ADA_V1, PATTERN_ADA_SHELLEY))
RE_DOT = re.compile(r"\b1[a-zA-Z1-9]{25,60}\b")

RE_PEM = re.compile(
    r"(?:-----BEGIN (?P<label>.+?)-----).+?(?:-----END (?P=label)-----)",
    re.DOTALL,
)

RE_JSON = regex.compile(
    r"""(?x)(?(DEFINE)
# Note that everything is atomic, JSON does not need backtracking if it's valid
# and this prevents catastrophic backtracking
(?<json>(?>(?&object)|(?&array)))
(?<object>(?>\{\s*(?>(?&pair)(?>\s*,\s*(?&pair))*)?\s*\}))
(?<pair>(?>(?&STRING)\s*:\s*(?&value)))
(?<array>(?>\[\s*(?>(?&value)(?>\s*,\s*(?&value))*)?\s*\]))
(?<value>(?>true|false|null|(?&STRING)|(?&NUMBER)|(?&object)|(?&array)))
(?<STRING>(?>"(?>\\(?>["\\\/bfnrt]|u[a-fA-F0-9]{4})|[^"\\\0-\x1F\x7F]+)*"))
(?<NUMBER>(?>-?(?>0|[1-9][0-9]*)(?>\.[0-9]+)?(?>[eE][+-]?[0-9]+)?))
)
(?<!\w)(?=[{[])(?&json)""",
    regex.VERBOSE,
)

RE_GUID = re.compile(r"\b(?<!-)[0-9a-fA-F]{8}[-]?(?:[0-9a-fA-F]{4}[-]?){3}[0-9a-fA-F]{12}(?!-)\b")
RE_MAC = re.compile(
    r"(?<![:-])(?:(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![:-])|(?<![.])(?:[0-9a-fA-F]{4}\.){2}[0-9a-fA-F]{4})(?![.])"
)
RE_IPV4 = re.compile(r"\b(?<!\.)(?=[0-9]{{,3}}\.){}(?!\.)\b".format(IPv4address), re.VERBOSE)
RE_IPV6 = re.compile(r"\b(?<!:)(?=(?:::)?[a-fA-F0-9]){}(?!:)\b".format(IPv6address), re.VERBOSE)
