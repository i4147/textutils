import datetime as dt
import logging
import os
import sys
import time

logger = None
start = 0


def set_logger(args=None, name=None, file=None):
    global logger
    if name is None:
        name = sys.argv[0]
    if logger:
        msg = "Odd, we should not have a logger yet?"
        raise Exception(msg)
    logger = logging.getLogger(name)
    if args and hasattr(args, "d") and args.d:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO
    logger.setLevel(lvl)
    fmt = logging.Formatter("%(asctime)s|%(levelname)s|%(name)s|%(message)s")
    hndlr = logging.StreamHandler(sys.stderr)
    hndlr.setFormatter(fmt)
    logger.addHandler(hndlr)
    if not file and args and hasattr(args, "outpref"):
        dt = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        file = args.outpref + f".{dt}.log"
    if not file and args and hasattr(args, "outdir"):
        dt = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        file = os.path.join(args.outdir, f"{dt}.log")
    if file:
        hdnlr = logging.FileHandler(file)
        hndlr.setFormatter(fmt)
        logger.addHandler(hdnlr)
    logger.info("Started: {}".format(dt.datetime.now().strftime("%Y-%m-%d %H:%M%S")))
    if args:
        logger.info("Arguments: {}".format(args))
    return logger


def ensurelogger():
    global logger
    if not logger:
        logger = logging.getLogger("UNINITIALIZEDLOGGER")
    return logger


def run_start():
    global start
    start = time.time()
    return start


def run_stop():
    logger = ensurelogger()
    if start == 0:
        logger.warning("Run timing not set up properly, no time!")
        return "", 0
    stop = time.time()
    delta = stop - start
    deltastr = str(dt.timedelta(seconds=delta))
    logger.info(f"Runtime: {deltastr}")
    return deltastr, delta


def file4logger(thelogger, noext=False):
    lpath = None
    for h in thelogger.handlers:
        if isinstance(h, logging.FileHandler):
            lpath = h.baseFilename
            if noext:
                lpath = os.path.splitext(lpath)[0]
            break
    return lpath
