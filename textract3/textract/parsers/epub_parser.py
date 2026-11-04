from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup

from .utils import BaseParser


class Parser(BaseParser):
    def extract(self, filename, **kwargs):
        book = epub.read_epub(filename)
        result = ""
        for id, _ in book.spine:
            item = book.get_item_with_id(id)
            if item is None:
                continue
            soup = BeautifulSoup(item.content, "lxml")
            for child in soup.find_all(["title", "p", "div", "h1", "h2", "h3", "h4"]):
                result = result + child.text + "\n"
        return result
