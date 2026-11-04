from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# from builtins import int

import sys
import traceback
import warnings
import pdb


class UIErrorWrapper:
    do_throw_both = True
    do_throw_exceptions = True
    do_throw_warnings = True

    do_soft_exit = False

    err_log_stream = sys.stderr

    def __init__(self, err):
        pass

    @classmethod
    def raise_error(cls, err):
        if cls.do_throw_both and cls.do_throw_exceptions:
            if not cls.do_soft_exit:
                print("Error thrown using UIErrorWrapper", file=cls.err_log_stream)
                raise (err)
            else:
                print("")
                print("*******************************")
                print("An internal error has occurred.")
                print("This program will exit. Contact")
                print("the author with a bug report.")
                print("*******************************")
                print("")
                sys.exit(1)

    @classmethod
    def warn(cls, msg):
        if cls.do_throw_both and cls.do_throw_warnings:
            warnings.warn(msg)


class UIError(Exception):
    pass


class UITypeError(UIError):
    pass


class UIValueError(UIError):
    pass


class UIOptNoneError(UIError):
    pass


class UITermError(UIError):
    pass


class UICallbackError(UIError):
    def __init__(self, callback):
        message = (
            "A callback has not returned a new _CallBack instance.\n"
            "See above the traceback for the menu hierarchy leading to the bad call"
        )
        super(UICallbackError, self).__init__(message)
        hierarchy = callback.get_menu_hierarchy()
        for i in range(len(hierarchy)):
            mstr = "  " * i + "--> " + hierarchy[i]
            print(mstr)
