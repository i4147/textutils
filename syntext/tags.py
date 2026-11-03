import html
import re
from . import nodes
from . import parsers
from . import utils

try:
    import pygments
    import pygments.lexers
    import pygments.formatters
except ImportError:
    pygments = None
tagmap = {}


def register(*tags):
    def register_tag_handler(func):
        for tag in tags:
            tagmap[tag] = func
        return func

    return register_tag_handler


def process(tag, pargs, kwargs, line_stream, meta):
    if tag in tagmap:
        node = tagmap[tag](tag, pargs, kwargs, line_stream, meta)
    elif tag == "hr" or re.fullmatch(r"-+", tag):
        node = nodes.Node("hr", kwargs, is_void=True)
    else:
        raise utils.SyntextError("Unrecognized tag '%s'." % tag)
    if "nl2lb" in pargs or "nl2br" in pargs:
        node = nodes.LinebreakNode().append_child(node)
    return node


@register("div")
def div_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.Node("div", kwargs)
    node.children = parsers.BlockParser().parse(line_stream, meta)
    return node


@register("span")
def span_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.Node("span", kwargs)
    node.children = parsers.InlineParser().parse(line_stream, meta)
    return node


@register("link")
def link_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.Node("a", kwargs)
    node.children = parsers.InlineParser().parse(line_stream, meta)
    if not "href" in kwargs:
        node.attributes["href"] = pargs[0] if pargs else ""
    return node


@register("quote")
def quote_tag_handler(tag, pargs, kwargs, line_stream, meta):
    quote = nodes.Node("blockquote", kwargs)
    quote.children = parsers.BlockParser().parse(line_stream, meta)
    if pargs:
        caption = nodes.Node("p")
        caption.add_class("blockquote-caption")
        caption.append_child(nodes.TextNode(pargs[0]))
        wrapper = nodes.Node()
        wrapper.append_child(quote)
        wrapper.append_child(caption)
        return wrapper
    return quote


@register("infobox", "alertbox")
def infobox_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.Node("div", kwargs)
    node.add_class(tag)
    node.children = parsers.BlockParser().parse(line_stream, meta)
    return node


@register("image", "!image")
def image_tag_handler(tag, pargs, kwargs, line_stream, meta):
    image = nodes.Node("img", is_void=True)
    image.attributes["src"] = pargs[0] if pargs else ""
    outernode = image
    if line_stream.has_next() and line_stream.peek().startswith("[") and line_stream.peek().endswith("]"):
        image.attributes["alt"] = html.escape(line_stream.next()[1:-1])
    if tag == "!image":
        link = nodes.Node("a")
        link.attributes["href"] = pargs[0] if pargs else ""
        link.append_child(image)
        outernode = link
    if line_stream.has_next():
        figcaption = nodes.Node("figcaption")
        figcaption.append_child(nodes.TextNode(str(line_stream).strip()))
        figure = nodes.Node("figure")
        figure.append_child(outernode)
        figure.append_child(figcaption)
        outernode = figure
    outernode.attributes.update(kwargs)
    return outernode


@register("comment")
def comment_tag_handler(tag, pargs, kwargs, line_stream, meta):
    return nodes.CommentNode(text=str(line_stream.indent(4)))


@register("raw")
def raw_tag_handler(tag, pargs, kwargs, line_stream, meta):
    return nodes.Node(text=str(line_stream))


@register("code")
def code_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.Node("pre", kwargs)
    lang = pargs[0] if pargs else None
    text = str(line_stream)
    if lang:
        node.attributes["data-lang"] = lang
        node.add_class("lang-%s" % lang)
    if meta.get("pygmentize") and pygments and lang:
        try:
            lexer = pygments.lexers.get_lexer_by_name(lang)
        except pygments.util.ClassNotFound:
            try:
                lexer = pygments.lexers.guess_lexer(text)
            except pygments.util.ClassNotFound:
                lexer = None
        if lexer:
            node.add_class("pygments")
            formatter = pygments.formatters.HtmlFormatter(nowrap=True)
            node.text = pygments.highlight(text, lexer, formatter).strip("\n")
            return node
    node.text = html.escape(text, quote=False)
    return node


@register("insert")
def insert_tag_handler(tag, pargs, kwargs, line_stream, meta):
    node = nodes.InsertNode()
    node.text = pargs[0] if pargs else ""
    return node


@register("table")
def table_tag_handler(tag, pargs, kwargs, line_stream, meta):
    lines = [line.strip("|") for line in line_stream.lines if line]
    alignment = []
    for line in lines:
        match = re.fullmatch(r"[ |-]*[:][ |:-]*", line)
        if match:
            for cell in [cell.strip() for cell in line.split("|")]:
                if cell.startswith(":") and cell.endswith(":"):
                    alignment.append("center")
                elif cell.startswith(":"):
                    alignment.append("left")
                elif cell.endswith(":"):
                    alignment.append("right")
                else:
                    alignment.append(None)
            break
    if lines and re.fullmatch(r"[ |:-]+", lines[0]):
        lines.pop(0)
    if lines and re.fullmatch(r"[ |:-]+", lines[-1]):
        lines.pop()
    header = None
    if len(lines) > 2 and re.fullmatch(r"[ |:-]+", lines[1]):
        header = [cell.strip() for cell in lines[0].split("|")]
        lines = lines[2:]
    footer = None
    if len(lines) > 2 and re.fullmatch(r"[ |:-]+", lines[-2]):
        footer = [cell.strip() for cell in lines[-1].split("|")]
        lines = lines[:-2]
    body = [[cell.strip() for cell in line.split("|")] for line in lines]

    def make_row(cells, tag):
        tr = nodes.Node("tr")
        for index, text in enumerate(cells):
            cell = nodes.Node(tag)
            cell.append_child(nodes.TextNode(text))
            if len(alignment) > index and alignment[index]:
                cell.add_class(alignment[index])
            tr.append_child(cell)
        return tr

    table = nodes.Node("table", kwargs)
    if header:
        thead = nodes.Node("thead")
        thead.append_child(make_row(header, "th"))
        table.append_child(thead)
    if footer:
        tfoot = nodes.Node("tfoot")
        tfoot.append_child(make_row(footer, "th"))
        table.append_child(tfoot)
    tbody = nodes.Node("tbody")
    for row in body:
        tbody.append_child(make_row(row, "td"))
    table.append_child(tbody)
    return table


@register("footnote")
def footnote_tag_handler(tag, pargs, kwargs, line_stream, meta):
    ref = pargs[0] if pargs else ""
    if not ref:
        ref = str(meta.setdefault("footnote-index", 1))
        meta["footnote-index"] += 1
    footnote = nodes.Node("div", {"id": "fn:%s" % ref})
    link = nodes.Node("a", {"href": "#fnref:%s" % ref})
    link.append_child(nodes.TextNode(ref))
    index = nodes.Node("dt")
    index.append_child(link)
    footnote.append_child(index)
    body = nodes.Node("dd")
    body.children = parsers.BlockParser().parse(line_stream, meta)
    footnote.append_child(body)
    if not "footnotes" in meta:
        meta["footnotes"] = nodes.Node("dl", {"class": "footnotes"})
    meta["footnotes"].append_child(footnote)
    return None
