__license__ = """
Copyright (c) 2009-2015 Mark Nottingham (code portions)
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""


DIGIT = r"[\x30-\x39]"

ALPHA = r"[\x41-\x5A\x61-\x7A]"

HEXDIG = r"[\x30-\x39A-Fa-f]"

DQUOTE = r"\""

pct_encoded = r" %% %(HEXDIG)s %(HEXDIG)s" % locals()

#   unreserved    = ALPHA / DIGIT / "-" / "." / "_" / "~"
unreserved = r"(?: %(ALPHA)s | %(DIGIT)s | \- | \. | _ | ~ )" % locals()

gen_delims = r"(?: : | / | \? | \# | \[ | \] | @ )"

sub_delims = r"""(?: ! | \$ | & | ' | \( | \) |
                     \* | \+ | , | ; | = )"""

#   pchar         = unreserved / pct-encoded / sub-delims / ":" / "@"
pchar = r"(?: %(unreserved)s | %(pct_encoded)s | %(sub_delims)s | : | @ )" % locals()

#   reserved      = gen-delims / sub-delims
reserved = r"(?: %(gen_delims)s | %(sub_delims)s )" % locals()


#   scheme        = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
scheme = r"%(ALPHA)s (?: %(ALPHA)s | %(DIGIT)s | \+ | \- | \. )*" % locals()


dec_octet = r"""(?: %(DIGIT)s |
                    [\x31-\x39] %(DIGIT)s |
                    1 %(DIGIT)s{2} |
                    2 [\x30-\x34] %(DIGIT)s |
                    25 [\x30-\x35]
                )
""" % locals()

IPv4address = r"%(dec_octet)s \. %(dec_octet)s \. %(dec_octet)s \. %(dec_octet)s" % locals()

h16 = r"(?: %(HEXDIG)s ){1,4}" % locals()

ls32 = r"(?: (?: %(h16)s : %(h16)s ) | %(IPv4address)s )" % locals()

IPv6address = r"""(?:                         (?: %(h16)s : ){6} %(ls32)s |
                                           :: (?: %(h16)s : ){5} %(ls32)s |
       (?:                      %(h16)s )? :: (?: %(h16)s : ){4} %(ls32)s |
       (?: (?: %(h16)s : ){0,1} %(h16)s )? :: (?: %(h16)s : ){3} %(ls32)s |
       (?: (?: %(h16)s : ){0,2} %(h16)s )? :: (?: %(h16)s : ){2} %(ls32)s |
       (?: (?: %(h16)s : ){0,3} %(h16)s )? ::     %(h16)s :      %(ls32)s |
       (?: (?: %(h16)s : ){0,4} %(h16)s )? ::                    %(ls32)s |
       (?: (?: %(h16)s : ){0,5} %(h16)s )? ::                    %(h16)s  |
       (?: (?: %(h16)s : ){0,6} %(h16)s )? ::
)
""" % locals()

IPvFuture = r"v %(HEXDIG)s+ \. (?: %(unreserved)s | %(sub_delims)s | : )+" % locals()

IP_literal = r"\[ (?: %(IPv6address)s | %(IPvFuture)s ) \]" % locals()

reg_name = r"(?: %(unreserved)s | %(pct_encoded)s | %(sub_delims)s )*" % locals()

#   userinfo      = *( unreserved / pct-encoded / sub-delims / ":" )
userinfo = r"(?: %(unreserved)s | %(pct_encoded)s | %(sub_delims)s | : )*" % locals()

#   host          = IP-literal / IPv4address / reg-name
host = r"(?: %(IP_literal)s | %(IPv4address)s | %(reg_name)s )" % locals()

#   port          = *DIGIT
port = r"(?: %(DIGIT)s )*" % locals()

authority = r"(?: %(userinfo)s @)? %(host)s (?: : %(port)s)?" % locals()


#   segment       = *pchar
segment = r"%(pchar)s*" % locals()

segment_nz = r"%(pchar)s+" % locals()

segment_nz_nc = r"(?: %(unreserved)s | %(pct_encoded)s | %(sub_delims)s | @ )+" % locals()

path_abempty = r"(?: / %(segment)s )*" % locals()

path_absolute = r"/ (?: %(segment_nz)s (?: / %(segment)s )* )?" % locals()

path_noscheme = r"%(segment_nz_nc)s (?: / %(segment)s )*" % locals()

path_rootless = r"%(segment_nz)s (?: / %(segment)s )*" % locals()

path_empty = r""

path = r"""(?: %(path_abempty)s |
               %(path_absolute)s |
               %(path_noscheme)s |
               %(path_rootless)s |
               %(path_empty)s
            )
