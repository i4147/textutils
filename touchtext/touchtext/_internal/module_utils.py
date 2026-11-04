import importlib.util


def is_module_available(*modules: str) -> bool:
    return all(importlib.util.find_spec(m) is not None for m in modules)
