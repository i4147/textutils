import logging
import os
import sys


def configure_logging(level: str | int = "INFO") -> None:
    lvl = level if isinstance(level, int) else logging.getLevelName(level)
    logging.basicConfig(
        level=lvl,
        stream=sys.stdout,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def suppress_warnings() -> None:
    if os.environ.get("TEXTRL_VERBOSE"):
        return
    import warnings

    warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
    warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
