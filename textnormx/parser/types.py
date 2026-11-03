from dataclasses import dataclass
from typing import Any, Dict, Literal

ElementType = Literal["Title", "Text", "Table"]
ChunkType = Literal["Text", "Table"]


@dataclass
class Element:
    type: ElementType
    text: str
    page: int = 1


@dataclass
class Chunk:
    text: str
    element_id: str
    type: ChunkType
    metadata: dict[str, Any]
