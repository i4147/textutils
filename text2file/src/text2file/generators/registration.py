import sys
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Set, TypeVar, cast

GeneratorFunc = TypeVar("GeneratorFunc", bound=Callable[..., Path])


class GeneratorRegistry:
    _instance: ClassVar[Optional["GeneratorRegistry"]] = None
    _generators: Dict[str, GeneratorFunc]
    _supported_extensions: Set[str]

    def __new__(cls) -> "GeneratorRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._generators = {}
            cls._instance._supported_extensions = set()
        return cls._instance

    def register_generator(self, ext: str, func: GeneratorFunc) -> None:
        ext = ext.lstrip(".").lower()
        self._generators[ext] = func
        self._supported_extensions.add(ext)
        print(f"DEBUG: Registered generator for .{ext}", file=sys.stderr)
        print(
            f"DEBUG: Current generators: {list(self._generators.keys())}",
            file=sys.stderr,
        )
        print(
            f"DEBUG: Current supported extensions: {self._supported_extensions}",
            file=sys.stderr,
        )

    def get_generator(self, ext: str) -> Optional[GeneratorFunc]:
        ext = ext.lstrip(".").lower()
        return self._generators.get(ext)

    def get_supported_extensions(self) -> Set[str]:
        return self._supported_extensions.copy()


_registry = GeneratorRegistry()


def register_generator(
    extensions: List[str],
) -> Callable[[GeneratorFunc], GeneratorFunc]:

    def decorator(func: GeneratorFunc) -> GeneratorFunc:
        for ext in extensions:
            _registry.register_generator(ext, func)
        return func

    return decorator


def register_generator_directly(extensions: List[str], func: GeneratorFunc) -> None:
    for ext in extensions:
        _registry.register_generator(ext, func)


def get_generator(extension: str) -> Optional[GeneratorFunc]:
    return _registry.get_generator(extension)


def get_supported_extensions() -> Set[str]:
    return _registry.get_supported_extensions()
