from enum import Enum
from typing import List, NamedTuple, NoReturn
import numpy as np
from scipy.sparse import csr_matrix, spmatrix
import torch


class Constants(NamedTuple):
    kwargs = "kwargs"
    frozen = "_frozen"
    default_model = "default"
    default_seed = 123456
    """The default random seed."""


class OutputType(Enum):
    array = np.ndarray
    sparse = spmatrix
    tensor = torch.Tensor

    @staticmethod
    def from_object(obj):
        for typ in OutputType.__members__.values():
            if isinstance(obj, typ.value):
                return typ
        msg = "Not a valid type!"
        raise ValueError(msg)


def check_false(expression: bool, exception: Exception) -> NoReturn:
    if expression:
        raise exception


def check_true(expression: bool, exception: Exception) -> NoReturn:
    if not expression:
        raise exception


def split_tokenizer(document: str) -> list[str]:
    return document.split()


def convert(arr, typ: OutputType, dtype=None, detach=False):
    if arr is None:
        return arr
    if isinstance(arr, list):
        return [convert(x, typ, dtype=dtype, detach=detach) for x in arr]
    if isinstance(arr, np.ndarray):
        if issubclass(typ.value, spmatrix):
            arr = csr_matrix(arr)
            if dtype is not None and arr.dtype != dtype:
                return arr.astype(dtype)
            return arr
        elif issubclass(typ.value, torch.Tensor):
            arr = torch.from_numpy(arr).to(device)
            if dtype is not None and arr.dtype != dtype:
                return arr.type(dtype)
            return arr
        if dtype is not None and arr.dtype != dtype:
            return np.asarray(arr.astype(dtype))
        return np.asarray(arr)
    elif isinstance(arr, spmatrix):
        if issubclass(typ.value, np.ndarray):
            arr = np.array(arr.todense())
            if dtype is not None and arr.dtype != dtype:
                return np.asarray(arr.astype(dtype))
            return np.asarray(arr)
        elif issubclass(typ.value, torch.Tensor):
            arr = torch.from_numpy(arr.todense()).to(device)
            if dtype is not None and arr.dtype != dtype:
                return arr.type(dtype)
            return arr
        if dtype is not None and arr.dtype != dtype:
            return arr.astype(dtype)
        return arr
    elif isinstance(arr, torch.Tensor):
        if issubclass(typ.value, np.ndarray):
            arr = arr.detach().cpu().numpy()
            if dtype is not None and arr.dtype != dtype:
                return np.asarray(arr.astype(dtype))
            return np.asarray(arr)
        elif issubclass(typ.value, spmatrix):
            arr = csr_matrix(arr.detach().cpu().numpy())
            if dtype is not None and arr.dtype != dtype:
                return arr.astype(dtype)
            return arr
        if dtype is not None and arr.dtype != dtype:
            return arr.type(dtype)
        return arr.detach() if detach else arr
    else:
        msg = "Unsupported input type"
        raise ValueError(msg)


def set_params(obj, **kwargs):
    for k, v in kwargs.items():
        parts = k.split("__", 1)
        if len(parts) == 1:
            if isinstance(obj, dict):
                obj[k] = v
            elif isinstance(obj, (tuple, list)):
                if isinstance(obj[1], dict):
                    obj[1][k] = v
                else:
                    obj[int(k)] = v
            elif hasattr(obj, "_set"):
                obj._set(k, v)
            else:
                setattr(obj, k, v)
        else:
            attr_name, key = parts
            if isinstance(obj, (dict, list)):
                if attr_name.isnumeric():
                    attr_name = int(attr_name)
                if isinstance(obj[attr_name], str):
                    obj[attr_name] = [obj[attr_name], dict()]
                set_params(obj[attr_name], **{key: v})
            else:
                set_params(getattr(obj, attr_name), **{key: v})


device = None
if torch.cuda.is_available():
    device = torch.device("cuda:0")
else:
    device = torch.device("cpu")
