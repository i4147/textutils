import datetime
from pathlib import Path
import sys
import logging
import logging.handlers
from typing import Any, cast
import click_log

EXIT_LEVEL = 35
logging.addLevelName(EXIT_LEVEL, "exit")


class PretextLogger(logging.Logger):
    def exit(self, message: object, *args: Any, **kwargs: Any) -> None:
        self.log(EXIT_LEVEL, message, *args, **kwargs)


logging.setLoggerClass(PretextLogger)
log = cast(PretextLogger, logging.getLogger("ptxlogger"))
log.__class__ = PretextLogger
logging.setLoggerClass(logging.Logger)


class ColorFormatter(click_log.ColorFormatter):
    colors = {
        **click_log.ColorFormatter.colors,
        "fatal": dict(fg="red", bold=True),
        "bug": dict(fg="magenta"),
        "fallback": dict(fg="cyan"),
        "exit": dict(fg="red"),
    }


def add_log_stream_handler() -> None:
    click_handler = logging.StreamHandler(sys.stdout)
    click_handler.setFormatter(ColorFormatter())
    log.addHandler(click_handler)


def get_log_error_flush_handler() -> logging.handlers.MemoryHandler:
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(ColorFormatter())
    sh.setLevel(logging.ERROR)
    error_flush_handler = logging.handlers.MemoryHandler(
        capacity=1024 * 100,
        flushLevel=100,
        target=sh,
        flushOnClose=False,
    )
    error_flush_handler.setLevel(logging.ERROR)
    log.addHandler(error_flush_handler)
    return error_flush_handler


def add_log_file_handler(log_folder_path: Path) -> None:
    log_folder_path.mkdir(exist_ok=True)
    logfile = log_folder_path / f"{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    fh = logging.FileHandler(logfile, mode="w")
    fh.setLevel(logging.DEBUG)
    file_log_format = logging.Formatter("{levelname:<8}: {message}", style="{")
    fh.setFormatter(file_log_format)
    log.addHandler(fh)
