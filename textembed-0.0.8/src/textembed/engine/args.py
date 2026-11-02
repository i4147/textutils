import multiprocessing
from dataclasses import dataclass
from typing import Optional, Union
from textembed.executor.primitives import EmbeddingDtype


@dataclass
class AsyncEngineArgs:
    model: str
    served_model_name: Optional[Union[str, None]]
    trust_remote_code: bool = True
    workers: int = multiprocessing.cpu_count()
    batch_size: int = 32
    embedding_dtype: str = "float32"

    def __post_init__(self):
        if self.served_model_name is None:
            self.served_model_name = self.model
        if self.batch_size < 1:
            raise ValueError("Batch size must be greater than or equal to 1.")
        if self.workers < 1:
            raise ValueError("Number of workers must be greater than or equal to 1.")
        if self.embedding_dtype not in [dtype.value for dtype in EmbeddingDtype]:
            raise ValueError(
                f"Unsupported embedding dtype: '{self.embedding_dtype}'. "
                f"Valid dtype are: {[dtype.value for dtype in EmbeddingDtype]}."
            )
