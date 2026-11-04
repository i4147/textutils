from __future__ import print_function, division, absolute_import
# from builtins import int

from collections import OrderedDict
import copy
import datetime as dt
import re
import sys

from .uiutils import print_in_columns
from .uierrors import UIErrorWrapper, UITypeError, UIValueError, UIOptNoneError


if sys.version_info.major == 2:
    text_input = raw_input
    from backports.shutil_get_terminal_size import get_terminal_size
elif sys.version_info.major == 3:
    text_input = input
    from shutil import get_terminal_size
else:
    raise NotImplementedError("No text input function defined for Python version {}".format(sys.version_info.major))


def user_input_list(
    prompt, options, returntype="value", currentvalue=None, emptycancel=True, printcols=True, **printcolargs
):

    if type(prompt) is not str:
        UIErrorWrapper.raise_error(UITypeError("prompt must be a string"))
    if type(options) is not list and type(options) is not tuple:
        UIErrorWrapper.raise_error(UITypeError("options must be a list or tuple"))
    if type(returntype) is not str or returntype.lower() not in ["value", "index"]:
        UIErrorWrapper.raise_error(UITypeError("returntype must be one of the strings 'value' or 'index'"))
    if type(emptycancel) is not bool:
        UIErrorWrapper.raise_error(UITypeError("emptycancel must be a bool"))

    print(prompt)
    if emptycancel:
        print("A empty answer will cancel.")
    if currentvalue is not None:
        print("The current value is marked with a *")

    entries = []
    for i in range(1, len(options) + 1):
        if currentvalue is not None and options[i - 1] == currentvalue:
            currstr = "*"
        else:
            currstr = " "
        entries.append("  {2}{0}: {1}".format(i, options[i - 1], currstr))

    if printcols:
        print_in_columns(entries, **printcolargs)
    else:
        print("\n".join(entries))

    while True:
        userans = text_input("Enter 1-{0}: ".format(len(options)))
        if len(userans) == 0:
            if emptycancel:
                return None
            else:
                continue

        try:
            userans = int(userans)
        except ValueError:
            print("Input invalid")
        else:
            if userans > 0 and userans <= len(options):
                break

    if returntype.lower() == "value":
        return options[userans - 1]
    elif returntype.lower() == "index":
        return userans - 1
    else:
        UIErrorWrapper.raise_error(
            UIValueError("Value '{0}' for keyword 'returntype' is not recognized".format(returntype))
        )


def user_input_date(prompt, currentvalue=None, emptycancel=True, req_time_part="day", smallest_allowed_time_part=None):

    if currentvalue is not None and type(currentvalue) is not dt.datetime and type(currentvalue) is not dt.date:
        UIErrorWrapper.raise_error(
            UITypeError("If given, currentvalue must be a datetime.date or datetime.datetime instance")
        )
    elif type(currentvalue) is dt.date:
        currentvalue = dt.datetime(currentvalue.year, currentvalue.month, currentvalue.day)

    if type(emptycancel) is not bool:
        UIErrorWrapper.raise_error(UITypeError("If given, emptycancel must be a bool"))

    time_formats = OrderedDict([
        ("year", "%Y"),
        ("month", "%Y-%m"),
        ("day", "%Y-%m-%d"),
        ("hour", "%Y-%m-%d %H"),
        ("minute", "%Y-%m-%d %H:%M"),
        ("second", "%Y-%m-%d %H:%M:%S"),
    ])
    if req_time_part not in time_formats:
        UIErrorWrapper.raise_error(
            UITypeError("req_time_part must be one of: {}".format(", ".join(time_formats.keys())))
        )
    elif smallest_allowed_time_part not in time_formats and smallest_allowed_time_part is not None:
        UIErrorWrapper.raise_error(
            UITypeError("smallest_allowed_time_part must be one of: {}".format(", ".join(time_formats.keys())))
        )
    else:
        key_ind = time_formats.keys().index(req_time_part)
        if smallest_allowed_time_part is None:
            smallest_ind = key_ind + 1
        else:
            smallest_ind = time_formats.keys().index(smallest_allowed_time_part) + 1

        if smallest_ind <= key_ind:
            UIErrorWrapper.raise_error(
                UIValueError("req_time_part must be a larger piece of time than smallest_allowed_time_part")
            )
        allowed_time_fmts = time_formats.values()[key_ind:smallest_ind]
        allowed_fmts_str = ", ".join([_human_readable_time_format(fmt) for fmt in allowed_time_fmts])

    print(prompt)
    print("Enter in one of the formats: {}".format(allowed_fmts_str))
    if len(allowed_time_fmts) > 1:
        print("Any omitted parts will be set to 0 or 1, as appropriate")

    if emptycancel:
        print("Entering nothing will cancel")

    if currentvalue is not None:
        print("Current value is {0}".format(currentvalue))

    while True:
        userdate = text_input("--> ")
        userdate = userdate.strip()
        if len(userdate) == 0:
            if emptycancel:
                return None
            else:
                print("You must enter a value")
                continue

        matching_fmt = None
        for fmt in allowed_time_fmts:
            if len(userdate) == len(_human_readable_time_format(fmt)):
                matching_fmt = fmt
                break

        if matching_fmt is None:
            print("Wrong number of characters. Allowed formats are: {}".format(allowed_fmts_str))
            continue

        try:
            dateout = dt.datetime.strptime(userdate, matching_fmt)
        except ValueError:
            print('Cannot understand "{}" as "{}"'.format(userdate, matching_fmt))

        return dateout


