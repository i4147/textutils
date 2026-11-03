from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datasets import Dataset
    from textnoisr import noise


def _add_noise_to_example(
    example: dict,
    noise_augmenter: noise.CharNoiseAugmenter,
    feature_name: str,
) -> dict:
    example[feature_name] = noise_augmenter.add_noise(example[feature_name])
    return example


def add_noise(
    dataset: Dataset,
    noise_augmenter: noise.CharNoiseAugmenter,
    feature_name: str = "tokens",
    **kwargs: Any,
) -> Dataset:
    return dataset.map(lambda x: _add_noise_to_example(x, noise_augmenter, feature_name), **kwargs)
