from __future__ import annotations

import io
from functools import cached_property
from pathlib import Path
from typing import Union

import freetype
import uharfbuzz as hb
from fontTools.ttLib import TTFont

FontLike = Union["Font", str, Path, bytes]


class Font:
    def __init__(self, source: str | Path | bytes, index: int = 0, name: str | None = None):
        if isinstance(source, (bytes, bytearray)):
            data = bytes(source)
        else:
            path = Path(source)
            data = path.read_bytes()
            name = name or path.name

        self.data = data
        self.index = index
        self.name = name or f"<font {hash(data) & 0xFFFFFF:06x}>"

    @classmethod
    def load(cls, source: FontLike, index: int = 0) -> "Font":
        if isinstance(source, Font):
            return source
        return cls(source, index)

    @cached_property
    def hb_font(self) -> hb.Font:
        face = hb.Face(hb.Blob(self.data), self.index)
        font = hb.Font(face)
        font.scale = (face.upem, face.upem)
        return font

    @cached_property
    def upem(self) -> int:
        return self.hb_font.face.upem

    @cached_property
    def space_gid(self) -> int:
        return self.hb_font.get_nominal_glyph(0x20) or -1

    @cached_property
    def ft_face(self) -> freetype.Face:
        return freetype.Face(io.BytesIO(self.data), self.index)

    def ttfont(self, lazy: bool | None = None) -> TTFont:
        return TTFont(io.BytesIO(self.data), fontNumber=self.index, lazy=lazy)

    @cached_property
    def _cmap(self) -> dict:
        return self.ttfont(lazy=True).getBestCmap()

    def covers(self, char: str) -> bool:
        return ord(char) in self._cmap

    def glyph_name(self, gid: int) -> str:
        return self.glyph_order[gid]

    @cached_property
    def glyph_order(self) -> list[str]:
        return list(self.ttfont(lazy=True).getGlyphOrder())

    def __repr__(self) -> str:
        return f"Font({self.name!r}, upem={self.upem})"
