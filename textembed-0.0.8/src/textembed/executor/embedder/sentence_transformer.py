from typing import Dict, List, Tuple, Union
import numpy as np
import torch
from sentence_transformers import SentenceTransformer, util
from torch import Tensor
from textembed.engine.args import AsyncEngineArgs
from textembed.executor.base import BaseEmbedder
from textembed.executor.primitives import EmbeddingDtype


class SentenceTransformerEmbedder(SentenceTransformer, BaseEmbedder):
    def __init__(self, engine_args: AsyncEngineArgs) -> None:
        super().__init__(
            model_name_or_path=engine_args.model,
            device="cpu",
            trust_remote_code=engine_args.trust_remote_code,
        )
        self.embedding_dtype = engine_args.embedding_dtype
        self.engine_args = engine_args
        self.eval()

    async def warm_up(self) -> None:
        sample_sentences = ["This is a sample sentence."] * 10
        await self.process_batch(sample_sentences)

    async def preprocess(self, sentences: List[str]) -> Tuple[Dict[str, Tensor], List[Union[int, str]]]:
        tokenized = self.tokenize(sentences)
        usage = [len(sentence) if isinstance(sentence, str) else str(sentence.size) for sentence in sentences]
        return tokenized, usage

    async def transfer_to_device(self, features: Dict[str, Tensor]) -> Dict[str, Tensor]:
        return util.batch_to_device(features, self.device)

    async def generate_embeddings(self, features: Dict[str, Tensor]) -> Tensor:
        with torch.inference_mode():
            return self.forward(features)["sentence_embedding"]

    async def postprocess(self, out_features: Tensor) -> np.ndarray:
        embeddings: np.ndarray = out_features.detach().cpu().numpy()
        if self.embedding_dtype == EmbeddingDtype.BINARY.value:
            return (embeddings > 0).astype(np.uint8)
        elif self.embedding_dtype == EmbeddingDtype.FLOAT16.value:
            return embeddings.astype(np.float16)
        elif self.embedding_dtype == EmbeddingDtype.FLOAT32.value:
            return embeddings.astype(np.float32)
        else:
            raise ValueError(f"Unsupported dtype: {self.embedding_dtype}")

    async def process_batch(self, sentences: List[str]) -> Tuple[np.ndarray, List[int]]:
        features, lengths = await self.preprocess(sentences)
        features = await self.transfer_to_device(features)
        out_features = await self.generate_embeddings(features)
        embeddings = await self.postprocess(out_features)
        return embeddings, lengths
