from typing import Any, List, Optional

import torch
from torch import Tensor
from torch.nn.utils.rnn import pad_sequence

__all__ = [
    "to_tensor",
    "truncate",
    "add_token",
    "str_to_int",
]


def to_tensor(input: Any, padding_value: Optional[int] = None, dtype: torch.dtype = torch.long) -> Tensor:
    if torch.jit.isinstance(input, List[int]):
        return torch.tensor(input, dtype=torch.long)
    elif torch.jit.isinstance(input, List[List[int]]):
        if padding_value is None:
            output = torch.tensor(input, dtype=dtype)
            return output
        else:
            output = pad_sequence(
                [torch.tensor(ids, dtype=dtype) for ids in input], batch_first=True, padding_value=float(padding_value)
            )
            return output
    else:
        raise TypeError("Input type not supported")


def truncate(input: Any, max_seq_len: int) -> Any:
    if torch.jit.isinstance(input, List[int]):
        return input[:max_seq_len]
    elif torch.jit.isinstance(input, List[str]):
        return input[:max_seq_len]
    elif torch.jit.isinstance(input, List[List[int]]):
        output: List[List[int]] = []
        for ids in input:
            output.append(ids[:max_seq_len])
        return output
    elif torch.jit.isinstance(input, List[List[str]]):
        output: List[List[str]] = []
        for ids in input:
            output.append(ids[:max_seq_len])
        return output
    else:
        raise TypeError("Input type not supported")


def add_token(input: Any, token_id: Any, begin: bool = True) -> Any:
    if torch.jit.isinstance(input, List[int]) and torch.jit.isinstance(token_id, int):
        if begin:
            return [token_id] + input
        else:
            return input + [token_id]
    elif torch.jit.isinstance(input, List[str]) and torch.jit.isinstance(token_id, str):
        if begin:
            return [token_id] + input
        else:
            return input + [token_id]
    elif torch.jit.isinstance(input, List[List[int]]) and torch.jit.isinstance(token_id, int):
        output: List[List[int]] = []

        if begin:
            for ids in input:
                output.append([token_id] + ids)
        else:
            for ids in input:
                output.append(ids + [token_id])

        return output
    elif torch.jit.isinstance(input, List[List[str]]) and torch.jit.isinstance(token_id, str):
        output: List[List[str]] = []
        if begin:
            for ids in input:
                output.append([token_id] + ids)
        else:
            for ids in input:
                output.append(ids + [token_id])

        return output
    else:
        raise TypeError("Input type not supported")


def str_to_int(input: Any) -> Any:
    if torch.jit.isinstance(input, List[str]):
        output: List[int] = []
        for element in input:
            output.append(int(element))
        return output
    if torch.jit.isinstance(input, List[List[str]]):
        output: List[List[int]] = []
        for ids in input:
            current: List[int] = []
            for element in ids:
                current.append(int(element))
            output.append(current)
        return output
    else:
        raise TypeError("Input type not supported")