def _human_readable_time_format(fmt):
    translation_dict = {"%Y": "yyyy", "%m": "mm", "%d": "dd", "%H": "HH", "%M": "MM", "%S": "SS"}
    for k, v in translation_dict.items():
        fmt = fmt.replace(k, v)
    return fmt


def user_input_value(prompt, testfxn=None, testmsg=None, currval=None, returntype=str, emptycancel=True):

    if type(prompt) is not str:
        UIErrorWrapper.raise_error(UITypeError("prompt must be a string"))
    if testfxn is not None and not isinstance(testfxn, type(lambda: 0)):
        UIErrorWrapper.raise_error(UITypeError("testfxn must be a function"))
    if testmsg is not None and type(testmsg) is not str:
        UIErrorWrapper.raise_error(UITypeError("testmsg must be a string"))
    if testmsg is None and testfxn is not None:
        UIErrorWrapper.warn("If you specify a testfxn but no testmsg it will not be clear to the user what is wrong")
    if type(emptycancel) is not bool:
        UIErrorWrapper.raise_error(UITypeError("If given, emptycancel must be a bool"))

    if testfxn is None:
        testfxn = lambda value: True
    if testmsg is None:
        testmsg = "That is not an allowed value"

    print(prompt)
    if currval is not None:
        print("The current value is {0}".format(currval))

    while True:
        if returntype is bool:
            userans = text_input("T/F: ").lower().strip()
            if userans == "t":
                return True
            elif userans == "f":
                return False
            elif len(userans) == 0:
                return None
            else:
                print("Option is a boolean. Must enter T or F.")
        else:
            userans = text_input("--> ").strip()
            if len(userans) == 0 and emptycancel:
                return None
            elif len(userans) == 0 and not emptycancel:
                print("Cannot enter an empty value.")
            else:
                try:
                    userans = returntype(userans)
                except ValueError:
                    print("Could not convert your input to {0}, try again".format(returntype.__name__))
                else:
                    if testfxn(userans):
                        return userans
                    else:
                        print(testmsg)


def user_input_yn(prompt, default="y"):

    if type(prompt) is not str:
        UIErrorWrapper.raise_error(UITypeError("prompt must be a string"))
    if type(default) is not str or default not in "YyNn":
        UIErrorWrapper.raise_error(UITypeError("default must be the string 'y' or 'n'"))

    while True:
        if default in "Yy":
            defstr = " [y]/n"
            defaultans = True
        else:
            defstr = " y/[n]"
            defaultans = False
        userans = text_input(prompt + defstr + ": ")

        if userans == "":
            return defaultans
        elif userans.lower() == "y":
            return True
        elif userans.lower() == "n":
            return False
        else:
            print("Enter y or n only. ", end="")


