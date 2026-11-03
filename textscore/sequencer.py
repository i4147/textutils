import math
from dataclasses import dataclass
from collections.abc import Iterable
import torch
from transformers import PreTrainedTokenizer
from textscore.strategy import ComputeStrategy
from textscore.types import Text

TORCH_IGNORE_INDEX = -100


@dataclass
class ComputeStep:
    inputs: torch.LongTensor
    targets: torch.LongTensor
    length: int


ComputeSequence = Iterable[ComputeStep]


class ComputeSequencer:
    def __init__(
        self, tokenizer: PreTrainedTokenizer, compute_strategy: ComputeStrategy = ComputeStrategy.OPTIMAL
    ) -> None:
        self.tokenizer = tokenizer
        self.compute_strategy = compute_strategy
        self.window_size = tokenizer.model_max_length
        self.stride = compute_strategy.stride_factory()(self.window_size)

    def __call__(self, text: Text) -> tuple[ComputeSequence, int, int]:
        tokens = self.tokenizer.tokenize(text)
        text_len = len(tokens)
        window_size, stride = self.window_size, self.stride
        sequence_len = max(1, math.ceil((text_len - window_size) / stride) + 1)

        def _sequencer() -> ComputeSequence:
            previous_end_idx = 0
            for step_idx in range(sequence_len):
                start_idx = step_idx * stride
                end_idx = min(start_idx + window_size, text_len)
                step_tokens = tokens[start_idx:end_idx]
                step_len = end_idx - previous_end_idx
                inputs = self.tokenizer.encode(step_tokens, return_tensors="pt")
                targets = inputs.clone()
                targets[:, :-step_len] = TORCH_IGNORE_INDEX
                yield ComputeStep(inputs=inputs, targets=targets, length=step_len)
                previous_end_idx = end_idx

        return _sequencer(), sequence_len, text_len
