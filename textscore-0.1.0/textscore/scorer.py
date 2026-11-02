import torch
from transformers import PreTrainedModel
from tqdm.auto import tqdm
from textscore.sequencer import ComputeSequencer
from textscore.types import Text, TextScore


class TextScorer:
    def __call__(self, text: Text) -> TextScore: ...


class CausalLMScorer(TextScorer):
    def __init__(self, model: PreTrainedModel, compute_sequencer: ComputeSequencer, *, verbose: bool = False) -> None:
        self.model = model
        self.compute_sequencer = compute_sequencer
        self.verbose = verbose

    def __call__(self, text: Text) -> TextScore:
        neg_log_likelihood = torch.zeros(1)
        device = self.model.device
        sequence, sequence_len, text_len = self.compute_sequencer(text)
        if self.verbose:
            sequence = tqdm(sequence, total=sequence_len, desc="Computing score", unit="steps")
        for step in sequence:
            with torch.no_grad():
                inputs = step.inputs.to(device)
                targets = step.targets.to(device)
                outputs = self.model(inputs, labels=targets)
                neg_log_likelihood += outputs.loss * step.length
        return torch.exp(neg_log_likelihood / text_len).item()
