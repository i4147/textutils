from .chunk import chunk_by_title
from .markdown import parse_markdown_elements
from .types import Chunk, Element

try:
    from .html import parse_html_elements
except Exception:

    def parse_html_elements(*args, **kwargs):
        msg = "parse_html_elements nécessite beautifulsoup4. Installe l'extra: pip install textnormx[html]"
        raise ImportError(msg)


__all__ = [
    "Chunk",
    "Element",
    "chunk_by_title",
    "parse_html_elements",
    "parse_markdown_elements",
]