def user_onoff_list(
    prompt, options, currentstate=None, feedback_level=2, returntype="opts", printcols=True, **printcolargs
):
    if type(prompt) is not str:
        UIErrorWrapper.raise_error(UITypeError("prompt must be a string"))
    if type(options) is not list and type(options) is not tuple:
        UIErrorWrapper.raise_error(UITypeError("options must be a list or tuple"))
    elif not all([type(x) is str for x in options]):
        UIErrorWrapper.raise_error(UITypeError("options must be a list or tuple of strings"))
    if currentstate is None:
        currentstate = [False] * len(options)
    elif type(currentstate) is not list or not all([type(x) is bool for x in currentstate]):
        UIErrorWrapper.raise_error(UITypeError("currentstate must be a list of bools, if given"))
    elif len(currentstate) != len(options):
        UIErrorWrapper.raise_error(UIValueError("currentstate must be the same length as options, if given"))
    else:
        currentstate = copy.copy(currentstate)

    prompt += (
        "\nEnter the number or multiple numbers separated by a space to toggle,\n"
        "'a' or 'all' to toggle all, 'on' to set all on, 'off' to set all off,\n"
        "'r' to accept and return, or 'c' to cancel and return.\n"
        "Active options are marked with a *:"
    )

    print(prompt)
    while True:
        entries = []
        for i in range(len(options)):
            if currentstate[i]:
                state_str = "[*]"
            else:
                state_str = "[ ]"
            entries.append("{0}: {1} {2}".format(i + 1, options[i], state_str))

        if printcols:
            print_in_columns(entries, **printcolargs)
        else:
            print("\n".join(entries))

        user_ans = text_input("(Type 'm' to see initial message again) --> ")
        opt_inds = []
        bad_opts = []
        if user_ans.lower() == "m":
            print("")
            print(prompt)
            continue
        elif user_ans.lower() == "r":
            if returntype == "bools":
                return currentstate
            elif returntype == "opts":
                return [opt for i, opt in enumerate(options) if currentstate[i]]
            else:
                UIErrorWrapper.raise_error(
                    NotImplementedError('No return method implemented for returntype == "{}"'.format(returntype))
                )
        elif user_ans.lower() == "c":
            return None
        elif user_ans.lower() == "all" or user_ans.lower() == "a":
            opt_inds = range(len(options))
        elif user_ans.lower() == "on":
            opt_inds = [i for i in range(len(options)) if not currentstate[i]]
        elif user_ans.lower() == "off":
            opt_inds = [i for i in range(len(options)) if currentstate[i]]
        else:
            user_ans = re.split("\s+", user_ans)
            for u_part in user_ans:
                try:
                    u_list = [int(u) - 1 for u in u_part.split("-")]
                except ValueError as err:
                    bad_opts.append(u_part)
                else:
                    if len(u_list) == 1:
                        opt = u_list
                    else:
                        opt = [x for x in range(u_list[0], u_list[1] + 1)]

                    if all([o >= 0 and o < len(options) for o in opt]):
                        opt_inds += opt
                    else:
                        bad_opts.append(u_part)

        if feedback_level > 1 and len(bad_opts) > 0:
            print("Could not parse {0},\nout of range or not a number".format(", ".join(bad_opts)))

        for i in opt_inds:
            currentstate[i] = not currentstate[i]


def _optional_input(user_input_fxn, prompt, value, do_ask_fxn, input_valid_fxn, input_invalid_msg, *args, **kwargs):
    if do_ask_fxn(value):
        return user_input_fxn(prompt, *args, **kwargs)
    elif not input_valid_fxn(value):
        UIErrorWrapper.raise_error(UIValueError(input_invalid_msg.format(value=value)))
    else:
        return value


def _get_do_ask_fxn(ask_fxn):
    def _default_do_ask_fxn(value):
        return value is None

    if ask_fxn is None:
        return _default_do_ask_fxn
    else:
        return ask_fxn


