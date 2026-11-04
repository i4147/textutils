import logging
from typing import Callable, Iterable, List, Optional, Tuple

import mwparserfromhell
from mwparserfromhell.nodes import ExternalLink, Heading, Tag, Text, Wikilink
from mwparserfromhell.wikicode import Wikicode

from mwtext.content_transformers.content_transformer import ContentTransformer
from mwtext.content_transformers.util import generate_non_link_namespace_names

logger = logging.getLogger(__name__)


KEEP_NODE_TYPES = (Text, Wikilink, ExternalLink, Tag, Heading)
ALLOWED_TAGS = frozenset([
    "b",
    "i",
    "u",
    "blockquote",
    "p",
    "div",
    "sub",
    "sup",
])


WikilinkParser = Callable[[Wikilink], Tuple[bool, bool, str, str]]


class Wikitext2Structured(ContentTransformer):
    def __init__(
        self,
        forbidden_wikilink_prefixes: Iterable[str] = frozenset(),
        allowed_tags: Iterable[str] = ALLOWED_TAGS,
        include_disallowed_tag_tokens: bool = False,
        custom_wikilink_parser: Optional[WikilinkParser] = None,
        include_external_link_anchors: bool = True,
        max_flattening_rounds: int = 5,
    ) -> None:
        self.forbidden_wikilink_prefixes = forbidden_wikilink_prefixes
        self.allowed_tags = allowed_tags
        self.include_disallowed_tag_tokens = include_disallowed_tag_tokens
        self.custom_wikilink_parser = custom_wikilink_parser
        self.include_external_link_anchors = include_external_link_anchors
        self.max_flattening_rounds = max_flattening_rounds

        self._included_tags = set()
        self._skipped_tags = set()

    @classmethod
    def from_siteinfo(cls, siteinfo, *args, **kwargs):
        forbidden_wikilink_prefixes = generate_non_link_namespace_names(siteinfo)
        return cls(*args, forbidden_wikilink_prefixes=forbidden_wikilink_prefixes, **kwargs)

    def transform(self, wikitext: str) -> dict:
        do_expensive_logging = logger.isEnabledFor(logging.DEBUG)

        parse_state = {
            "section_idx": 0,
            "section_name": "Introduction",
            "current_text": "",
            "current_wikilinks": [],
        }

        wikicode = mwparserfromhell.parse(wikitext.strip())
        filtered_nodes = [node for node in wikicode.nodes if isinstance(node, KEEP_NODE_TYPES)]

        current_nodes = list(filtered_nodes)
        for iround in range(self.max_flattening_rounds):
            flatter_nodes = []
            for node in current_nodes:
                if self.node_is_expandable(node):
                    flatter_nodes.extend(node.contents.nodes)
                else:
                    flatter_nodes.append(node)

            if len(flatter_nodes) == len(current_nodes):
                break

            current_nodes = list(flatter_nodes)

        paragraphs = []
        for node in flatter_nodes:
            if do_expensive_logging:
                logger.debug("node=%s, %s", type(node), repr(node))

            if isinstance(node, Text):
                paragraphs_local = self._parse_text_node(node, parse_state)
                paragraphs.extend(paragraphs_local)
            elif isinstance(node, Wikilink):
                self._parse_wikilink_node(node, parse_state)
            elif isinstance(node, ExternalLink):
                self._parse_external_link_node(node, parse_state)
            elif isinstance(node, Tag):
                self._parse_tag_node(node, parse_state)
            elif isinstance(node, Heading):
                self._parse_heading_node(node, parse_state)

        if parse_state["current_text"] and not parse_state["current_text"].isspace():
            paragraphs.append({
                "plaintext": parse_state["current_text"].rstrip(),
                "wikilinks": parse_state["current_wikilinks"],
                "section_idx": parse_state["section_idx"],
                "section_name": parse_state["section_name"],
            })

        has_disambigution_template = self._has_disambiguation_template(wikitext)
        return {
            "paragraphs": paragraphs,
            "categories": self._default_filter_categories(wikicode),
            "has_disambiguation_template": has_disambigution_template,
        }

    def node_is_expandable(self, node):
        if isinstance(node, Tag) and node.tag.lower() in self.allowed_tags and hasattr(node, "contents"):
            return True
        else:
            return False

    def _parse_heading_node(self, node: Heading, parse_state) -> None:
        if node.level == 2:
            parse_state["section_name"] = node.title.strip_code().strip()
            parse_state["section_idx"] += 1

    def _parse_tag_node(self, node: Tag, parse_state) -> None:

        if len(node.contents) == 0:
            return

        node_tag = node.tag.strip_code().strip().lower()

        if node_tag in self.allowed_tags:
            self._included_tags.add(node_tag)
            text = node.contents.strip_code().strip()
            parse_state["current_text"] += text

        else:
            self._skipped_tags.add(node_tag)
            if self.include_disallowed_tag_tokens:
                text = "<{}>".format(node_tag)
                parse_state["current_text"] += text

    def _parse_external_link_node(self, node: ExternalLink, parse_state):
        if not self.include_external_link_anchors:
            return
        if not node.title:
            return
        text = node.title.strip_code().strip()
        parse_state["current_text"] += text

    def _default_wikilink_parser(self, node: Wikilink) -> Tuple[bool, bool, str, str]:
        target = node.title.strip_code().strip()

        if len(target) == 0:
            return (False, False, "", "")

        if any([target.lower().startswith(prefix + ":") for prefix in self.forbidden_wikilink_prefixes]):
            return (False, False, "", "")

        if target.startswith("#"):
            anchor = target[1:]
            return (True, False, target, anchor)

        target = target[: target.index("#")] if "#" in target else target

        anchor = node.text.strip_code().strip() if node.text else target

        anchor = anchor[anchor.rindex(":") + 1 :] if ":" in anchor else anchor

        target = target[0].upper() + target[1:].replace(" ", "_")

        add_text = True
        add_link = ":" not in target
        return (add_text, add_link, target, anchor)

    def _parse_wikilink_node(self, node: Wikilink, parse_state) -> None:

        if self.custom_wikilink_parser is not None:
            wikilink_parser = self.custom_wikilink_parser
        else:
            wikilink_parser = self._default_wikilink_parser

        add_text, add_link, target, anchor = wikilink_parser(node)

        if add_text:
            start = len(parse_state["current_text"])
            parse_state["current_text"] += anchor
            end = len(parse_state["current_text"])
        if add_link:
            parse_state["current_wikilinks"].append((target, anchor, start, end))

    def _parse_text_node(self, node: Text, parse_state) -> List[dict]:
        paragraphs_local = []
        for ii, text in enumerate(node.split("\n")):
            if ii == 0:
                parse_state["current_text"] += text
            else:
                if parse_state["current_text"] and not parse_state["current_text"].isspace():
                    paragraphs_local.append({
                        "plaintext": parse_state["current_text"],
                        "wikilinks": parse_state["current_wikilinks"],
                        "section_idx": parse_state["section_idx"],
                        "section_name": parse_state["section_name"],
                    })

                parse_state["current_text"] = text
                parse_state["current_wikilinks"] = []

        return paragraphs_local

    def _default_filter_categories(self, wikicode: Wikicode) -> List[str]:
        wikilinks = wikicode.filter_wikilinks()
        ii = len("Category:")
        category_links = [el for el in wikilinks if el.title.lower().startswith("category:")]
        category_titles = [el.title.rstrip()[ii:] for el in category_links if len(el.title.rstrip()[ii:]) > 0]
        category_titles = [title[0].upper() + title[1:].replace(" ", "_") for title in category_titles]

        return category_titles

    def _has_disambiguation_template(self, wikitext: str) -> bool:
        template_bool = "{{disambiguation|" in wikitext or "{{disambiguation}}" in wikitext
        return template_bool


if __name__ == "__main__":
    import json
    import os

    FORBIDDEN_SECTIONS = frozenset([
        "bibliography",
        "citations",
        "external links",
        "further reading",
        "other uses",
        "references",
        "see also",
        "source",
    ])

    test_path = "../../tests/content_transformers/data"

    file_path = os.path.join(test_path, "enwiki_siteinfo.json")
    siteinfo = json.load(open(file_path, "r"))
    forbidden_wikilink_prefixes = generate_non_link_namespace_names(siteinfo)
    transformer = Wikitext2Structured(
        forbidden_wikilink_prefixes=forbidden_wikilink_prefixes,
        allowed_tags=frozenset(["b", "i", "u", "blockquote"]),
    )

    file_path = os.path.join(test_path, "39_Albedo_953762015.wikitext")
    wikitext = open(file_path, "r").read()
    structured = transformer.transform(wikitext)
    filtered_paragraphs = [
        para for para in structured["paragraphs"] if para["section_name"].lower() not in FORBIDDEN_SECTIONS
    ]

    list_of_paragraph_texts = [el["text"] for el in filtered_paragraphs]
    one_string = " ".join(list_of_paragraph_texts)
    list_of_words = one_string.split(" ")
