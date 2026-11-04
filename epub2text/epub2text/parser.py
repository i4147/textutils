import logging
import re
import urllib.parse
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal, cast

import ebooklib
from bs4 import BeautifulSoup, NavigableString
from defusedxml import ElementTree as DefusedET
from ebooklib import epub

from .cleaner import calculate_text_length, clean_text
from .models import Chapter, Metadata, Page, PageSource
from .structured import (
    EpubPackageInfo,
    ExtractionPolicy,
    NavigationEntry,
    SourceDocument,
    StructuredEpubExtraction,
    TextSegment,
)

logger = logging.getLogger(__name__)
_PAGE_LIST_ATTR_PATTERN = re.compile(
    r"epub:type\s*=\s*['\"]page-list['\"]", re.IGNORECASE
)


class EPUBParser:
    def __init__(self, filepath: str, paragraph_separator: str = "\n\n"):
        self.filepath = Path(filepath)
        if not self.filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        self.paragraph_separator = paragraph_separator
        self.book: Any = None
        self.doc_content: dict[str, str] = {}
        self.content_texts: dict[str, str] = {}
        self.content_lengths: dict[str, int] = {}
        self.processed_nav_structure: list[dict[str, Any]] = []
        self._metadata: Metadata | None = None
        self._page_list_nav: tuple[Any, str] | None = None
        self._page_list_nav_checked = False
        self._nav_processed = False
        self._upper_title_cache: set[str] | None = None
        self._structured_cache: dict[tuple[Any, ...], StructuredEpubExtraction] = {}
        self._chapter_documents_cache: dict[tuple[Any, ...], list[Any]] = {}

        self._load_epub()

    def _get_upper_titles_for_toc(self) -> set[str]:
        if self._upper_title_cache is not None:
            return self._upper_title_cache
        titles: set[str] = set()
        meta = self.get_metadata()
        if meta.title:
            titles.add(meta.title.upper())
        for ch in self.get_chapters(include_text=False):
            if ch.title:
                titles.add(ch.title.upper())
        self._upper_title_cache = titles
        return titles

    def _load_epub(self) -> None:
        try:
            self.book = epub.read_epub(str(self.filepath))
            logger.info(f"Loaded EPUB: {self.filepath.name}")
        except Exception as e:
            raise ValueError(f"Failed to read EPUB file: {e}") from e

    def _get_single_metadata(self, field: str) -> str | None:
        try:
            items = self.book.get_metadata("DC", field)
            if items and len(items) > 0:
                value: str = items[0][0]
                return value
        except Exception as e:
            logger.warning(f"Error extracting {field}: {e}")
        return None

    def _get_list_metadata(self, field: str) -> list[str]:
        try:
            items = self.book.get_metadata("DC", field)
            if items:
                return [item[0] for item in items if len(item) > 0]
        except Exception as e:
            logger.warning(f"Error extracting {field}: {e}")
        return []

    def get_metadata(self) -> Metadata:
        if self._metadata is not None:
            return self._metadata

        publication_year = None
        date_str = self._get_single_metadata("date")
        if date_str:
            year_match = re.search(r"\b(19|20)\d{2}\b", date_str)
            publication_year = year_match.group(0) if year_match else date_str

        self._metadata = Metadata(
            title=self._get_single_metadata("title"),
            authors=self._get_list_metadata("creator"),
            description=self._get_single_metadata("description"),
            publisher=self._get_single_metadata("publisher"),
            publication_year=publication_year,
            identifier=self._get_single_metadata("identifier"),
            language=self._get_single_metadata("language"),
            contributors=self._get_list_metadata("contributor"),
            rights=self._get_single_metadata("rights"),
            coverage=self._get_single_metadata("coverage"),
        )
        return self._metadata

    def get_chapters(self, include_text: bool = True) -> list[Chapter]:
        self._process_epub_content_nav()
        if not self._nav_processed:
            self._process_epub_content_nav()
        chapters: list[Chapter] = []
        self._build_chapters_from_nav(
            self.processed_nav_structure, chapters, level=1, include_text=include_text
        )

        return chapters

    def _build_chapters_from_nav(
        self,
        nav_structure: list[dict[str, Any]],
        chapters: list[Chapter],
        parent_id: str | None = None,
        level: int = 1,
        include_text: bool = True,
    ) -> None:
        for entry in nav_structure:
            src: str | None = entry.get("src")
            title: str = entry.get("title", "Untitled")
            children: list[dict[str, Any]] = entry.get("children", [])

            chapter_id = src if src else f"chapter_{len(chapters)}"

            if include_text:
                text = self.content_texts.get(src, "") if src else ""
            else:
                text = ""
            char_count = self.content_lengths.get(src, 0) if src else 0

            chapter = Chapter(
                id=chapter_id,
                title=title,
                text=text,
                char_count=char_count,
                parent_id=parent_id,
                level=level,
            )
            chapters.append(chapter)

            if children:
                self._build_chapters_from_nav(
                    children,
                    chapters,
                    parent_id=chapter_id,
                    level=level + 1,
                    include_text=include_text,
                )

    def _process_epub_content_nav(self) -> None:
        if self._nav_processed:
            return
        logger.info("Processing EPUB using navigation document (NAV/NCX)...")
        nav_item = None
        nav_type = None

        nav_items = list(self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION))
        if nav_items:
            preferred_nav = next(
                (
                    item
                    for item in nav_items
                    if "nav" in item.get_name().lower()
                    and item.get_name().lower().endswith((".xhtml", ".html"))
                ),
                None,
            )
            if preferred_nav:
                nav_item = preferred_nav
                nav_type = "html"
                logger.info(f"Found preferred NAV HTML: {nav_item.get_name()}")
            else:
                html_nav = next(
                    (
                        item
                        for item in nav_items
                        if item.get_name().lower().endswith((".xhtml", ".html"))
                    ),
                    None,
                )
                if html_nav:
                    nav_item = html_nav
                    nav_type = "html"
                    logger.info(f"Found NAV HTML: {html_nav.get_name()}")

        if not nav_item and nav_items:
            ncx_in_nav = next(
                (
                    item
                    for item in nav_items
                    if item.get_name().lower().endswith(".ncx")
                ),
                None,
            )
            if ncx_in_nav:
                nav_item = ncx_in_nav
                nav_type = "ncx"
                logger.info(f"Found NCX via ITEM_NAVIGATION: {ncx_in_nav.get_name()}")

        ncx_constant = getattr(epub, "ITEM_NCX", None)
        if not nav_item and ncx_constant is not None:
            ncx_items = list(self.book.get_items_of_type(ncx_constant))
            if ncx_items:
                nav_item = ncx_items[0]
                nav_type = "ncx"
                logger.info(f"Found NCX via ITEM_NCX: {nav_item.get_name()}")

        if not nav_item:
            for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                try:
                    html_content = item.get_content().decode("utf-8", errors="ignore")
                    if "<nav" in html_content and 'epub:type="toc"' in html_content:
                        soup = BeautifulSoup(html_content, "html.parser")
                        nav_tag = soup.find("nav", attrs={"epub:type": "toc"})
                        if nav_tag:
                            nav_item = item
                            nav_type = "html"
                            logger.info(f"Found NAV HTML in: {item.get_name()}")
                            break
                except (AttributeError, UnicodeDecodeError):
                    continue

        if not nav_item or not nav_type:
            logger.warning("No navigation document found")
            raise ValueError("No navigation document (NAV HTML or NCX) found")

        parser_type = "html.parser" if nav_type == "html" else "xml"
        logger.info(f"Using parser: '{parser_type}' for {nav_item.get_name()}")

        try:
            nav_content = nav_item.get_content().decode("utf-8", errors="ignore")
            nav_soup = BeautifulSoup(nav_content, parser_type)
        except Exception as e:
            logger.error(f"Failed to parse navigation: {e}")
            raise ValueError(f"Failed to parse navigation content: {e}") from e

        self.doc_content = {}
        spine_docs = []
        for spine_item_tuple in self.book.spine:
            item_id = spine_item_tuple[0]
            item = self.book.get_item_with_id(item_id)
            if item:
                spine_docs.append(item.get_name())
            else:
                logger.warning(f"Spine item with id '{item_id}' not found")

        doc_order = {href: i for i, href in enumerate(spine_docs)}
        doc_order_decoded = {
            urllib.parse.unquote(href): i for href, i in doc_order.items()
        }

        self.content_texts = {}
        self.content_lengths = {}

        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            href = item.get_name()
            if href in doc_order or any(
                href in str(nav_point.get("src", ""))
                for nav_point in nav_soup.find_all(["content", "a"])
            ):
                try:
                    html_content = item.get_content().decode("utf-8", errors="ignore")
                    self.doc_content[href] = html_content
                except Exception as e:
                    logger.error(f"Error decoding content for {href}: {e}")
                    self.doc_content[href] = ""

        ordered_nav_entries: list[dict[str, Any]] = []
        self.processed_nav_structure = []

        parse_successful = False
        if nav_type == "ncx":
            nav_map = nav_soup.find("navMap")
            if nav_map:
                logger.info("Parsing NCX <navMap>...")
                for nav_point in nav_map.find_all("navPoint", recursive=False):
                    self._parse_ncx_navpoint(
                        nav_point,
                        ordered_nav_entries,
                        doc_order,
                        doc_order_decoded,
                        self.processed_nav_structure,
                    )
                parse_successful = bool(ordered_nav_entries)
            else:
                logger.warning("Could not find <navMap> in NCX")
        elif nav_type == "html":
            logger.info("Parsing NAV HTML...")
            toc_nav = nav_soup.find("nav", attrs={"epub:type": "toc"})
            if not toc_nav:
                all_navs = nav_soup.find_all("nav")
                for nav in all_navs:
                    if nav.find("ol"):
                        toc_nav = nav
                        logger.info("Found fallback TOC in <nav> with <ol>")
                        break
            if toc_nav:
                top_ol = toc_nav.find("ol", recursive=False)
                if top_ol:
                    for li in top_ol.find_all("li", recursive=False):
                        self._parse_html_nav_li(
                            li,
                            ordered_nav_entries,
                            doc_order,
                            doc_order_decoded,
                            self.processed_nav_structure,
                        )
                    parse_successful = bool(ordered_nav_entries)
                else:
                    logger.warning("Found <nav> but no top-level <ol>")
            else:
                logger.warning("Could not find TOC structure in NAV HTML")

        if not parse_successful:
            logger.warning("No valid navigation entries found")
            raise ValueError("No valid navigation entries found after parsing")

        ordered_nav_entries.sort(key=lambda x: (x["doc_order"], x["position"]))
        logger.info(f"Sorted {len(ordered_nav_entries)} navigation entries")

        num_entries = len(ordered_nav_entries)
        for i in range(num_entries):
            current_entry = ordered_nav_entries[i]
            current_src = current_entry["src"]
            current_doc = current_entry["doc_href"]
            current_pos = current_entry["position"]
            current_doc_html = self.doc_content.get(current_doc, "")

            next_entry = ordered_nav_entries[i + 1] if (i + 1) < num_entries else None
            next_doc = next_entry["doc_href"] if next_entry else None
            next_pos = next_entry["position"] if next_entry else None

            slice_html = self._slice_spine_html(
                current_doc,
                current_pos,
                next_doc,
                next_pos,
                spine_docs,
                allow_wraparound=True,
            )

            if not slice_html.strip() and current_doc_html:
                logger.warning(f"No content for '{current_src}', using full file")
                slice_html = current_doc_html

            if slice_html.strip():
                slice_soup = BeautifulSoup(slice_html, "html.parser")

                block_break_tags = {
                    "p",
                    "div",
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                }
                for tag in slice_soup.find_all(block_break_tags):
                    if tag.name == "div" and tag.find(block_break_tags):
                        continue
                    tag.append(self.paragraph_separator)

                for ol in slice_soup.find_all("ol"):
                    start_attr = ol.get("start")
                    start_num = int(str(start_attr)) if start_attr else 1
                    for li_idx, li in enumerate(ol.find_all("li", recursive=False)):
                        number_text = f"{start_num + li_idx}) "
                        li_text = li.string
                        if li_text:
                            cast(NavigableString, li_text).replace_with(
                                number_text + str(li_text)
                            )
                        else:
                            li.insert(0, NavigableString(number_text))

                for tag in slice_soup.find_all(["sup", "sub"]):
                    tag.decompose()

                text = clean_text(
                    slice_soup.get_text(),
                    preserve_single_newlines=(self.paragraph_separator == "\n"),
                ).strip()
                if text:
                    self.content_texts[current_src] = text
                    self.content_lengths[current_src] = calculate_text_length(text)
                else:
                    self.content_texts[current_src] = ""
                    self.content_lengths[current_src] = 0
            else:
                self.content_texts[current_src] = ""
                self.content_lengths[current_src] = 0

        if ordered_nav_entries:
            first_entry = ordered_nav_entries[0]
            first_doc_href = first_entry["doc_href"]
            first_pos = first_entry["position"]
            first_doc_order = first_entry["doc_order"]
            prefix_html = ""

            for doc_idx in range(first_doc_order):
                if doc_idx < len(spine_docs):
                    intermediate_doc_href = spine_docs[doc_idx]
                    prefix_html += self.doc_content.get(intermediate_doc_href, "")

            first_doc_html = self.doc_content.get(first_doc_href, "")
            prefix_html += first_doc_html[:first_pos]

            if prefix_html.strip():
                prefix_soup = BeautifulSoup(prefix_html, "html.parser")
                for tag in prefix_soup.find_all(["sup", "sub"]):
                    tag.decompose()
                prefix_text = clean_text(prefix_soup.get_text()).strip()

                if prefix_text:
                    prefix_chapter_src = "internal:prefix_content"
                    self.content_texts[prefix_chapter_src] = prefix_text
                    self.content_lengths[prefix_chapter_src] = len(prefix_text)
                    self.processed_nav_structure.insert(
                        0,
                        {
                            "src": prefix_chapter_src,
                            "title": "Introduction",
                            "children": [],
                        },
                    )
                    logger.info("Added prefix content chapter")

        logger.info(f"Finished processing. Found {len(self.content_texts)} sections")
        self._nav_processed = True
        self._upper_title_cache = None

    def _find_doc_key(
        self,
        base_href: str,
        doc_order: dict[str, int],
        doc_order_decoded: dict[str, int],
    ) -> tuple[str | None, int | None]:
        import os

        candidates = [
            base_href,
            urllib.parse.unquote(base_href),
        ]
        base_name = os.path.basename(base_href).lower()
        for k in list(doc_order.keys()) + list(doc_order_decoded.keys()):
            if os.path.basename(k).lower() == base_name:
                candidates.append(k)
        for candidate in candidates:
            if candidate in doc_order:
                return candidate, doc_order[candidate]
            elif candidate in doc_order_decoded:
                return candidate, doc_order_decoded[candidate]
        return None, None

    def _parse_ncx_navpoint(
        self,
        nav_point: Any,
        ordered_entries: list[dict[str, Any]],
        doc_order: dict[str, int],
        doc_order_decoded: dict[str, int],
        tree_structure_list: list[dict[str, Any]],
    ) -> None:
        nav_label = nav_point.find("navLabel")
        content = nav_point.find("content")
        title = (
            nav_label.find("text").get_text(strip=True)
            if nav_label and nav_label.find("text")
            else "Untitled Section"
        )
        src = content["src"] if content and "src" in content.attrs else None

        current_entry_node: dict[str, Any] = {
            "title": title,
            "src": src,
            "children": [],
        }

        if src:
            base_href, fragment = src.split("#", 1) if "#" in src else (src, None)
            doc_key, doc_idx = self._find_doc_key(
                base_href, doc_order, doc_order_decoded
            )
            if not doc_key:
                logger.warning(f"Entry '{title}' points to '{base_href}' not in spine")
                current_entry_node["has_content"] = False
            else:
                position = self._find_position_robust(doc_key, fragment)
                entry_data = {
                    "src": src,
                    "title": title,
                    "doc_href": doc_key,
                    "position": position,
                    "doc_order": doc_idx,
                }
                ordered_entries.append(entry_data)
                current_entry_node["has_content"] = True
        else:
            logger.warning(f"Entry '{title}' has no 'src' attribute")
            current_entry_node["has_content"] = False

        child_navpoints = nav_point.find_all("navPoint", recursive=False)
        if child_navpoints:
            for child_np in child_navpoints:
                self._parse_ncx_navpoint(
                    child_np,
                    ordered_entries,
                    doc_order,
                    doc_order_decoded,
                    current_entry_node["children"],
                )

        if title and (
            current_entry_node.get("has_content", False)
            or current_entry_node["children"]
        ):
            tree_structure_list.append(current_entry_node)

    def _parse_html_nav_li(
        self,
        li_element: Any,
        ordered_entries: list[dict[str, Any]],
        doc_order: dict[str, int],
        doc_order_decoded: dict[str, int],
        tree_structure_list: list[dict[str, Any]],
    ) -> None:
        link = li_element.find("a", recursive=False)
        span_text = li_element.find("span", recursive=False)
        title = "Untitled Section"
        src: str | None = None
        current_entry_node: dict[str, Any] = {"children": []}

        if link and "href" in link.attrs:
            src = link["href"]
            title = link.get_text(strip=True) or title
            if not title.strip() and span_text:
                title = span_text.get_text(strip=True) or title
            if not title.strip():
                li_text = "".join(
                    t for t in li_element.contents if isinstance(t, NavigableString)
                ).strip()
                title = li_text or title
        elif span_text:
            title = span_text.get_text(strip=True) or title
            if not title.strip():
                li_text = "".join(
                    t for t in li_element.contents if isinstance(t, NavigableString)
                ).strip()
                title = li_text or title
        else:
            li_text = "".join(
                t for t in li_element.contents if isinstance(t, NavigableString)
            ).strip()
            title = li_text or title

        current_entry_node["title"] = title
        current_entry_node["src"] = src

        doc_key = None
        doc_idx = None
        position = 0
        fragment = None
        if src:
            base_href, fragment = src.split("#", 1) if "#" in src else (src, None)
            doc_key, doc_idx = self._find_doc_key(
                base_href, doc_order, doc_order_decoded
            )
            if doc_key is not None:
                position = self._find_position_robust(doc_key, fragment)
                entry_data = {
                    "src": src,
                    "title": title,
                    "doc_href": doc_key,
                    "position": position,
                    "doc_order": doc_idx,
                }
                ordered_entries.append(entry_data)
                current_entry_node["has_content"] = True
            else:
                logger.warning(f"Entry '{title}' points to '{base_href}' not in spine")
                current_entry_node["has_content"] = False
        else:
            current_entry_node["has_content"] = False

        for child_ol in li_element.find_all("ol", recursive=False):
            for child_li in child_ol.find_all("li", recursive=False):
                self._parse_html_nav_li(
                    child_li,
                    ordered_entries,
                    doc_order,
                    doc_order_decoded,
                    current_entry_node["children"],
                )
        tree_structure_list.append(current_entry_node)

    def _find_position_robust(self, doc_href: str, fragment_id: str | None) -> int:
        if doc_href not in self.doc_content:
            logger.warning(f"Document '{doc_href}' not found in cached content")
            return 0
        html_content = self.doc_content[doc_href]
        if not fragment_id:
            return 0

        try:
            temp_soup = BeautifulSoup(f"<div>{html_content}</div>", "html.parser")
            target_element = temp_soup.find(id=fragment_id)
            if target_element:
                tag_str = str(target_element)
                pos = html_content.find(tag_str[: min(len(tag_str), 200)])
                if pos != -1:
                    logger.debug(f"Found position for id='{fragment_id}': {pos}")
                    return pos
        except Exception as e:
            logger.warning(f"BeautifulSoup failed to find id='{fragment_id}': {e}")

        safe_fragment_id = re.escape(fragment_id)
        id_name_pattern = re.compile(
            f"<[^>]+(?:id|name)\\s*=\\s*[\"']{safe_fragment_id}[\"']", re.IGNORECASE
        )
        match = id_name_pattern.search(html_content)
        if match:
            pos = match.start()
            logger.debug(f"Found position for id/name='{fragment_id}' (regex): {pos}")
            return pos

        id_match_str = f'id="{fragment_id}"'
        name_match_str = f'name="{fragment_id}"'
        id_pos = html_content.find(id_match_str)
        name_pos = html_content.find(name_match_str)

        pos = -1
        if id_pos != -1 and name_pos != -1:
            pos = min(id_pos, name_pos)
        elif id_pos != -1:
            pos = id_pos
        elif name_pos != -1:
            pos = name_pos

        if pos != -1:
            tag_start_pos = html_content.rfind("<", 0, pos)
            final_pos = tag_start_pos if tag_start_pos != -1 else 0
            logger.debug(f"Found position for id/name='{fragment_id}': {final_pos}")
            return final_pos

        logger.warning(f"Anchor '{fragment_id}' not found in {doc_href}")
        return 0

    def _remove_duplicate_title_line(self, text: str, title: str) -> str:
        if not text or not title:
            return text

        lines = text.split("\n", 1)
        if not lines:
            return text

        first_line = lines[0].strip()
        title_clean = title.strip()

        if not title_clean:
            return text

        def remove_leading_duplicate_titles(remainder: str) -> str:
            remainder = remainder.lstrip("\n")
            if not remainder:
                return ""
            return self._remove_duplicate_title_line(remainder, title)

        if first_line == title_clean:
            return remove_leading_duplicate_titles(lines[1]) if len(lines) > 1 else ""

        if first_line.lower() == title_clean.lower():
            return remove_leading_duplicate_titles(lines[1]) if len(lines) > 1 else ""

        def join_remainder(remainder: str) -> str:
            remainder = remainder.lstrip()
            if len(lines) > 1:
                if remainder:
                    return remainder + "\n" + lines[1]
                return lines[1]
            return remainder

        if first_line.startswith(title_clean + " "):
            remainder = first_line[len(title_clean) :]
            return join_remainder(remainder)

        if first_line.lower().startswith(title_clean.lower() + " "):
            remainder = first_line[len(title_clean) :]
            return join_remainder(remainder)

        separator_pattern = re.compile(
            rf"^{re.escape(title_clean)}[\s:\-\.,\u2013\u2014]+(.+)$",
            flags=re.IGNORECASE,
        )
        separator_match = separator_pattern.match(first_line)
        if separator_match:
            remainder = separator_match.group(1)
            return join_remainder(remainder)

        normalized_title = re.sub(r"[^a-z0-9]+", "", title_clean.lower())
        normalized_first = re.sub(r"[^a-z0-9]+", "", first_line.lower())
        if normalized_title and normalized_first:
            if normalized_first == normalized_title:
                return (
                    remove_leading_duplicate_titles(lines[1]) if len(lines) > 1 else ""
                )

            is_heading_like = len(
                first_line
            ) <= 120 and not first_line.rstrip().endswith((".", "!", "?"))
            if is_heading_like and normalized_title in normalized_first:
                if len(normalized_title) >= 3:
                    return lines[1] if len(lines) > 1 else ""

                heading_prefixes = (
                    "chapter",
                    "part",
                    "book",
                    "section",
                    "act",
                )
                if first_line.lower().startswith(heading_prefixes):
                    return lines[1] if len(lines) > 1 else ""

        return text

    def extract_chapters(
        self,
        chapter_ids: list[str] | None = None,
        deduplicate_chapter_titles: bool = True,
        skip_toc: bool = False,
        include_chapter_title: bool = False,
    ) -> str:
        chapters = self.get_chapters()

        if chapter_ids is None:
            selected = chapters
        else:
            selected = [ch for ch in chapters if ch.id in chapter_ids]

        if skip_toc:
            filtered = []
            for chapter in selected:
                temp_page = Page(
                    page_number="temp",
                    text=chapter.text,
                    char_count=chapter.char_count,
                    chapter_title=chapter.title,
                    source=PageSource.SYNTHETIC,
                )
                if not self._is_toc_or_front_matter(temp_page):
                    filtered.append(chapter)
            selected = filtered

        parts: list[str] = []
        for i, chapter in enumerate(selected):
            if chapter.text:
                if deduplicate_chapter_titles:
                    cleaned_text = self._remove_duplicate_title_line(
                        chapter.text, chapter.title
                    )
                else:
                    cleaned_text = chapter.text

                if i == 0 and include_chapter_title:
                    parts.append(f"{chapter.title}\n\n{cleaned_text}")
                elif i > 0 and include_chapter_title:
                    parts.append(f"\n\n\n\n{chapter.title}\n\n{cleaned_text}")
                else:
                    parts.append(cleaned_text)

        return "".join(parts)

    def get_chapter_documents(
        self,
        *,
        options: Any | None = None,
        policy: ExtractionPolicy | None = None,
    ) -> list[Any]:
        from .chapter_documents import (
            ChapterMarkdownOptions,
            _effective_policy,
            assemble_chapter_documents,
        )

        effective_options = options or ChapterMarkdownOptions()
        if not isinstance(effective_options, ChapterMarkdownOptions):
            raise TypeError("options must be ChapterMarkdownOptions or None")
        effective_policy = _effective_policy(effective_options, policy)
        cache_key = (effective_options, repr(effective_policy))
        if cache_key not in self._chapter_documents_cache:
            extraction = self.extract_structured(
                policy=effective_policy,
                include_inline_runs=True,
                include_markdown_fragments=True,
                include_segments=False,
            )
            self._chapter_documents_cache[cache_key] = assemble_chapter_documents(
                extraction, options=effective_options
            )
        return self._chapter_documents_cache[cache_key]

    def get_pages(
        self,
        synthetic_page_size: int = 2000,
        use_words: bool = False,
    ) -> list[Page]:
        pages = self._get_epub_page_list()

        if pages:
            logger.info(f"Found {len(pages)} pages from EPUB page-list")
            return pages

        logger.info("No page-list found, generating synthetic pages")
        return self._generate_synthetic_pages(synthetic_page_size, use_words)

    def has_page_list(self) -> bool:
        return bool(self._find_page_list_nav())

    def _find_page_list_nav(self) -> tuple[Any, str] | None:
        if self._page_list_nav_checked:
            return self._page_list_nav

        nav_items = list(self.book.get_items_of_type(ebooklib.ITEM_NAVIGATION))

        for nav_item in nav_items:
            if nav_item.get_name().lower().endswith((".xhtml", ".html")):
                try:
                    nav_content = nav_item.get_content().decode(
                        "utf-8", errors="ignore"
                    )
                    if not _PAGE_LIST_ATTR_PATTERN.search(nav_content):
                        continue
                    nav_soup = BeautifulSoup(nav_content, "html.parser")
                    page_list_nav = nav_soup.find(
                        "nav", attrs={"epub:type": "page-list"}
                    )
                    if page_list_nav:
                        logger.info(
                            f"Found page-list in NAV HTML: {nav_item.get_name()}"
                        )
                        self._page_list_nav = (page_list_nav, "html")
                        self._page_list_nav_checked = True
                        return self._page_list_nav
                except (AttributeError, UnicodeDecodeError):
                    continue

        ncx_item = None
        for nav_item in nav_items:
            if nav_item.get_name().lower().endswith(".ncx"):
                ncx_item = nav_item
                break

        if not ncx_item:
            ncx_constant = getattr(epub, "ITEM_NCX", None)
            if ncx_constant is not None:
                ncx_items = list(self.book.get_items_of_type(ncx_constant))
                if ncx_items:
                    ncx_item = ncx_items[0]

        if ncx_item:
            try:
                ncx_content = ncx_item.get_content().decode("utf-8", errors="ignore")
                ncx_root = DefusedET.fromstring(ncx_content)
                page_list = ncx_root.find(".//{*}pageList")
                if page_list is not None:
                    logger.info(f"Found pageList in NCX: {ncx_item.get_name()}")
                    self._page_list_nav = (page_list, "ncx")
                    self._page_list_nav_checked = True
                    return self._page_list_nav
            except (DefusedET.ParseError, UnicodeDecodeError, ValueError):
                pass

        for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            try:
                html_content = item.get_content().decode("utf-8", errors="ignore")
                if not _PAGE_LIST_ATTR_PATTERN.search(html_content):
                    continue
                soup = BeautifulSoup(html_content, "html.parser")
                page_list_nav = soup.find("nav", attrs={"epub:type": "page-list"})
                if page_list_nav:
                    logger.info(f"Found page-list in document: {item.get_name()}")
                    self._page_list_nav = (page_list_nav, "html")
                    self._page_list_nav_checked = True
                    return self._page_list_nav
            except (AttributeError, UnicodeDecodeError):
                continue

        self._page_list_nav = None
        self._page_list_nav_checked = True
        return None

    def _get_epub_page_list(self) -> list[Page]:
        nav_result = self._find_page_list_nav()
        if not nav_result:
            return []

        page_list_nav, nav_type = nav_result
        pages: list[Page] = []

        if not self.content_texts:
            self._process_epub_content_nav()

        spine_docs = []
        for spine_item_tuple in self.book.spine:
            item_id = spine_item_tuple[0]
            item = self.book.get_item_with_id(item_id)
            if item:
                spine_docs.append(item.get_name())

        doc_order = {href: i for i, href in enumerate(spine_docs)}
        doc_order_decoded = {
            urllib.parse.unquote(href): i for href, i in doc_order.items()
        }

        page_entries: list[dict[str, Any]] = []

        if nav_type == "html":
            ol = page_list_nav.find("ol")
            if ol:
                for li in ol.find_all("li", recursive=False):
                    link = li.find("a")
                    if link and "href" in link.attrs:
                        page_num = link.get_text(strip=True)
                        src = link["href"]
                        page_entries.append({"page_number": page_num, "src": src})
        elif nav_type == "ncx":
            for page_target in page_list_nav.findall(".//{*}pageTarget"):
                nav_label = page_target.find("{*}navLabel")
                content = page_target.find("{*}content")
                text_elem = nav_label.find("{*}text") if nav_label is not None else None
                page_num = text_elem.text.strip() if text_elem is not None else ""
                src = content.get("src") if content is not None else ""
                if page_num and src:
                    page_entries.append({"page_number": page_num, "src": src})

        if not page_entries:
            return []

        for entry in page_entries:
            src = entry["src"]
            base_href, fragment = src.split("#", 1) if "#" in src else (src, None)
            doc_key, doc_idx = self._find_doc_key(
                base_href, doc_order, doc_order_decoded
            )
            if doc_key is not None:
                position = self._find_position_robust(doc_key, fragment)
                entry["doc_href"] = doc_key
                entry["doc_order"] = doc_idx
                entry["position"] = position
            else:
                entry["doc_href"] = base_href
                entry["doc_order"] = 999999
                entry["position"] = 0

        page_entries.sort(key=lambda x: (x.get("doc_order", 0), x.get("position", 0)))

        num_entries = len(page_entries)
        chapters = self.get_chapters()
        chapter_map = self._build_chapter_position_map(chapters, doc_order)

        for i in range(num_entries):
            current = page_entries[i]
            next_entry = page_entries[i + 1] if i + 1 < num_entries else None

            text = self._extract_text_between_positions(current, next_entry, spine_docs)

            chapter_id, chapter_title = self._find_chapter_for_position(
                current.get("doc_href", ""),
                current.get("position", 0),
                chapter_map,
            )

            page = Page(
                page_number=current["page_number"],
                text=text,
                char_count=calculate_text_length(text),
                source=PageSource.EPUB_PAGE_LIST,
                chapter_id=chapter_id,
                chapter_title=chapter_title,
            )
            pages.append(page)

        return pages

    def _generate_synthetic_pages(self, page_size: int, use_words: bool) -> list[Page]:
        chapters = self.get_chapters()
        if not chapters:
            return []

        pages: list[Page] = []
        page_num = 1
        current_sentences: list[str] = []
        current_size = 0
        current_chapter_id: str | None = None
        current_chapter_title: str | None = None

        def get_size(text: str) -> int:
            if use_words:
                return len(text.split())
            return len(text)

        def save_page() -> None:
            nonlocal page_num, current_sentences, current_size

            if current_sentences:
                page_text_parts = []
                for s in current_sentences:
                    if s == "\n\n":
                        page_text_parts.append("\n\n")
                    else:
                        page_text_parts.append(s)

                page_text = ""
                for i, part in enumerate(page_text_parts):
                    if part == "\n\n":
                        page_text += "\n\n"
                    elif i > 0 and page_text_parts[i - 1] != "\n\n":
                        page_text += " " + part
                    else:
                        page_text += part

                page_text = page_text.strip()

                pages.append(
                    Page(
                        page_number=str(page_num),
                        text=page_text,
                        char_count=calculate_text_length(page_text),
                        source=PageSource.SYNTHETIC,
                        chapter_id=current_chapter_id,
                        chapter_title=current_chapter_title,
                    )
                )
                page_num += 1
                current_sentences = []
                current_size = 0

        for chapter in chapters:
            if not chapter.text:
                continue

            if (
                current_chapter_id is not None
                and (
                    chapter.id != current_chapter_id
                    or chapter.title != current_chapter_title
                )
                and current_sentences
            ):
                save_page()

            current_chapter_id = chapter.id
            current_chapter_title = chapter.title

            sentences = self._split_into_sentences(chapter.text)

            for sentence in sentences:
                if sentence == "\n\n":
                    current_sentences.append("\n\n")
                    continue

                sentence = sentence.strip()
                if not sentence:
                    continue

                sentence_size = get_size(sentence)

                if sentence_size > page_size and not current_sentences:
                    pages.append(
                        Page(
                            page_number=str(page_num),
                            text=sentence,
                            char_count=calculate_text_length(sentence),
                            source=PageSource.SYNTHETIC,
                            chapter_id=current_chapter_id,
                            chapter_title=current_chapter_title,
                        )
                    )
                    page_num += 1
                    continue

                if current_size + sentence_size > page_size and current_sentences:
                    save_page()

                current_sentences.append(sentence)
                current_size += sentence_size

        save_page()

        return pages

    def _split_into_sentences(
        self,
        text: str,
        language_model: str = "en_core_web_sm",
        apply_corrections: bool = True,
        split_on_colon: bool = True,
        use_spacy: bool = False,
    ) -> list[str]:
        if not text or not text.strip():
            return []

        from phrasplit import split_paragraphs, split_sentences

        sentences: list[str] = []
        paragraphs = split_paragraphs(text)

        for para_idx, paragraph in enumerate(paragraphs):
            if not paragraph.strip():
                continue

            para_sentences = split_sentences(
                paragraph,
                language_model=language_model,
                apply_corrections=apply_corrections,
                split_on_colon=split_on_colon,
                use_spacy=use_spacy,
            )
            for sent in para_sentences:
                sent = sent.strip()
                if sent:
                    sentences.append(sent)
            if para_idx < len(paragraphs) - 1:
                sentences.append("\n\n")

        return sentences

    def _build_chapter_position_map(
        self,
        chapters: list[Chapter],
        doc_order: dict[str, int],
    ) -> list[tuple[str, int, str, str]]:
        chapter_positions: list[tuple[str, int, str, str]] = []

        for chapter in chapters:
            src = chapter.id
            if not src or src.startswith("internal:"):
                continue

            base_href, fragment = src.split("#", 1) if "#" in src else (src, None)

            doc_key = None
            for key in doc_order:
                if key == base_href or key.endswith("/" + base_href):
                    doc_key = key
                    break
                decoded = urllib.parse.unquote(key)
                if decoded == base_href or decoded.endswith("/" + base_href):
                    doc_key = key
                    break

            if doc_key:
                position = self._find_position_robust(doc_key, fragment)
                chapter_positions.append((doc_key, position, chapter.id, chapter.title))

        chapter_positions.sort(key=lambda x: (doc_order.get(x[0], 999999), x[1]))

        return chapter_positions

    def _find_chapter_for_position(
        self,
        doc_href: str,
        position: int,
        chapter_map: list[tuple[str, int, str, str]],
    ) -> tuple[str | None, str | None]:
        result_id: str | None = None
        result_title: str | None = None

        for ch_doc, ch_pos, ch_id, ch_title in chapter_map:
            if ch_doc == doc_href and ch_pos <= position:
                result_id = ch_id
                result_title = ch_title
            elif ch_doc == doc_href and ch_pos > position:
                break

        return result_id, result_title

    def _get_spine_index(self, doc_href: str, spine_docs: list[str]) -> int | None:
        try:
            return spine_docs.index(doc_href)
        except ValueError:
            logger.warning("Document '%s' not found in spine order", doc_href)
            return None

    def _slice_spine_html(
        self,
        current_doc: str,
        current_pos: int,
        next_doc: str | None,
        next_pos: int | None,
        spine_docs: list[str],
        *,
        allow_wraparound: bool,
    ) -> str:
        current_doc_html = self.doc_content.get(current_doc, "")
        if not current_doc_html:
            return ""

        if next_doc is None:
            slice_html = current_doc_html[current_pos:]
            idx_current = self._get_spine_index(current_doc, spine_docs)
            if idx_current is None:
                return slice_html
            for doc_idx in range(idx_current + 1, len(spine_docs)):
                slice_html += self.doc_content.get(spine_docs[doc_idx], "")
            return slice_html

        if current_doc == next_doc:
            return current_doc_html[current_pos:next_pos]

        slice_html = current_doc_html[current_pos:]
        idx_current = self._get_spine_index(current_doc, spine_docs)
        idx_next = self._get_spine_index(next_doc, spine_docs)
        if idx_current is None or idx_next is None:
            return slice_html

        docs_between: list[str] = []
        if idx_current < idx_next:
            docs_between = spine_docs[idx_current + 1 : idx_next]
        elif allow_wraparound and idx_current > idx_next:
            docs_between = spine_docs[idx_current + 1 :] + spine_docs[:idx_next]

        for doc_href in docs_between:
            slice_html += self.doc_content.get(doc_href, "")

        next_doc_html = self.doc_content.get(next_doc, "")
        slice_html += next_doc_html[: next_pos or 0]

        return slice_html

    def _extract_text_between_positions(
        self,
        current: dict[str, Any],
        next_entry: dict[str, Any] | None,
        spine_docs: list[str],
    ) -> str:
        current_doc = current.get("doc_href", "")
        current_pos = current.get("position", 0)
        next_doc = next_entry.get("doc_href", "") if next_entry else None
        next_pos = next_entry.get("position", 0) if next_entry else None

        slice_html = self._slice_spine_html(
            current_doc,
            current_pos,
            next_doc,
            next_pos,
            spine_docs,
            allow_wraparound=False,
        )

        if not slice_html.strip():
            return ""

        slice_soup = BeautifulSoup(slice_html, "html.parser")

        for tag in slice_soup.find_all(["p", "div"]):
            tag.append(self.paragraph_separator)

        for tag in slice_soup.find_all(["sup", "sub"]):
            tag.decompose()

        text = clean_text(
            slice_soup.get_text(),
            preserve_single_newlines=(self.paragraph_separator == "\n"),
        ).strip()

        return text

    def extract_pages(
        self,
        page_numbers: list[str] | None = None,
        deduplicate_chapter_titles: bool = True,
        skip_toc: bool = False,
    ) -> str:
        pages = self.get_pages()

        if page_numbers is None:
            selected = pages
        else:
            pages_by_number = {page.page_number: page for page in pages}
            selected = [
                pages_by_number[num] for num in page_numbers if num in pages_by_number
            ]

        parts: list[str] = []
        current_chapter: str | None = None

        for page in selected:
            if not page.text:
                continue

            page_text = page.text
            if skip_toc:
                front_matter_keywords = {
                    "INTRODUCTION",
                    "TABLE OF CONTENTS",
                    "CONTENTS",
                    "TOC",
                    "ACKNOWLEDGEMENTS",
                    "ACKNOWLEDGMENTS",
                    "FOREWORD",
                    "PREFACE",
                }
                if (
                    page.chapter_title
                    and page.chapter_title.upper() in front_matter_keywords
                ):
                    continue

                if self._is_toc_or_front_matter(page):
                    stripped = self._strip_toc_from_page(page_text)
                    if not stripped.strip():
                        continue
                    page_text = stripped
                else:
                    page_text = self._strip_toc_from_page(page_text)

                if not page_text.strip():
                    continue

            if page.chapter_title and page.chapter_title != current_chapter:
                current_chapter = page.chapter_title
                if parts:
                    parts.append(f"\n\n\n\n{current_chapter}\n\n")
                else:
                    parts.append(f"{current_chapter}\n\n")

            if deduplicate_chapter_titles and page.chapter_title:
                cleaned_text = self._remove_duplicate_title_line(
                    page_text, page.chapter_title
                )
            else:
                cleaned_text = page_text

            parts.append(f"<<PAGE: {page.page_number}>>\n\n{cleaned_text}")

        return "\n\n".join(parts)

    def _is_toc_or_front_matter(self, page: Page) -> bool:
        if not page.text:
            return False

        front_matter_keywords = {
            "INTRODUCTION",
            "TABLE OF CONTENTS",
            "CONTENTS",
            "TOC",
            "ACKNOWLEDGEMENTS",
            "ACKNOWLEDGMENTS",
            "FOREWORD",
            "PREFACE",
        }

        if page.chapter_title and page.chapter_title.upper() in front_matter_keywords:
            return True

        search_terms = list(self._get_upper_titles_for_toc())
        if not search_terms:
            return False

        text_upper = page.text[:2000].upper()
        lines = text_upper.split("\n")

        matches = 0
        for line in lines:
            line_stripped = line.strip()
            if line_stripped in search_terms:
                matches += 1

        if matches > 3:
            return True

        return False

    def _strip_toc_from_page(self, page_text: str) -> str:
        if not page_text:
            return page_text

        chapter_titles = self._get_upper_titles_for_toc()
        if not chapter_titles:
            return page_text

        lines = page_text.split("\n")
        toc_entries = []

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_upper = line_stripped.upper()

            if line_upper in chapter_titles and len(line_upper) < 30:
                toc_entries.append((i, line_stripped, True))
            else:
                for title in chapter_titles:
                    if line_upper.startswith(title + " ") and len(title) < 30:
                        toc_entries.append((i, line_stripped, False))
                        break

        if len(toc_entries) >= 5:
            first_idx = toc_entries[0][0]
            last_idx = toc_entries[-1][0]

            if (last_idx - first_idx) / len(toc_entries) < 3:
                last_entry_idx, last_entry_line, is_exact = toc_entries[-1]

                before_toc = lines[:first_idx]

                if is_exact:
                    after_toc = lines[last_entry_idx + 1 :]
                else:
                    line_upper = last_entry_line.upper()
                    for title in chapter_titles:
                        if line_upper.startswith(title + " "):
                            remainder = last_entry_line[len(title) :].lstrip()
                            after_toc = [remainder] + lines[last_entry_idx + 1 :]
                            break
                    else:
                        after_toc = lines[last_entry_idx + 1 :]

                result_lines = before_toc
                started = False
                for line in after_toc:
                    if line.strip() or started:
                        result_lines.append(line)
                        started = True

                return "\n".join(result_lines)

        return page_text

    def inspect_package(self) -> EpubPackageInfo:
        from .package import inspect_package

        return inspect_package(self)

    def get_spine_documents(
        self,
        raw: bool = True,
        include_byte_offsets: bool = True,
        include_non_linear: bool = False,
        include_nav_documents: bool = False,
    ) -> list[SourceDocument]:
        from .package import get_spine_documents

        return get_spine_documents(
            self,
            include_byte_offsets=include_byte_offsets,
            include_non_linear=include_non_linear,
            include_nav_documents=include_nav_documents,
        )

    def get_navigation(self) -> list[NavigationEntry]:
        from .nav import navigation_from_parser

        return navigation_from_parser(self, self.get_spine_documents())

    def extract_structured(
        self,
        *,
        policy: ExtractionPolicy | None = None,
        include_raw_documents: bool = False,
        include_offsets: bool = True,
        include_inline_runs: bool = True,
        include_segments: bool = False,
        include_xhtml_fragments: bool = False,
        include_markdown_fragments: bool = False,
        markdown_flavor: Literal["commonmark", "gfm"] | None = None,
        segment_mode: str = "sentence",
    ) -> StructuredEpubExtraction:
        from .blocks import extract_blocks
        from .diagnostics import StrictExtractionError
        from .fragments import (
            render_block_xhtml_fragment,
            render_segment_xhtml_fragment,
        )
        from .markdown_fragments import (
            render_block_markdown_fragment,
            render_segment_markdown_fragment,
        )
        from .nav import navigation_from_parser
        from .package import inspect_package
        from .segments import extract_segments
        from .source import sha256_bytes
        from .toc_map import annotate_blocks_with_navigation

        extraction_policy = policy or ExtractionPolicy()
        if markdown_flavor is not None:
            extraction_policy = replace(
                extraction_policy, markdown_flavor=markdown_flavor
            )
        cache_key = (
            repr(extraction_policy),
            include_raw_documents,
            include_offsets,
            include_inline_runs,
            include_segments,
            include_xhtml_fragments,
            include_markdown_fragments,
            markdown_flavor,
            segment_mode,
        )
        cached = self._structured_cache.get(cache_key)
        if cached is not None:
            return cached
        documents = self.get_spine_documents(
            include_byte_offsets=include_offsets,
            include_non_linear=extraction_policy.include_non_linear_spine,
            include_nav_documents=extraction_policy.include_nav_documents,
        )
        navigation = navigation_from_parser(self, documents)
        blocks = []
        diagnostics = []
        for document in documents:
            document_blocks = extract_blocks(document, extraction_policy)
            if extraction_policy.resolve_css_emphasis and include_markdown_fragments:
                from .styles import resolve_block_styles

                styled_blocks = []
                for block in document_blocks:
                    root_style, span_styles, style_diagnostics = resolve_block_styles(
                        self, document, block
                    )
                    block = replace(
                        block,
                        computed_style=root_style,
                        computed_styles=span_styles,
                        diagnostics=[*block.diagnostics, *style_diagnostics],
                    )
                    styled_blocks.append(block)
                document_blocks = styled_blocks
            if include_xhtml_fragments or include_markdown_fragments:
                rendered_blocks = []
                for block in document_blocks:
                    if include_xhtml_fragments:
                        block = replace(
                            block,
                            xhtml_fragment=render_block_xhtml_fragment(
                                block, extraction_policy
                            ),
                        )
                    if include_markdown_fragments:
                        block = replace(
                            block,
                            markdown_fragment=render_block_markdown_fragment(
                                block, extraction_policy
                            ),
                        )
                    rendered_blocks.append(block)
                document_blocks = rendered_blocks
            blocks.extend(document_blocks)
            diagnostics.extend(document.diagnostics)
            for block in document_blocks:
                diagnostics.extend(block.diagnostics)
        blocks = annotate_blocks_with_navigation(blocks, navigation)
        segments = extract_segments(blocks, segment_mode) if include_segments else []
        if include_segments and (include_xhtml_fragments or include_markdown_fragments):
            blocks_by_id = {block.id: block for block in blocks}
            rendered_segments = []
            for segment in segments:
                block = blocks_by_id[segment.block_id]
                if include_xhtml_fragments:
                    segment = replace(
                        segment,
                        xhtml_fragment=render_segment_xhtml_fragment(
                            block, segment, extraction_policy
                        ),
                    )
                if include_markdown_fragments:
                    segment = replace(
                        segment,
                        markdown_fragment=render_segment_markdown_fragment(
                            block, segment, extraction_policy
                        ),
                    )
                rendered_segments.append(segment)
            segments = rendered_segments
        package = inspect_package(self)
        diagnostics.extend(package.diagnostics)
        for entry in navigation:
            diagnostics.extend(entry.diagnostics)
        for block in blocks:
            if block.xhtml_fragment is not None:
                diagnostics.extend(block.xhtml_fragment.diagnostics)
            if block.markdown_fragment is not None:
                diagnostics.extend(block.markdown_fragment.diagnostics)
        for segment in segments:
            if segment.xhtml_fragment is not None:
                diagnostics.extend(segment.xhtml_fragment.diagnostics)
            if segment.markdown_fragment is not None:
                diagnostics.extend(segment.markdown_fragment.diagnostics)
        if extraction_policy.strict_offsets and any(
            d.severity in {"warning", "error"} for d in diagnostics
        ):
            raise StrictExtractionError(diagnostics)
        result = StructuredEpubExtraction(
            source_path=str(self.filepath),
            source_sha256=sha256_bytes(self.filepath.read_bytes()),
            package=package,
            documents=documents,
            navigation=navigation,
            blocks=blocks,
            segments=segments,
            diagnostics=diagnostics,
        )
        self._structured_cache[cache_key] = result
        return result

    def extract_segments(
        self, mode: str = "sentence", *, policy: ExtractionPolicy | None = None
    ) -> list[TextSegment]:
        return self.extract_structured(
            policy=policy, include_segments=True, segment_mode=mode
        ).segments
