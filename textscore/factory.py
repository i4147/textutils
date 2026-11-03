from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from textscore.constants import DEFAULT_DEVICE, DEFAULT_MODEL
from textscore.strategy import ComputeStrategy
from textscore.scorer import CausalLMScorer, TextScorer, ComputeSequencer


def scorer_factory(
    model_name_or_path: str | Path = DEFAULT_MODEL,
    compute_strategy: ComputeStrategy = ComputeStrategy.OPTIMAL,
    device: str = DEFAULT_DEVICE,
    *,
    verbose: bool = False,
) -> TextScorer:
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(model_name_or_path)
    model = model.eval()
    torch_device = torch.device(device)
    model = model.to(torch_device)
    compute_sequencer = ComputeSequencer(tokenizer=tokenizer, compute_strategy=compute_strategy)
    return CausalLMScorer(model=model, compute_sequencer=compute_sequencer, verbose=verbose)
