from importlib.metadata import version

__author__ = "Dave Pearson"
__copyright__ = "Copyright 2026, Dave Pearson"
__credits__ = ["Dave Pearson"]
__maintainer__ = "Dave Pearson"
__email__ = "davep@davep.org"
__version__: str = version("gemtext")
__licence__ = "MIT"
from .parser import (
    Gemtext,
    Heading,
    Line,
    Link,
    ListItem,
    Paragraph,
    PreFormatted,
    Quote,
    SpartanPrompt,
)

__all__ = [
    "Gemtext",
    "Heading",
    "Line",
    "Link",
    "ListItem",
    "Paragraph",
    "PreFormatted",
    "Quote",
    "SpartanPrompt",
]