def opt_user_input_list(prompt, value, options, do_ask_test=None, invalid_msg=None, error_on_none=True, **kwargs):

    do_ask_test = _get_do_ask_fxn(do_ask_test)

    input_valid_fxn = lambda value: value in options
    if invalid_msg is None:
        invalid_msg = "The value {{value}} is invalid. It must be one of: {opts}".format(opts=", ".join(options))
    else:
        invalid_msg = invalid_msg.format(value="{value}", opts=", ".join(options))

    response = _optional_input(
        user_input_list, prompt, value, do_ask_test, input_valid_fxn, invalid_msg, options, **kwargs
    )

    if response is None and error_on_none:
        UIErrorWrapper.raise_error(UIOptNoneError("The user failed to provide a value"))

    if "returntype" in kwargs and kwargs["returntype"] == "index" and response in options:
        response = options.index(response)

    return response


def opt_user_input_date(
    prompt, value, do_ask_test=None, is_valid_test=None, invalid_msg=None, error_on_none=True, **kwargs
):
    do_ask_test = _get_do_ask_fxn(do_ask_test)
    if is_valid_test is None:
        is_valid_test = lambda value: isinstance(value, (dt.date, dt.datetime))
    elif is_valid_test is not None and invalid_msg is None:
        UIErrorWrapper.raise_error(
            UIValueError(
                "If is_valid_test is given, invalid_msg should be to so that the error message matches the test"
            )
        )
    elif invalid_msg is None:
        invalid_msg = (
            "The given value must be an instance of datetime.date or datetime.datetime"
            if invalid_msg is None
            else invalid_msg
        )

    response = _optional_input(user_input_date, prompt, value, do_ask_test, is_valid_test, invalid_msg, **kwargs)
    if response is None and error_on_none:
        UIErrorWrapper.raise_error(UIOptNoneError("The user failed to provide a value"))

    return response


def opt_user_input_value(
    prompt, value, do_ask_test=None, is_valid_test=None, invalid_msg=None, error_on_none=True, **kwargs
):
    do_ask_test = _get_do_ask_fxn(do_ask_test)
    if is_valid_test is not None and invalid_msg is None:
        UIErrorWrapper.raise_error(UIValueError("If is_valid_test is given, invalid_msg must be as well"))
    elif is_valid_test is None:
        is_valid_test = lambda val: True

    response = _optional_input(
        user_input_value,
        prompt,
        value,
        do_ask_test,
        is_valid_test,
        invalid_msg,
        testfxn=is_valid_test,
        testmsg=invalid_msg,
        **kwargs,
    )
    if response is None and error_on_none:
        UIErrorWrapper.raise_error(UIOptNoneError("The user failed to provide a value"))

    return response


def opt_user_input_yn(prompt, value, do_ask_test=None, **kwargs):
    do_ask_test = _get_do_ask_fxn(do_ask_test)
    invalid_msg = "The given value must be a boolean"
    return _optional_input(
        user_input_yn, prompt, value, do_ask_test, lambda x: isinstance(x, bool), invalid_msg, **kwargs
    )


def opt_user_onoff_list(prompt, value, options, do_ask_test=None, returntype="opts", value_name="The value", **kwargs):
    do_ask_test = _get_do_ask_fxn(do_ask_test)

    def opt_valid_test(val):
        if not isinstance(val, (list, tuple)):
            return False
        else:
            return all([v in options for v in val])

    def bool_valid_test(val):
        if not isinstance(val, (list, tuple)):
            return False
        else:
            return all([isinstance(v, bool) for v in val]) and len(val) == len(options)

    if returntype == "opts":
        is_valid_test = opt_valid_test
        invalid_message = "{} must be a list or tuple containing a subset of the following: {}".format(
            value_name, ", ".join(options)
        )
    elif returntype == "bools":
        is_valid_test = bool_valid_test
        invalid_message = "{} must be a list or tuple of booleans the same length as options ({})".format(
            value_name, len(options)
        )
    else:
        UIErrorWrapper.raise_error(ValueError('returntype == "{}" is not permitted'.format(returntype)))

    return _optional_input(
        user_onoff_list, prompt, value, do_ask_test, is_valid_test, invalid_message, options, **kwargs
    )
