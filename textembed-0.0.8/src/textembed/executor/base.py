from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Union
import numpy as np
from torch import Tensor


class BaseEmbedder(ABC):
    @abstractmethod
    async def preprocess(self, sentences: List[str]) -> Tuple[Dict[str, Tensor], List[Union[int, str]]]:
        pass

    @abstractmethod
    async def transfer_to_device(self, features: Dict[str, Tensor]) -> Dict[str, Tensor]:
        pass

    @abstractmethod
    async def generate_embeddings(self, features: Dict[str, Tensor]) -> Tensor:
        pass

    @abstractmethod
    async def postprocess(self, out_features: Tensor) -> np.ndarray:
        pass

    @abstractmethod
    async def process_batch(self, sentences: List[str]) -> Tuple[np.ndarray, List[int]]:
        pass
