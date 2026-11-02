import html
import hashlib
import re

re_italic_sc = re.compile(r"\*(\S)\*")
re_italic_mc = re.compile(r"\*(\S.*?\S)\*", re.DOTALL)
re_bold_sc = re.compile(r"\*{2}(\S)\*{2}")
re_bold_mc = re.compile(r"\*{2}(\S.*?\S)\*{2}", re.DOTALL)
re_bolditalic_sc = re.compile(r"\*{3}(\S)\*{3}")
re_bolditalic_mc = re.compile(r"\*{3}(\S.*?\S)\*{3}", re.DOTALL)
re_backticks = re.compile(r"`(.+?)`", re.DOTALL)
re_link = re.compile(r"\[([^\]]+)\]\(([^\)]+)\)")
re_ref_link = re.compile(r"\[([^\]]+)\]\[([^\]]*)\]")
re_img = re.compile(r"!\[([^\]]*)\]\(([^\)]+)\)")
re_ref_img = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
re_footnote_super = re.compile(r"\[\^([^\]]*?)\]")
re_footnote_span = re.compile(r"\[fn:?([^\]]*?)\]")
re_entity = re.compile(r"&[#a-zA-Z0-9]+;")
re_html_tag = re.compile(r"<([a-zA-Z/][^>]*?|!--.*?--)>")
re_bracketed_url = re.compile(r"<((?:https?|ftp)://[^>]+)>")
re_bare_url = re.compile(
    r"""
    (^|\s)
    (https?|ftp)
    (://[-A-Z0-9+&@#/%?=~_|\[\]\(\)!:,\.;]*[-A-Z0-9+&@#/%=~_|\[\]])
    ($|\W)
    """,
    re.VERBOSE | re.MULTILINE | re.IGNORECASE,
)
re_ndash = re.compile(r"((?<=\s)|\b|^)--(?=[ ]|\b|$)", re.MULTILINE)
re_mdash = re.compile(r"((?<=\s)|\b|^)---(?=[ ]|\b|$)", re.MULTILINE)
re_superscript = re.compile(r"\^\{(.+?)\}")
re_subscript = re.compile(r"_\{(.+?)\}")
re_verbatim = re.compile(r"``(.+?)``", re.DOTALL)


def render(text, meta):
    hashes = {}
    text = render_verbatim(text, hashes)
    text = render_backticks(text, hashes)
    text = render_bracketed_urls(text, hashes)
    text = render_inline_html(text, hashes)
    text = render_html_entities(text, hashes)
    text = render_dashes(text, hashes)
    text = html.escape(text, False)
    text = render_bolditalic(text)
    text = render_bold(text)
    text = render_italic(text)
    text = render_footnotes(text, meta)
    text = render_images(text)
    text = render_ref_images(text, meta)
    text = render_links(text)
    text = render_ref_links(text, meta)
    text = render_superscripts(text)
    text = render_subscripts(text)
    if "nl2br" in meta.get("context", []):
        text = text.replace("\n", "<br>\n")
    for key, value in hashes.items():
        text = text.replace(key, value)
    return text


def hashstr(text, hashes):
    digest = hashlib.sha1(text.encode()).hexdigest()
    hashes[digest] = text
    return digest


def render_backticks(text, hashes):
    def callback(match):
        content = html.escape(match.group(1))
        return hashstr("<code>%s</code>" % content, hashes)

    return re_backticks.sub(callback, text)


def render_bracketed_urls(text, hashes):
    def callback(match):
        url = '<a href="%s">%s</a>' % (match.group(1), match.group(1))
        return hashstr(url, hashes)

    return re_bracketed_url.sub(callback, text)


def render_inline_html(text, hashes):
    return re_html_tag.sub(lambda match: hashstr(match.group(), hashes), text)


def render_verbatim(text, hashes):
    return re_verbatim.sub(lambda match: hashstr(match.group(1), hashes), text)


def render_html_entities(text, hashes):
    return re_entity.sub(lambda match: hashstr(match.group(), hashes), text)


def render_dashes(text, hashes):
    text = re_ndash.sub(hashstr("&ndash;", hashes), text)
    text = re_mdash.sub(hashstr("&mdash;", hashes), text)
    return text


def render_bold(text):
    text = re_bold_sc.sub(r"<b>\1</b>", text)
    text = re_bold_mc.sub(r"<b>\1</b>", text)
    return text


def render_italic(text):
    text = re_italic_sc.sub(r"<i>\1</i>", text)
    text = re_italic_mc.sub(r"<i>\1</i>", text)
    return text


def render_bolditalic(text):
    text = re_bolditalic_sc.sub(r"<b><i>\1</i></b>", text)
    text = re_bolditalic_mc.sub(r"<b><i>\1</i></b>", text)
    return text


def render_superscripts(text):
    return re_superscript.sub(r"<sup>\1</sup>", text)


def render_subscripts(text):
    return re_subscript.sub(r"<sub>\1</sub>", text)


def render_images(text):
    def callback(match):
        alt = html.escape(match.group(1))
        url = match.group(2)
        return f'<img alt="{alt}" src="{url}">'

    return re_img.sub(callback, text)


def render_ref_images(text, meta):
    def callback(match):
        alt = html.escape(match.group(1))
        ref = match.group(2).lower() if match.group(2) else alt.lower()
        url, title = meta.get("linkrefs", {}).get(ref, ("", ""))
        if title:
            title = html.escape(title)
            return '<img alt="%s" src="%s" title="%s">' % (alt, url, title)
        else:
            return '<img alt="%s" src="%s">' % (alt, url)

    return re_ref_img.sub(callback, text)


def render_links(text):
    def callback(match):
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}">{text}</a>'

    return re_link.sub(callback, text)


def render_ref_links(text, meta):
    def callback(match):
        text = match.group(1)
        ref = match.group(2).lower() if match.group(2) else text.lower()
        url, title = meta.get("linkrefs", {}).get(ref, ("", ""))
        if title:
            title = html.escape(title)
            return '<a href="%s" title="%s">%s</a>' % (url, title, text)
        else:
            return '<a href="%s">%s</a>' % (url, text)

    return re_ref_link.sub(callback, text)


def render_footnotes(text, meta):
    def callback(match):
        if match.group(1):
            ref = match.group(1)
        else:
            ref = meta.setdefault("footnote-ref-index", 1)
            meta["footnote-ref-index"] += 1
        link = f'<a href="#fn:{ref}">{ref}</a>'
        return f'<{tag} class="footnote" id="fnref:{ref}">{link}</{tag}>'

    tag = "sup"
    text = re_footnote_super.sub(callback, text)
    tag = "span"
    text = re_footnote_span.sub(callback, text)
    return text
