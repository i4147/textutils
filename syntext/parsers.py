import re
import sys
import html
import html.parser
from . import nodes
from . import utils


class HeadingParser:
    def __call__(self, stream, meta):
        match = re.match(r"([#]{1,6})[ ]+", stream.peek())
        if match:
            tag = "h" + str(len(match.group(1)))
            line = stream.next()
            text = line.strip("#").strip()
            if re.fullmatch(r"[-=─]+", text):
                return True, None
            else:
                return True, nodes.Node(tag).append_child(nodes.TextNode(text))
        else:
            return False, None


class FancyHeadingParser:
    def __call__(self, stream, meta):
        if not re.fullmatch(r"-+", stream.peek()):
            return False, None
        line1 = stream.next()
        if stream.has_next():
            line2 = stream.next()
        else:
            stream.rewind(1)
            return False, None
        if stream.has_next():
            line3 = stream.next()
        else:
            stream.rewind(2)
            return False, None
        if re.fullmatch(r"-+", line3):
            match = re.match(r"([#]{1,6})[ ]+", line2)
            if match:
                text = nodes.TextNode(line2.strip("#").strip())
                tag = "h" + str(len(match.group(1)))
                return True, nodes.Node(tag).append_child(text)
        else:
            stream.rewind(3)
            return False, None


class IndentedCodeParser:
    def __call__(self, stream, meta):
        if stream.peek().startswith("    "):
            lines = utils.LineStream()
            while stream.has_next():
                nextline = stream.peek()
                if nextline == "" or nextline.startswith("    "):
                    lines.append(stream.next())
                else:
                    break
            text = str(lines.dedent().trim())
            text = html.escape(text, quote=False)
            return True, nodes.Node("pre", text=text)
        return False, None


class TextParser:
    def __call__(self, stream, meta):
        return True, nodes.TextNode(stream.next())


class CompactUListParser:
    def __call__(self, stream, meta):
        match = re.fullmatch(r"[ ]{0,3}([*•+-])([ ].+)?", stream.peek())
        if not match:
            return False, None
        marker = match.group(1)
        re_header = r"[ ]{0,3}[%s]([ ].+)?" % marker
        items = []
        while stream.has_next():
            match = re.fullmatch(re_header, stream.peek())
            if match:
                stream.next()
                item = utils.LineStream()
                items.append(item)
                while stream.has_next():
                    if re.fullmatch(re_header, stream.peek()):
                        break
                    elif stream.peek().startswith(" ") or stream.peek() == "":
                        item.append(stream.next())
                    else:
                        break
                item.dedent()
                if match.group(1):
                    item.prepend(match.group(1).strip())
            else:
                break
        parsers = (CompactUListParser(), CompactOListParser(), TextParser())
        ul = nodes.Node("ul")
        for item in items:
            li = nodes.Node("li")
            li.children = Parser(parsers).parse(item.trim(), meta)
            ul.append_child(li)
        return True, ul


class BlockUListParser:
    def __call__(self, stream, meta):
        match = re.match(r"^[(]([*•+-])[)]", stream.peek())
        if not match:
            return False, None
        marker = match.group(1)
        re_header = r"[(][%s][)]([ ].+)?" % marker
        items = []
        while stream.has_next():
            match = re.fullmatch(re_header, stream.peek())
            if match:
                stream.next()
                item = utils.LineStream()
                items.append(item)
                while stream.has_next():
                    if re.fullmatch(re_header, stream.peek()):
                        break
                    elif stream.peek().startswith(" ") or stream.peek() == "":
                        item.append(stream.next())
                    else:
                        break
                item.dedent()
                if match.group(1):
                    item.prepend(match.group(1).strip())
            else:
                break
        ul = nodes.Node("ul")
        for item in items:
            li = nodes.Node("li")
            li.children = BlockParser().parse(item.trim(), meta)
            ul.append_child(li)
        return True, ul


