from typing import Any, Callable, Optional, Union


class SimpleValidator:
    def __init__(
        self,
        _type: type | tuple[type, ...] = object,
        /,
        literal: Optional[Any | tuple[Any, ...]] = ...,
        valuer: Optional[Callable[[Any], bool]] = ...,
        default: Optional[Any] = ...,
    ) -> None:
        self._type = _type
        self.literal = literal
        self.valuer = (lambda _: True) if valuer is ... else valuer
        self.default = default
        self.name: str

    def __set_name__(self, _: type, name: str) -> None:
        self.name = name

    def __set__(self, instance: object, value: Any) -> None:
        if isinstance(value, self.__class__):
            return
        if not isinstance(value, self._type):
            msg = (
                f"invalid type for {self.name!r}: expected "
                f"{tuple_repr(self._type, is_type=True)}; "
                f"got {value.__class__.__name__!r} instead"
            )
            raise TypeError(msg)
        if self.literal is not ...:
            if not isinstance(self.literal, tuple):
                self.literal = (self.literal,)
            if value not in self.literal:
                msg = f"invalid value for {self.name!r}: expected {tuple_repr(self.literal)}; got {value!r} instead"
                raise ValueError(msg)
        if not self.valuer(value):
            msg = f"invalid value for {self.name!r}: {value}"
            raise ValueError(msg)
        instance.__dict__[self.name] = value

    def __get__(self, instance: object, owner: type) -> Any:
        if not instance:
            return self
        if self.name not in instance.__dict__:
            if self.default is ...:
                msg = f"{owner.__name__!r} object has no attribute {self.name!r}"
                raise AttributeError(msg)
            instance.__dict__[self.name] = self.default
        return instance.__dict__[self.name]

    def __delete__(self, instance: object) -> None:
        del instance.__dict__[self.name]


def tuple_repr(maybe_tuple: Any | tuple[Any, ...], is_type: bool = False) -> str:
    maybe_tuple = maybe_tuple if isinstance(maybe_tuple, tuple) else (maybe_tuple,)
    if is_type:
        maybe_tuple = [x.__name__ for x in maybe_tuple]
    if len(maybe_tuple) == 0:
        return ""
    elif len(maybe_tuple) == 1:
        return repr(maybe_tuple[0])
    elif len(maybe_tuple) == 2:
        return "'" + "' or '".join(maybe_tuple) + "'"
    else:
        return "'" + "', '".join(maybe_tuple[:-1]) + f"', or {maybe_tuple[-1]!r}"
