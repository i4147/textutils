from __future__ import annotations

import os
import sys

from loguru import logger

__all__ = ["apply_process_priority"]


def apply_process_priority(priority: str) -> None:
    if priority != "low":
        return

    if sys.platform == "win32":
        _apply_below_normal_windows()
    else:
        _apply_nice_posix()


def _apply_nice_posix() -> None:
    try:
        new_nice = os.nice(10)
        logger.debug("os.nice(10) applied; current niceness={}", new_nice)
    except OSError as exc:
        logger.debug("os.nice failed: {}", exc)


def _apply_below_normal_windows() -> None:
    try:
        import psutil
    except ImportError:
        logger.debug("psutil not available; skipping Windows priority adjustment")
        return
    try:
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        logger.debug("BELOW_NORMAL_PRIORITY_CLASS applied")
    except (psutil.Error, OSError) as exc:
        logger.debug("psutil priority adjustment failed: {}", exc)
