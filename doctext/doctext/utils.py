# -*- coding: utf-8 -*-

import subprocess
import logging


def run_checked(command, return_output: bool = False) -> bool | tuple[bool, str, str]:

    logging.debug(f"Running shell command: {command}")

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        if return_output:
            return (False, result.stdout, result.stderr)
        return False
    if return_output:
        return (True, result.stdout, result.stderr)
    return True


def log_exception(logger: logging.Logger, e: Exception, message: str = None):
    if message:
        logger.warning(message)
    if logger.getEffectiveLevel() <= logging.WARNING:
        logger.exception(e)
