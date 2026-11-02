from dataclasses import dataclass
from typing import Any


@dataclass
class HFRollout:
    backend: str = "hf"

    def apply(self, config: Any) -> Any:
        return config
