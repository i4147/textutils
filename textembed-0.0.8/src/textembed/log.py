import logging
import sys
from enum import Enum
from typing import Any

logging.getLogger().handlers.clear()
log_handlers: list[Any] = []
try:
    from rich.console import Console
    from rich.logging import RichHandler

    rich_handler = RichHandler(console=Console(stderr=True), show_time=False)
    log_handlers.append(rich_handler)
except ImportError:
    log_handlers.append(logging.StreamHandler(sys.stderr))
LOG_LEVELS: dict[str, int] = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
    "trace": 5,
}
LOG_FORMAT = "%(asctime)s %(name)s %(levelname)s: %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=log_handlers,
)
logger = logging.getLogger("textembed")


class UvicornLogLevels(Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"
    TRACE = "trace"