class CompactOListParser:
    def __call__(self, stream, meta):
        match = re.fullmatch(r"[ ]{0,3}([#]|\d+)[.]([ ].+)?", stream.peek())
        if not match:
            return False, None
        marker = match.group(1)
        if marker == "#":
            re_header = r"[ ]{0,3}[#][.]([ ].+)?"
        else:
            re_header = r"[ ]{0,3}\d+[.]([ ].+)?"
        attributes = None if marker in ("#", "1") else {"start": marker}
        items = []
        while stream.has_next():
            match = re.fullmatch(re_header, stream.peek())
            if match:
                stream.next()
                item = utils.LineStream()
                items.append(item)
                while stream.has_next():
                    if re.fullmatch(re_header, stream.peek()):
                        break
                    elif stream.peek().startswith(" ") or stream.peek() == "":
                        item.append(stream.next())
                    else:
                        break
                item.dedent()
                if match.group(1):
                    item.prepend(match.group(1).strip())
            else:
                break
        parsers = (CompactUListParser(), CompactOListParser(), TextParser())
        ol = nodes.Node("ol", attributes)
        for item in items:
            li = nodes.Node("li")
            li.children = Parser(parsers).parse(item.trim(), meta)
            ol.append_child(li)
        return True, ol


class BlockOListParser:
    def __call__(self, stream, meta):
        match = re.match(r"^[(]([#]|\d+)[)]", stream.peek())
        if not match:
            return False, None
        marker = match.group(1)
        if marker == "#":
            re_header = r"[(][#][)]([ ].+)?"
        else:
            re_header = r"[(]\d+[)]([ ].+)?"
        attributes = None if marker in ("#", "1") else {"start": marker}
        items = []
        while stream.has_next():
            match = re.fullmatch(re_header, stream.peek())
            if match:
                stream.next()
                item = utils.LineStream()
                items.append(item)
                while stream.has_next():
                    if re.fullmatch(re_header, stream.peek()):
                        break
                    elif stream.peek().startswith(" ") or stream.peek() == "":
                        item.append(stream.next())
                    else:
                        break
                item.dedent()
                if match.group(1):
                    item.prepend(match.group(1).strip())
            else:
                break
        ol = nodes.Node("ol", attributes)
        for item in items:
            li = nodes.Node("li")
            li.children = BlockParser().parse(item.trim(), meta)
            ol.append_child(li)
        return True, ol


class DefinitionListParser:
    def __call__(self, stream, meta):
        match = re.fullmatch(r"\[\[(.+)\]\]", stream.peek())
        if not match:
            return False, None
        dl = nodes.Node("dl")
        while stream.has_next():
            match = re.fullmatch(r"\[\[(.+)\]\]", stream.peek())
            if match:
                stream.next()
                div = nodes.Node("div")
                dl.append_child(div)
                termtext = match.group(1).lstrip("[").rstrip("]").strip()
                dt = nodes.Node("dt").append_child(nodes.TextNode(termtext))
                div.append_child(dt)
                definition = utils.LineStream()
                while stream.has_next():
                    if re.fullmatch(r"\[\[(.+)\]\]", stream.peek()):
                        break
                    elif stream.peek().startswith(" ") or stream.peek() == "":
                        definition.append(stream.next())
                    else:
                        break
                dd = nodes.Node("dd")
                dd.children = BlockParser().parse(definition.dedent(), meta)
                div.append_child(dd)
            else:
                break
        return True, dl


class ParagraphParser:
    def __call__(self, stream, meta):
        lines = []
        while stream.has_next():
            if stream.peek() == "":
                break
            lines.append(stream.next())
        text = nodes.TextNode("\n".join(lines))
        return True, nodes.Node("p").append_child(text)


class BlankLineParser:
    def __call__(self, stream, meta):
        if stream.peek() == "":
            stream.next()
            return True, None
        return False, None


class HtmlParser:
    html_block_tags = """
        address article aside blockquote body canvas dd div dl fieldset
        figcaption figure footer form head h1 h2 h3 h4 h5 h6 header hgroup
        li main noscript ol output p pre script section style table tfoot
        title ul video html
    """.split()

    def __call__(self, stream, meta):
        match = re.match(r"<(\w+)[^>]*?>", stream.peek())
        if match and match.group(1) in self.html_block_tags:
            tag = match.group(1)
        else:
            return False, None
        first_line = stream.next()
        lines = [first_line]
        html_parser = HtmlBlockTagParser(tag)
        html_parser.feed(first_line)
        if html_parser.done:
            return True, nodes.Node(text=first_line)
        while stream.has_next():
            line = stream.next()
            lines.append(line)
            html_parser.feed(line)
            if html_parser.done:
                return True, nodes.Node(text="\n".join(lines))
        raise utils.SyntextError("Missing block-level HTML closing tag '</%s>'." % tag)


