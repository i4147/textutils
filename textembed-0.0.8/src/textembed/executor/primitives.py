from enum import Enum
from typing import Literal

ModelCapabilities = Literal["embedding"]


class EmbeddingDtype(Enum):
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BINARY = "binary"
