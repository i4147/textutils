from typing import Any
from datasets import Dataset


def _columns(ds: Dataset) -> set[str]:
    return set(ds.column_names)


def _require(ds: Dataset, required: set[str], *, name: str) -> None:
    missing = required - _columns(ds)
    if missing:
        raise ValueError(
            f"Dataset for {name} is missing required columns: {sorted(missing)}. Got: {sorted(_columns(ds))}"
        )


def validate_prompt_dataset(ds: Any) -> Dataset:
    if not isinstance(ds, Dataset):
        raise TypeError(f"Expected datasets.Dataset, got {type(ds).__name__}")
    cols = _columns(ds)
    if "prompt" not in cols and "messages" not in cols:
        raise ValueError(f"Prompt dataset must have 'prompt' or 'messages' column. Got: {sorted(cols)}")
    return ds


def validate_preference_dataset(ds: Any) -> Dataset:
    if not isinstance(ds, Dataset):
        raise TypeError(f"Expected datasets.Dataset, got {type(ds).__name__}")
    _require(ds, {"prompt", "chosen", "rejected"}, name="preference")
    return ds


def validate_kto_dataset(ds: Any) -> Dataset:
    if not isinstance(ds, Dataset):
        raise TypeError(f"Expected datasets.Dataset, got {type(ds).__name__}")
    _require(ds, {"prompt", "completion", "label"}, name="kto")
    return ds


def validate_reward_model_dataset(ds: Any) -> Dataset:
    if not isinstance(ds, Dataset):
        raise TypeError(f"Expected datasets.Dataset, got {type(ds).__name__}")
    _require(ds, {"chosen", "rejected"}, name="reward_model")
    return ds