class HtmlBlockTagParser(html.parser.HTMLParser):
    def __init__(self, tag):
        super().__init__()
        self.tag = tag
        self.stack = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if tag == self.tag:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == self.tag:
            self.stack.pop()
        if len(self.stack) == 0:
            self.done = True


class LinkRefParser:
    def __call__(self, stream, meta):
        match = re.match(r"\[([^\]]+)\][:][ ]*(\S+)?", stream.peek())
        if match:
            stream.next()
        else:
            return False, None
        ref = match.group(1).lower()
        url = match.group(2) or ""
        lines = []
        while stream.has_next():
            if stream.peek().startswith(" ") or stream.peek() == "":
                line = stream.next()
                if line:
                    lines.append(line.strip())
            else:
                break
        if lines and not url:
            url = lines[0]
            lines.pop(0)
        title = " ".join(lines).strip()
        meta.setdefault("linkrefs", {})[ref] = (url, title)
        return True, None


class ShorthandParser:
    def __call__(self, stream, meta):
        match = re.fullmatch(r":([^ ]+)([ ].+)?", stream.peek())
        if match:
            header = stream.next()
        else:
            return False, None
        content = utils.LineStream()
        while stream.has_next():
            if stream.peek().startswith(" ") or stream.peek() == "":
                content.append(stream.next())
            else:
                break
        content = content.trim().dedent()
        if stream.has_next():
            nextline = stream.peek()
            if nextline.startswith(":end") or nextline.startswith(":$"):
                stream.next()
        from . import shorthand

        return True, shorthand.process(header, content, meta)


class TagParser:
    def __call__(self, stream, meta):
        if not stream.peek().startswith("::: "):
            return False, None
        header = stream.next().strip(":")
        elements = header.split(maxsplit=1)
        if len(elements) == 2:
            tag, argstring = elements[0], elements[1]
        elif len(elements) == 1:
            tag, argstring = elements[0], ""
        else:
            tag, argstring = "", ""
        pargs, kwargs = utils.ArgParser().parse(argstring)
        content = utils.LineStream()
        while stream.has_next():
            if stream.peek().startswith(" ") or stream.peek() == "":
                content.append(stream.next())
            else:
                break
        content = content.trim().dedent()
        if stream.has_next():
            nextline = stream.peek()
            if nextline.startswith("::: end") or nextline.startswith("::$"):
                stream.next()
        from . import tags

        return True, tags.process(tag, pargs, kwargs, content, meta)


class Parser:
    def __init__(self, parsers):
        self.parsers = parsers

    def parse(self, stream, meta):
        nodelist = []
        while stream.has_next():
            for parser in self.parsers:
                found_match, result = parser(stream, meta)
                if found_match:
                    if isinstance(result, nodes.Node):
                        nodelist.append(result)
                    break
            if not found_match:
                sys.stderr.write("UNPARSEABLE: %s\n" % stream.next())
        mergedlist = []
        for node in nodelist:
            if mergedlist and isinstance(mergedlist[-1], nodes.TextNode):
                if isinstance(node, nodes.TextNode):
                    mergedlist[-1].text += "\n" + node.text
                    continue
            mergedlist.append(node)
        return mergedlist


class BlockParser(Parser):
    parser_list = [
        BlankLineParser(),
        TagParser(),
        ShorthandParser(),
        IndentedCodeParser(),
        HeadingParser(),
        FancyHeadingParser(),
        CompactUListParser(),
        BlockUListParser(),
        CompactOListParser(),
        BlockOListParser(),
        DefinitionListParser(),
        LinkRefParser(),
        HtmlParser(),
        ParagraphParser(),
    ]

    def __init__(self):
        self.parsers = self.parser_list


class InlineParser(Parser):
    parser_list = [
        TagParser(),
        ShorthandParser(),
        TextParser(),
    ]

    def __init__(self):
        self.parsers = self.parser_list
