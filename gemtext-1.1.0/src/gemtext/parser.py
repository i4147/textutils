from collections.abc import Iterator
from functools import cached_property
from typing import Final


class Line:
    def __init__(self, content: str) -> None:
        self._content = content
        """The content of the line."""

    def __str__(self) -> str:
        return self._content

    def _repr_props(self) -> tuple[str, ...]:
        return (f"content={self._content!r}",)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({', '.join(self._repr_props())})"


class Paragraph(Line):
    pass


class ListItem(Line):
    pass


class Quote(Line):
    pass


class PreFormatted(Line):
    def __init__(self, content: str, alt_text: str = "") -> None:
        super().__init__(content)
        self._alt_text = alt_text
        """The alternative text for the preformatted block."""

    @property
    def alt_text(self) -> str:
        return self._alt_text

    @property
    def has_alt_text(self) -> bool:
        return bool(self._alt_text)

    def _repr_props(self) -> tuple[str, ...]:
        return super()._repr_props() + (f"alt_text={self._alt_text!r}",)


class Heading(Line):
    def __init__(self, content: str, level: int) -> None:
        super().__init__(content)
        self._level = level
        """The level of the heading."""

    @property
    def level(self) -> int:
        return self._level

    def _repr_props(self) -> tuple[str, ...]:
        return super()._repr_props() + (f"level={self._level!r}",)


class Link(Line):
    def __init__(self, uri: str, description: str) -> None:
        self._uri = uri.strip()
        """The description of the link."""
        super().__init__(description.strip() or self._uri)

    @property
    def uri(self) -> str:
        return self._uri

    def _repr_props(self) -> tuple[str, ...]:
        return super()._repr_props() + (f"uri={self._uri!r}",)


class SpartanPrompt(Link):
    pass


_LINK: Final[str] = "=>"
"""Marker for a link in Gemtext."""
_H1: Final[str] = "#"
"""Marker for a level 1 heading in Gemtext."""
_H2: Final[str] = "##"
"""Marker for a level 2 heading in Gemtext."""
_H3: Final[str] = "###"
"""Marker for a level 3 heading in Gemtext."""
_QUOTE: Final[str] = ">"
"""Marker for a quote in Gemtext."""
_PRE_FORMAT: Final[str] = "```"
"""Marker for preformatted text in Gemtext."""
_LIST_ITEM: Final[str] = "* "
"""Marker for a list item in Gemtext."""
_NON_CONFORMING_LIST_ITEM: Final[str] = "*\t"
"""Marker for a non-conforming list item in Gemtext."""
_SPARTAN_PROMPT: Final[str] = "=:"
"""Marker for a Spartan protocol prompt in Gemtext."""


class Gemtext:
    def __init__(self, text: str, *, with_spartan_support: bool = True) -> None:
        self._text = text
        """The raw Gemtext content to be parsed."""
        self._with_spartan_support = with_spartan_support
        """Whether to support Spartan protocol prompts."""

    def _parse(self) -> Iterator[Line]:
        in_preformat = False
        preformat_alt_text = ""
        preformat_content: list[str] = []
        for line in self._text.splitlines():
            is_a = line.startswith
            if is_a(_PRE_FORMAT):
                if in_preformat := not in_preformat:
                    preformat_alt_text = line.removeprefix(_PRE_FORMAT).strip()
                else:
                    yield PreFormatted("\n".join(preformat_content), preformat_alt_text)
                    preformat_alt_text = ""
                    preformat_content.clear()
            elif in_preformat:
                preformat_content.append(line)
            elif is_a(_LINK):
                parts = line.removeprefix(_LINK).strip().split(maxsplit=1)
                yield Link(parts[0], parts[1] if len(parts) > 1 else "")
            elif is_a(_QUOTE):
                yield Quote(line.removeprefix(_QUOTE).strip())
            elif is_a(_H3):
                yield Heading(line.removeprefix(_H3).strip(), 3)
            elif is_a(_H2):
                yield Heading(line.removeprefix(_H2).strip(), 2)
            elif is_a(_H1):
                yield Heading(line.removeprefix(_H1).strip(), 1)
            elif is_a(_LIST_ITEM):
                yield ListItem(line.removeprefix(_LIST_ITEM).strip())
            elif is_a(_NON_CONFORMING_LIST_ITEM):
                yield ListItem(line.removeprefix(_NON_CONFORMING_LIST_ITEM).strip())
            elif is_a(_SPARTAN_PROMPT) and self._with_spartan_support:
                parts = line.removeprefix(_SPARTAN_PROMPT).strip().split(maxsplit=1)
                yield SpartanPrompt(parts[0], parts[1] if len(parts) > 1 else "")
            else:
                yield Paragraph(line)
        if in_preformat:
            yield PreFormatted("\n".join(preformat_content), preformat_alt_text)

    @cached_property
    def content(self) -> tuple[Line, ...]:
        return tuple(self._parse())

    def __str__(self) -> str:
        return self._text