""" % locals()


#   query         = *( pchar / "/" / "?" )
query = r"(?: %(pchar)s | / | \? )*" % locals()

#   fragment      = *( pchar / "/" / "?" )
fragment = r"(?: %(pchar)s | / | \? )*" % locals()


hier_part = r"""(?: (?: // %(authority)s %(path_abempty)s ) |
                    %(path_absolute)s |
                    %(path_rootless)s |
                    %(path_empty)s
                )
""" % locals()

relative_part = r"""(?: (?: // %(authority)s %(path_abempty)s ) |
                        %(path_absolute)s |
                        %(path_noscheme)s |
                        %(path_empty)s
                    )
""" % locals()

relative_ref = r"%(relative_part)s (?: \? %(query)s)? (?: \# %(fragment)s)?" % locals()

URI = r"(?: %(scheme)s : %(hier_part)s (?: \? %(query)s )? (?: \# %(fragment)s )? )" % locals()

URI_reference = r"(?: %(URI)s | %(relative_ref)s )" % locals()

absolute_URI = r"(?: %(scheme)s : %(hier_part)s (?: \? %(query)s )? )" % locals()


http_URI = r"(?: http: // %(authority)s %(path_abempty)s (?: \? %(query)s )? (?: \# %(fragment)s )? )" % locals()


https_URI = r"(?: https: // %(authority)s %(path_abempty)s (?: \? %(query)s )? (?: \# %(fragment)s )? )" % locals()


ws_URI = r"(?: ws: // %(host)s (?: : %(port)s )? %(path)s (?: \? %(query)s )? )" % locals()


wss_URI = r"(?: wss: // %(host)s (?: : %(port)s )? %(path)s (?: \? %(query)s )? )" % locals()


some_delims = r"""(?: ! | \$ | ' | \( | \) | \*
                      \+ | , | ; | : | @ )"""

# qchar        = unreserved / pct-encoded / some-delims

qchar = r"(?: %(unreserved)s | %(pct_encoded)s | %(some_delims)s )" % locals()


dtext_no_obs = r"(?: [\x21-\x5B\x5E-\x7E] )"

#

rfc5322_atext = r"""(?: 
    %(ALPHA)s | %(DIGIT)s | 
    ! | # | 
    \$ | %% | 
    & | ' | 
    \* | \+ | 
    - | / | 
    = | \? | 
    \^ | _ | 
    ` | { | 
    \| | } | 
    ~ )""" % locals()
rfc5322_dot_atom_text = r"(?: %(rfc5322_atext)s{1,} (?: . %(rfc5322_atext)s{1,} )* )" % locals()

#
#
# ccontent        =   ctext / quoted-pair / comment
#
#

qcontent = rfc5322_FWS = rfc5322_CFWS = r"(?: )"


rfc5322_quoted_string = r"""(?:
    (?: %(rfc5322_CFWS)s )? 
    %(DQUOTE)s (?: (?: %(rfc5322_FWS)s )? %(qcontent)s )* (?: %(rfc5322_FWS)s )? %(DQUOTE)s 
    (?: %(rfc5322_CFWS)s )? )
""" % locals()


domain = r"(?: %(rfc5322_dot_atom_text)s | (?: \[ %(dtext_no_obs)s* \] ) )" % locals()


local_part = r"(?: %(rfc5322_dot_atom_text)s | %(rfc5322_quoted_string)s )" % locals()


addr_spec = r"(?: %(local_part)s @ %(domain)s )" % locals()

# hfvalue      = *qchar

hfvalue = r"(?: %(qchar)s* )" % locals()

# hfname       = *qchar

hfname = r"(?: %(qchar)s* )" % locals()


hfield = r"(?: %(hfname)s = %(hfvalue)s )" % locals()


to = r"(?: %(addr_spec)s (?: , %(addr_spec)s )* )" % locals()


hfields = r"(?: \? %(hfield)s (?: & %(hfield)s )* )" % locals()

# mailtoURI    = "mailto:" [ to ] [ hfields ]

mailto_URI = r"(?: mailto : (?: %(to)s )? (?: %(hfields)s )? )" % locals()


rfc2045_token = r"(?: [\x30-\x7A]+ )"
rfc2045_ietf_token = rfc2045_token
rfc2045_iana_tokens = rfc2045_token


rfc2045_x_token = r"(?: [xX] - %(rfc2045_token)s )" % locals()


rfc2045_extension_token = r"(?: %(rfc2045_ietf_token)s | %(rfc2045_x_token)s )" % locals()


rfc2045_discrete_type = r"(?: text | image | audio | video | application | %(rfc2045_extension_token)s )" % locals()


rfc2045_composite_type = r"(?: message | multipart | %(rfc2045_extension_token)s )" % locals()


rfc2045_type = r"(?: %(rfc2045_discrete_type)s | %(rfc2045_composite_type)s )" % locals()


rfc2045_subtype = r"(?: %(rfc2045_extension_token)s | %(rfc2045_iana_tokens)s )" % locals()

#

rfc2045_quoted_string = r"(?: )"
rfc2045_attribute = r"(?: %(rfc2045_token)s )" % locals()
rfc2045_value = r"(?: %(rfc2045_token)s | %(rfc2045_quoted_string)s )" % locals()
rfc2045_parameter = r"(?: %(rfc2045_attribute)s = %(rfc2045_value)s )" % locals()


mediatype = r"""(?: 
                    (?: %(rfc2045_type)s / %(rfc2045_subtype)s )? 
                    (?: ; %(rfc2045_parameter)s )*
                )""" % locals()

# uric          = reserved | unreserved | escaped  // 2396

rfc2396_uric = r"(?: %(reserved)s | %(unreserved)s | %(pct_encoded)s )" % locals()
data = r"(?: %(rfc2396_uric)s* )" % locals()


data_URI = r"(?: data : (?: %(mediatype)s )? (?: ;base64 )? , %(data)s )" % locals()


gopher_path = path
gopher_URI = r"(?: gopher :// %(host)s : %(port)s / %(gopher_path)s )" % locals()


file_f_scheme = r"(?: file )"


file_f_auth = r"(?: (?: %(userinfo)s @ )? %(host)s )" % locals()


file_unc_path = r"(?: /{2,3} %(authority)s %(path_absolute)s )" % locals()


file_drive_marker = r"(?: : | \| )"


file_drive_letter = r"(?: %(ALPHA)s (?: %(file_drive_marker)s )? )" % locals()


file_windows_path = r"(?: %(file_drive_letter)s %(path_absolute)s )" % locals()


file_local_path = r"(?: %(path_absolute)s | %(file_windows_path)s )" % locals()


file_auth_path = r"""(?: 
                          (?: %(file_f_auth)s? %(path_absolute)s ) 
                          | %(file_unc_path)s 
                          | %(file_windows_path)s 
                       )""" % locals()


file_f_hier_part = r"(?: (?: // %(file_auth_path)s ) | %(file_local_path)s )" % locals()


file_URI = r"(?: %(file_f_scheme)s : %(file_f_hier_part)s (?: \? %(query)s )? )" % locals()
URI_SCHEMES = [
    "aaa",
    "aaas",
    "about",
    "acap",
    "acct",
    "acd",
    "acr",
    "adiumxtra",
    "adt",
    "afp",
    "afs",
    "aim",
    "amss",
    "android",
    "appdata",
    "apt",
    "ark",
    "attachment",
    "aw",
    "barion",
    "beshare",
    "bitcoin",
    "bitcoincash",
    "blob",
    "bolo",
    "browserext",
    "cabal",
    "calculator",
    "callto",
    "cap",
    "cast",
    "casts",
    "chrome",
    "chrome-extension",
    "cid",
    "coap",
    "coap+tcp",
    "coap+ws",
    "coaps",
    "coaps+tcp",
    "coaps+ws",
    "com-eventbrite-attendee",
    "content",
    "conti",
    "crid",
    "cvs",
    "dab",
    "dat",
    "data",
    "dav",
    "diaspora",
    "dict",
    "did",
    "dis",
    "dlna-playcontainer",
    "dlna-playsingle",
    "dns",
    "dntp",
    "doi",
    "dpp",
    "drm",
    "drop",
    "dtmi",
    "dtn",
    "dvb",
    "dweb",
    "ed2k",
    "elsi",
    "ens",
    "ethereum",
    "example",
    "facetime",
    "fax",
    "feed",
    "feedready",
    "file",
    "filesystem",
    "finger",
    "first-run-pen-experience",
    "fish",
    "fm",
    "ftp",
    "fuchsia-pkg",
    "geo",
    "gg",
    "git",
    "gizmoproject",
    "go",
    "gopher",
    "graph",
    "gtalk",
    "h323",
    "ham",
    "hcap",
    "hcp",
    "http",
    "https",
    "hxxp",
    "hxxps",
    "hydrazone",
    "hyper",
    "iax",
    "icap",
    "icon",
    "im",
    "imap",
    "info",
    "iotdisco",
    "ipfs",
    "ipn",
    "ipns",
    "ipp",
    "ipps",
    "irc",
    "irc6",
    "ircs",
    "iris",
    "iris.beep",
    "iris.lwz",
    "iris.xpc",
    "iris.xpcs",
    "isostore",
    "itms",
    "jabber",
    "jar",
    "jms",
    "keyparc",
    "lastfm",
    "lbry",
    "ldap",
    "ldaps",
    "leaptofrogans",
    "lorawan",
    "lvlt",
    "magnet",
    "mailserver",
    "mailto",
    "maps",
    "market",
    "matrix",
    "message",
    "microsoft.windows.camera",
    "microsoft.windows.camera.multipicker",
    "microsoft.windows.camera.picker",
    "mid",
    "mms",
    "modem",
    "mongodb",
    "moz",
    "ms-access",
    "ms-browser-extension",
    "ms-calculator",
    "ms-drive-to",
    "ms-enrollment",
    "ms-excel",
    "ms-eyecontrolspeech",
    "ms-gamebarservices",
    "ms-gamingoverlay",
    "ms-getoffice",
    "ms-help",
    "ms-infopath",
    "ms-inputapp",
    "ms-lockscreencomponent-config",
    "ms-media-stream-id",
    "ms-mixedrealitycapture",
    "ms-mobileplans",
    "ms-officeapp",
    "ms-people",
    "ms-project",
    "ms-powerpoint",
    "ms-publisher",
    "ms-restoretabcompanion",
    "ms-screenclip",
    "ms-screensketch",
    "ms-search",
    "ms-search-repair",
    "ms-secondary-screen-controller",
    "ms-secondary-screen-setup",
    "ms-settings",
    "ms-settings-airplanemode",
    "ms-settings-bluetooth",
    "ms-settings-camera",
    "ms-settings-cellular",
    "ms-settings-cloudstorage",
    "ms-settings-connectabledevices",
    "ms-settings-displays-topology",
    "ms-settings-emailandaccounts",
    "ms-settings-language",
    "ms-settings-location",
    "ms-settings-lock",
    "ms-settings-nfctransactions",
    "ms-settings-notifications",
    "ms-settings-power",
    "ms-settings-privacy",
    "ms-settings-proximity",
    "ms-settings-screenrotation",
    "ms-settings-wifi",
    "ms-settings-workplace",
    "ms-spd",
    "ms-sttoverlay",
    "ms-transit-to",
    "ms-useractivityset",
    "ms-virtualtouchpad",
    "ms-visio",
    "ms-walk-to",
    "ms-whiteboard",
    "ms-whiteboard-cmd",
    "ms-word",
    "msnim",
    "msrp",
    "msrps",
    "mss",
    "mtqp",
    "mumble",
    "mupdate",
    "mvn",
    "news",
    "nfs",
    "ni",
    "nih",
    "nntp",
    "notes",
    "num",
    "ocf",
    "oid",
    "onenote",
    "onenote-cmd",
    "opaquelocktoken",
    "openpgp4fpr",
    "otpauth",
    "pack",
    "palm",
    "paparazzi",
    "payment",
    "payto",
    "pkcs11",
    "platform",
    "pop",
    "pres",
    "prospero",
    "proxy",
    "pwid",
    "psyc",
    "pttp",
    "qb",
    "query",
    "quic-transport",
    "redis",
    "rediss",
    "reload",
    "res",
    "resource",
    "rmi",
    "rsync",
    "rtmfp",
    "rtmp",
    "rtsp",
    "rtsps",
    "rtspu",
    "secondlife",
    "secret-token",
    "service",
    "session",
    "sftp",
    "sgn",
    "shttp",
    "sieve",
    "simpleledger",
    "sip",
    "sips",
    "skype",
    "smb",
    "sms",
    "smtp",
    "snews",
    "snmp",
    "soap.beep",
    "soap.beeps",
    "soldat",
    "spiffe",
    "spotify",
    "ssb",
    "ssh",
    "steam",
    "stun",
    "stuns",
    "submit",
    "swh",
    "svn",
    "tag",
    "teamspeak",
    "tel",
    "teliaeid",
    "telnet",
    "tftp",
    "things",
    "thismessage",
    "tip",
    "tn3270",
    "tool",
    "turn",
    "turns",
    "tv",
    "udp",
    "unreal",
    "upt",
    "urn",
    "ut2004",
    "v-event",
    "vemmi",
    "ventrilo",
    "videotex",
    "vnc",
    "view-source",
    "vscode",
    "vscode-insiders",
    "vsls",
    "wais",
    "wcr",
    "webcal",
    "wifi",
    "wpid",
    "ws",
    "wss",
    "wtai",
    "wyciwyg",
    "xcon",
    "xcon-userid",
    "xfire",
    "xmlrpc.beep",
    "xmlrpc.beeps",
    "xmpp",
    "xri",
    "ymsgr",
    "z39.50",
    "z39.50r",
    "z39.50s",
]
