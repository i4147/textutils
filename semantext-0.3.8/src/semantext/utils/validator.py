import functools
import inspect
from typing import TypeVar, Callable
from pydantic import BaseModel, TypeAdapter, ValidationError

T = TypeVar("T", bound=BaseModel)


def validate_inputs(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        for param_name, param in sig.parameters.items():
            if param.annotation is inspect.Parameter.empty:
                continue
            if param_name in bound_args.arguments:
                data_to_validate = bound_args.arguments[param_name]
                try:
                    adapter = TypeAdapter(param.annotation)
                    validated_data = adapter.validate_python(data_to_validate)
                    bound_args.arguments[param_name] = validated_data
                except ValidationError as e:
                    raise ValueError(f"Argument '{param_name}' failed validation for type '{param.annotation}':\n{e}")
                except TypeError:
                    pass
        return func(*bound_args.args, **bound_args.kwargs)

    return wrapper
