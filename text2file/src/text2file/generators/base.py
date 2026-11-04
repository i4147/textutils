from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional, Union


class BaseGenerator(ABC):
    @classmethod
    @abstractmethod
    def generate(
        cls,
        content: str,
        output_path: Union[str, Path],
        **kwargs: Any,
    ) -> Path:
        raise NotImplementedError("Subclasses must implement generate()")
