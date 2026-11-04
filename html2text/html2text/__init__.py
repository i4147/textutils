import html.entities
import html.parser
import re
import string
import urllib.parse as urlparse
from textwrap import wrap
from typing import Dict, List, Optional, Tuple, Union

from . import config
from ._typing import OutCallback
from ._version import __version_tuple__
from .elements import AnchorElement, ListElement
from .utils import (
    control_character_replacements,
    dumb_css_parser,
    element_style,
    escape_md,
    escape_md_section,
    google_fixed_width_font,
    google_has_height,
    google_list_style,
    google_text_emphasis,
    hn,
    list_numbering_start,
    pad_tables_in_text,
    skipwrap,
    unifiable_n,
)

__version__ = __version_tuple__


class HTML2Text(html.parser.HTMLParser):
    def __init__(
        self,
        out: Optional[OutCallback] = None,
        baseurl: str = "",
        bodywidth: int = config.BODY_WIDTH,
    ) -> None:
        super().__init__(convert_charrefs=False)

        self.split_next_td = False
        self.td_count = 0
        self.table_start = False
        self.unicode_snob = config.UNICODE_SNOB
        self.escape_snob = config.ESCAPE_SNOB
        self.links_each_paragraph = config.LINKS_EACH_PARAGRAPH
        self.body_width = bodywidth
        self.skip_internal_links = config.SKIP_INTERNAL_LINKS
        self.inline_links = config.INLINE_LINKS
        self.protect_links = config.PROTECT_LINKS
        self.google_list_indent = config.GOOGLE_LIST_INDENT
        self.ignore_links = config.IGNORE_ANCHORS
        self.ignore_mailto_links = config.IGNORE_MAILTO_LINKS
        self.ignore_images = config.IGNORE_IMAGES
        self.images_as_html = config.IMAGES_AS_HTML
        self.images_to_alt = config.IMAGES_TO_ALT
        self.images_with_size = config.IMAGES_WITH_SIZE
        self.ignore_emphasis = config.IGNORE_EMPHASIS
        self.bypass_tables = config.BYPASS_TABLES
        self.ignore_tables = config.IGNORE_TABLES
        self.google_doc = False
        self.ul_item_mark = "*"
        self.emphasis_mark = "_"
        self.strong_mark = "**"
        self.single_line_break = config.SINGLE_LINE_BREAK
        self.use_automatic_links = config.USE_AUTOMATIC_LINKS
        self.hide_strikethrough = False
        self.mark_code = config.MARK_CODE
        self.backquote_code_style = config.BACKQUOTE_CODE_STYLE
        self.wrap_list_items = config.WRAP_LIST_ITEMS
        self.wrap_links = config.WRAP_LINKS
        self.wrap_tables = config.WRAP_TABLES
        self.pad_tables = config.PAD_TABLES
        self.default_image_alt = config.DEFAULT_IMAGE_ALT
        self.tag_callback = None
        self.open_quote = config.OPEN_QUOTE
        self.close_quote = config.CLOSE_QUOTE
        self.include_sup_sub = config.INCLUDE_SUP_SUB

        if out is None:
            self.out = self.outtextf
        else:
            self.out = out

        self.outtextlist: List[str] = []

        self.quiet = 0
        self.p_p = 0
        self.outcount = 0
        self.start = True
        self.space = False
        self.a: List[AnchorElement] = []
        self.astack: List[Optional[Dict[str, Optional[str]]]] = []
        self.maybe_automatic_link: Optional[str] = None
        self.empty_link = False
        self.absolute_url_matcher = re.compile(r"^[a-zA-Z+]+://")
        self.acount = 0
        self.list: List[ListElement] = []
        self.blockquote = 0
        self.pre = False
        self.startpre = False
        self.pre_indent = ""
        self.list_code_indent = ""
        self.code = False
        self.quote = False
        self.br_toggle = ""
        self.lastWasNL = False
        self.lastWasList = False
        self.style = 0
        self.style_def: Dict[str, Dict[str, str]] = {}
        self.tag_stack: List[Tuple[str, Dict[str, Optional[str]], Dict[str, str]]] = []
        self.emphasis = 0
        self.drop_white_space = 0
        self.inheader = False
        self.abbr_title: Optional[str] = None
        self.abbr_data: Optional[str] = None
        self.abbr_list: Dict[str, str] = {}
        self.baseurl = baseurl
        self.stressed = False
        self.preceding_stressed = False
        self.preceding_data = ""
        self.current_tag = ""

        config.UNIFIABLE["nbsp"] = "&nbsp_place_holder;"

    def feed(self, data: str) -> None:
        data = data.replace("</' + 'script>", "</ignore>")
        super().feed(data)

    def handle(self, data: str) -> str:
        self.start = True
        self.feed(data)
        self.feed("")
        markdown = self.optwrap(self.finish())
        if self.pad_tables:
            return pad_tables_in_text(markdown)
        else:
            return markdown

    def outtextf(self, s: str) -> None:
        self.outtextlist.append(s)
        if s:
            self.lastWasNL = s[-1] == "\n"

    def finish(self) -> str:
        self.close()

        self.pbr()
        self.o("", force="end")

        outtext = "".join(self.outtextlist)

        if self.unicode_snob:
            nbsp = html.entities.html5["nbsp;"]
        else:
            nbsp = " "
        outtext = outtext.replace("&nbsp_place_holder;", nbsp)

        self.outtextlist = []

        return outtext

    def handle_charref(self, c: str) -> None:
        self.handle_data(self.charref(c), True)

    def handle_entityref(self, c: str) -> None:
        ref = self.entityref(c)

        if ref:
            self.handle_data(ref, True)

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.handle_tag(tag, dict(attrs), start=True)

    def handle_endtag(self, tag: str) -> None:
        self.handle_tag(tag, {}, start=False)

    def previousIndex(self, attrs: Dict[str, Optional[str]]) -> Optional[int]:
        if "href" not in attrs:
            return None

        match = False
        for i, a in enumerate(self.a):
            if "href" in a.attrs and a.attrs["href"] == attrs["href"]:
                if "title" in a.attrs or "title" in attrs:
                    if "title" in a.attrs and "title" in attrs and a.attrs["title"] == attrs["title"]:
                        match = True
                else:
                    match = True

            if match:
                return i
        return None

    def handle_emphasis(self, start: bool, tag_style: Dict[str, str], parent_style: Dict[str, str]) -> None:
        tag_emphasis = google_text_emphasis(tag_style)
        parent_emphasis = google_text_emphasis(parent_style)

        strikethrough = "line-through" in tag_emphasis and self.hide_strikethrough

        bold = False
        for bold_marker in config.BOLD_TEXT_STYLE_VALUES:
            bold = bold_marker in tag_emphasis and bold_marker not in parent_emphasis
            if bold:
                break

        italic = "italic" in tag_emphasis and "italic" not in parent_emphasis
        fixed = google_fixed_width_font(tag_style) and not google_fixed_width_font(parent_style) and not self.pre

        if start:
            if bold or italic or fixed:
                self.emphasis += 1
            if strikethrough:
                self.quiet += 1
            if italic:
                self.o(self.emphasis_mark)
                self.drop_white_space += 1
            if bold:
                self.o(self.strong_mark)
                self.drop_white_space += 1
            if fixed:
                self.o("`")
                self.drop_white_space += 1
                self.code = True
        else:
            if bold or italic or fixed:
                self.emphasis -= 1
                self.space = False
            if fixed:
                if self.drop_white_space:
                    self.drop_white_space -= 1
                else:
                    self.o("`")
                self.code = False
            if bold:
                if self.drop_white_space:
                    self.drop_white_space -= 1
                else:
                    self.o(self.strong_mark)
            if italic:
                if self.drop_white_space:
                    self.drop_white_space -= 1
                else:
                    self.o(self.emphasis_mark)
            if (bold or italic) and not self.emphasis:
                self.o(" ")
            if strikethrough:
                self.quiet -= 1

    def handle_tag(self, tag: str, attrs: Dict[str, Optional[str]], start: bool) -> None:
        self.current_tag = tag

        if self.tag_callback is not None:
            if self.tag_callback(self, tag, attrs, start) is True:
                return

        if (
            start
            and self.maybe_automatic_link is not None
            and tag not in ["p", "div", "style", "dl", "dt"]
            and (tag != "img" or self.ignore_images)
        ):
            self.o("[")
            self.maybe_automatic_link = None
            self.empty_link = False

        if self.google_doc:
            parent_style: Dict[str, str] = {}
            if start:
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]
                tag_style = element_style(attrs, self.style_def, parent_style)
                self.tag_stack.append((tag, attrs, tag_style))
            else:
                dummy, attrs, tag_style = self.tag_stack.pop() if self.tag_stack else (None, {}, {})
                if self.tag_stack:
                    parent_style = self.tag_stack[-1][2]

        if hn(tag):
            if self.astack:
                if start:
                    self.inheader = True
                    if self.outtextlist and self.outtextlist[-1] == "[":
                        self.outtextlist.pop()
                        self.space = False
                        self.o(hn(tag) * "#" + " ")
                        self.o("[")
                else:
                    self.p_p = 0
                    self.inheader = False
                    return
            else:
                self.p()
                if start:
                    self.inheader = True
                    self.o(hn(tag) * "#" + " ")
                else:
                    self.inheader = False
                    return

        if tag in ["p", "div"]:
            if self.google_doc:
                if start and google_has_height(tag_style):
                    self.p()
                else:
                    self.soft_br()
            elif self.astack:
                pass
            elif self.split_next_td:
                pass
            else:
                self.p()

        if tag == "br" and start:
            if self.blockquote > 0:
                self.o("  \n> ")
            else:
                self.o("  \n")

        if tag == "hr" and start:
            self.p()
            self.o("* * *")
            self.p()

        if tag in ["head", "style", "script"]:
            if start:
                self.quiet += 1
            else:
                self.quiet -= 1

        if tag == "style":
            if start:
                self.style += 1
            else:
                self.style -= 1

        if tag in ["body"]:
            self.quiet = 0

        if tag == "blockquote":
            if start:
                self.p()
                self.o("> ", force=True)
                self.start = True
                self.blockquote += 1
            else:
                self.blockquote -= 1
                self.p()

        if tag in ["em", "i", "u"] and not self.ignore_emphasis:
            if (
                start
                and self.preceding_data
                and self.preceding_data[-1] not in string.whitespace
                and self.preceding_data[-1] not in string.punctuation
            ):
                emphasis = " " + self.emphasis_mark
                self.preceding_data += " "
            else:
                emphasis = self.emphasis_mark

            self.o(emphasis)
            if start:
                self.stressed = True

        if tag in ["strong", "b"] and not self.ignore_emphasis:
            if (
                start
                and self.preceding_data
                and len(self.strong_mark) > 0
                and self.preceding_data[-1] == self.strong_mark[0]
            ):
                strong = " " + self.strong_mark
                self.preceding_data += " "
            else:
                strong = self.strong_mark

            self.o(strong)
            if start:
                self.stressed = True

        if tag in ["del", "strike", "s"]:
            if start and self.preceding_data and self.preceding_data[-1] == "~":
                strike = " ~~"
                self.preceding_data += " "
            else:
                strike = "~~"

            self.o(strike)
            if start:
                self.stressed = True

        if self.google_doc:
            if not self.inheader:
                self.handle_emphasis(start, tag_style, parent_style)

        if tag in ["kbd", "code", "tt"] and not self.pre:
            self.o("`")
            self.code = not self.code

        if tag == "abbr":
            if start:
                self.abbr_title = None
                self.abbr_data = ""
                if "title" in attrs:
                    self.abbr_title = attrs["title"]
            else:
                if self.abbr_title is not None:
                    assert self.abbr_data is not None
                    self.abbr_list[self.abbr_data] = self.abbr_title
                    self.abbr_title = None
                self.abbr_data = None

        if tag == "q":
            if not self.quote:
                self.o(self.open_quote)
            else:
                self.o(self.close_quote)
            self.quote = not self.quote

        def link_url(self: HTML2Text, link: str, title: str = "") -> None:
            url = urlparse.urljoin(self.baseurl, link)
            title = ' "{}"'.format(title) if title.strip() else ""
            self.o("]({url}{title})".format(url=escape_md(url), title=title))

        if tag == "a" and not self.ignore_links:
            if start:
                if (
                    "href" in attrs
                    and attrs["href"] is not None
                    and not (self.skip_internal_links and attrs["href"].startswith("#"))
                    and not (self.ignore_mailto_links and attrs["href"].startswith("mailto:"))
                ):
                    self.astack.append(attrs)
                    self.maybe_automatic_link = attrs["href"]
                    self.empty_link = True
                    if self.protect_links:
                        attrs["href"] = "<" + attrs["href"] + ">"
                else:
                    self.astack.append(None)
            else:
                if self.astack:
                    a = self.astack.pop()
                    if self.maybe_automatic_link and not self.empty_link:
                        self.maybe_automatic_link = None
                    elif a:
                        assert a["href"] is not None
                        if self.empty_link:
                            self.o("[")
                            self.empty_link = False
                            self.maybe_automatic_link = None
                        if self.inline_links:
                            self.p_p = 0
                            title = a.get("title") or ""
                            title = escape_md(title)
                            link_url(self, a["href"], title)
                        else:
                            i = self.previousIndex(a)
                            if i is not None:
                                a_props = self.a[i]
                            else:
                                self.acount += 1
                                a_props = AnchorElement(a, self.acount, self.outcount)
                                self.a.append(a_props)
                            self.o("][" + str(a_props.count) + "]")

        if tag == "img" and start and not self.ignore_images:
            if "src" in attrs and attrs["src"] is not None:
                if not self.images_to_alt:
                    attrs["href"] = attrs["src"]
                alt = attrs.get("alt") or self.default_image_alt

                if self.images_as_html or (self.images_with_size and ("width" in attrs or "height" in attrs)):
                    self.o("<img src='" + attrs["src"] + "' ")
                    if "width" in attrs and attrs["width"] is not None:
                        self.o("width='" + attrs["width"] + "' ")
                    if "height" in attrs and attrs["height"] is not None:
                        self.o("height='" + attrs["height"] + "' ")
                    if alt:
                        self.o("alt='" + alt + "' ")
                    self.o("/>")
                    return

                if self.maybe_automatic_link is not None:
                    href = self.maybe_automatic_link
                    if self.images_to_alt and escape_md(alt) == href and self.absolute_url_matcher.match(href):
                        self.o("<" + escape_md(alt) + ">")
                        self.empty_link = False
                        return
                    else:
                        self.o("[")
                        self.maybe_automatic_link = None
                        self.empty_link = False

                if self.images_to_alt:
                    self.o(escape_md(alt))
                else:
                    self.o("![" + escape_md(alt) + "]")
                    if self.inline_links:
                        href = attrs.get("href") or ""
                        self.o("(" + escape_md(urlparse.urljoin(self.baseurl, href)) + ")")
                    else:
                        i = self.previousIndex(attrs)
                        if i is not None:
                            a_props = self.a[i]
                        else:
                            self.acount += 1
                            a_props = AnchorElement(attrs, self.acount, self.outcount)
                            self.a.append(a_props)
                        self.o("[" + str(a_props.count) + "]")

        if tag == "dl" and start:
            self.p()
        if tag == "dt" and not start:
            self.pbr()
        if tag == "dd" and start:
            self.o("    ")
        if tag == "dd" and not start:
            self.pbr()

        if tag in ["ol", "ul"]:
            if not self.list and not self.lastWasList:
                self.p()
            if start:
                if self.google_doc:
                    list_style = google_list_style(tag_style)
                else:
                    list_style = tag
                numbering_start = list_numbering_start(attrs)
                self.list.append(ListElement(list_style, numbering_start))
            else:
                if self.list:
                    self.list.pop()
                    if not self.google_doc and not self.list:
                        self.o("\n")
            self.lastWasList = True
        else:
            self.lastWasList = False

        if tag == "li":
            self.list_code_indent = ""
            self.pbr()
            if start:
                if self.list:
                    li = self.list[-1]
                else:
                    li = ListElement("ul", 0)
                if self.google_doc:
                    self.o("  " * self.google_nest_count(tag_style))
                else:
                    parent_list = None
                    for list in self.list:
                        self.list_code_indent += "   " if parent_list == "ol" else "  "
                        parent_list = list.name
                    self.o(self.list_code_indent)

                if li.name == "ul":
                    self.list_code_indent += "  "
                    self.o(self.ul_item_mark + " ")
                elif li.name == "ol":
                    li.num += 1
                    self.list_code_indent += "   "
                    self.o(str(li.num) + ". ")
                self.start = True

        if tag in ["table", "tr", "td", "th"]:
            if self.ignore_tables:
                if tag == "tr":
                    if start:
                        pass
                    else:
                        self.soft_br()
                else:
                    pass

            elif self.bypass_tables:
                if start:
                    self.soft_br()
                if tag in ["td", "th"]:
                    if start:
                        self.o("<{}>\n\n".format(tag))
                    else:
                        self.o("\n</{}>".format(tag))
                else:
                    if start:
                        self.o("<{}>".format(tag))
                    else:
                        self.o("</{}>".format(tag))

            else:
                if tag == "table":
                    if start:
                        self.table_start = True
                        if self.pad_tables:
                            self.o("<" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                    else:
                        if self.pad_tables:
                            self.soft_br()
                            self.o("</" + config.TABLE_MARKER_FOR_PAD + ">")
                            self.o("  \n")
                if tag in ["td", "th"] and start:
                    if self.split_next_td:
                        self.o("| ")
                    self.split_next_td = True

                if tag == "tr" and start:
                    self.td_count = 0
                if tag == "tr" and not start:
                    self.split_next_td = False
                    self.soft_br()
                if tag == "tr" and not start and self.table_start:
                    self.o("|".join(["---"] * self.td_count))
                    self.soft_br()
                    self.table_start = False
                if tag in ["td", "th"] and start:
                    self.td_count += 1

        if tag == "pre":
            if start:
                self.startpre = True
                self.pre = True
                self.pre_indent = ""
            else:
                self.pre = False
                if self.backquote_code_style:
                    self.out("\n" + self.pre_indent + "```")
                if self.mark_code:
                    self.out("\n[/code]")
            self.p()

        if tag in ["sup", "sub"] and self.include_sup_sub:
            if start:
                self.o("<{}>".format(tag))
            else:
                self.o("</{}>".format(tag))

    def pbr(self) -> None:
        if self.p_p == 0:
            self.p_p = 1

    def p(self) -> None:
        self.p_p = 1 if self.single_line_break else 2

    def soft_br(self) -> None:
        self.pbr()
        self.br_toggle = "  "

    def o(self, data: str, puredata: bool = False, force: Union[bool, str] = False) -> None:
        if self.abbr_data is not None:
            self.abbr_data += data

        if not self.quiet:
            if self.google_doc:
                # marks ('**' and '_')
                lstripped_data = data.lstrip()
                if self.drop_white_space and not (self.pre or self.code):
                    data = lstripped_data
                if lstripped_data != "":
                    self.drop_white_space = 0

            if puredata and not self.pre:
                data = re.sub(r"\s+", r" ", data)
                if data and data[0] == " ":
                    self.space = True
                    data = data[1:]
            if not data and not force:
                return

            if self.startpre:
                # self.out(" :") #TODO: not output when already one there
                if not data.startswith("\n") and not data.startswith("\r\n"):
                    data = "\n" + data
                if self.mark_code:
                    self.out("\n[code]")
                    self.p_p = 0

            bq = ">" * self.blockquote
            if not (force and data and data[0] == ">") and self.blockquote:
                bq += " "

            if self.pre:
                if self.list:
                    bq += self.list_code_indent

                if not self.backquote_code_style:
                    bq += "    "

                data = data.replace("\n", "\n" + bq)
                self.pre_indent = bq

            if self.startpre:
                self.startpre = False
                if self.backquote_code_style:
                    self.out("\n" + self.pre_indent + "```")
                    self.p_p = 0
                elif self.list:
                    data = data.lstrip("\n" + self.pre_indent)

            if self.start:
                self.space = False
                self.p_p = 0
                self.start = False

            if force == "end":
                self.p_p = 0
                self.out("\n")
                self.space = False

            if self.p_p:
                self.out((self.br_toggle + "\n" + bq) * self.p_p)
                self.space = False
                self.br_toggle = ""

            if self.space:
                if not self.lastWasNL:
                    self.out(" ")
                self.space = False

            if self.a and ((self.p_p == 2 and self.links_each_paragraph) or force == "end"):
                if force == "end":
                    self.out("\n")

                newa = []
                for link in self.a:
                    if self.outcount > link.outcount:
                        self.out("   [" + str(link.count) + "]: " + urlparse.urljoin(self.baseurl, link.attrs["href"]))
                        if "title" in link.attrs and link.attrs["title"] is not None:
                            self.out(" (" + link.attrs["title"] + ")")
                        self.out("\n")
                    else:
                        newa.append(link)

                if self.a != newa:
                    self.out("\n")

                self.a = newa

            if self.abbr_list and force == "end":
                for abbr, definition in self.abbr_list.items():
                    self.out("  *[" + abbr + "]: " + definition + "\n")

            self.p_p = 0
            self.out(data)
            self.outcount += 1

    def handle_data(self, data: str, entity_char: bool = False) -> None:
        if not data:
            return

        if self.stressed:
            data = data.strip()
            self.stressed = False
            self.preceding_stressed = True
        elif self.preceding_stressed:
            if (
                re.match(r"[^][(){}\s.!?]", data[0])
                and not hn(self.current_tag)
                and self.current_tag not in ["a", "code", "pre"]
            ):
                data = " " + data
            self.preceding_stressed = False

        if self.style:
            self.style_def.update(dumb_css_parser(data))

        if self.maybe_automatic_link is not None:
            href = self.maybe_automatic_link
            if href == data and self.absolute_url_matcher.match(href) and self.use_automatic_links:
                self.o("<" + data + ">")
                self.empty_link = False
                return
            else:
                self.o("[")
                self.maybe_automatic_link = None
                self.empty_link = False

        if not self.code and not self.pre and not entity_char:
            data = escape_md_section(data, snob=self.escape_snob)
        self.preceding_data = data
        self.o(data, puredata=True)

    def charref(self, name: str) -> str:
        if name[0] in ["x", "X"]:
            c = int(name[1:], 16)
        else:
            c = int(name)

        if not 0 < c < 0x110000 or 0xD800 <= c < 0xE000:
            c = 0xFFFD
        c = control_character_replacements.get(c, c)

        if not self.unicode_snob and c in unifiable_n:
            return unifiable_n[c]
        else:
            return chr(c)

    def entityref(self, c: str) -> str:
        if not self.unicode_snob and c in config.UNIFIABLE:
            return config.UNIFIABLE[c]
        try:
            ch = html.entities.html5[c + ";"]
        except KeyError:
            return "&" + c + ";"
        return config.UNIFIABLE[c] if c == "nbsp" else ch

    def google_nest_count(self, style: Dict[str, str]) -> int:
        nest_count = 0
        if "margin-left" in style:
            nest_count = int(style["margin-left"][:-2]) // self.google_list_indent

        return nest_count

    def optwrap(self, text: str) -> str:
        if not self.body_width:
            return text

        result = ""
        newlines = 0
        if not self.wrap_links:
            self.inline_links = False
        start_code = False
        for para in text.split("\n"):
            if self.backquote_code_style and para.lstrip().startswith("```"):
                start_code = not start_code
            if start_code:
                result += para + "\n"
            elif len(para) > 0:
                if not skipwrap(para, self.wrap_links, self.wrap_list_items, self.wrap_tables):
                    indent = ""
                    if para.startswith("  " + self.ul_item_mark):
                        indent = "    "
                    elif para.startswith("> "):
                        indent = "> "
                    wrapped = wrap(
                        para,
                        self.body_width,
                        break_long_words=False,
                        subsequent_indent=indent,
                    )
                    result += "\n".join(wrapped)
                    if para.endswith("  "):
                        result += "  \n"
                        newlines = 1
                    elif indent:
                        result += "\n"
                        newlines = 1
                    else:
                        result += "\n\n"
                        newlines = 2
                else:
                    # line.isspace()
                    if not config.RE_SPACE.match(para):
                        result += para + "\n"
                        newlines = 1
            else:
                if newlines < 2:
                    result += "\n"
                    newlines += 1
        return result


def html2text(html: str, baseurl: str = "", bodywidth: Optional[int] = None) -> str:
    if bodywidth is None:
        bodywidth = config.BODY_WIDTH
    h = HTML2Text(baseurl=baseurl, bodywidth=bodywidth)

    return h.handle(html)
