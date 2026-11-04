from __future__ import annotations
from enum import Enum
import importlib


class Backend(Enum):
    NLTK = "NLTK"
    Stanza = "Stanza"

    @staticmethod
    def values() -> list[Backend]:

        return [Backend.NLTK, Backend.Stanza]

    @staticmethod
    def parse(backend: Backend | str) -> Backend | None:
        if isinstance(backend, Backend):
            return backend

        if not isinstance(backend, str):
            return None

        backend = backend.lower()
        return next(
            (candidate for candidate in Backend.values() if backend == candidate.value.lower()),
            None,
        )

    @staticmethod
    def is_supported(backend: Backend | str) -> bool:
        try:
            backend = Backend.parse(backend)
            if backend is None:
                return False

            module_name = backend.value.lower()
            importlib.import_module(module_name)
            return True
        except (ImportError, ModuleNotFoundError):
            return False

    @staticmethod
    def list_supported() -> list[Backend]:
        return [backend for backend in Backend.values() if Backend.is_supported(backend)]
