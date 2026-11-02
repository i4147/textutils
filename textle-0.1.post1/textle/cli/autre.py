import sys
import click


def bool_adapter(x):
    return True if x == "true" else False


def interpret_extra_options(extra_options):
    glob_opts = {}
    intern_opts = {}
    if len(extra_options) % 2 == 1:
        click.echo("Invalid number of extra options passed to new.", err=True)
        sys.exit(1)
    for opt, value in zip(extra_options[::2], extra_options[1::2]):
        if not opt.startswith("--") or ":" not in opt:
            click.echo("All extra options passed to new must be of the form --subsystem:value <some_value>", err=True)
            sys.exit(1)
        opt = opt[2:]
        subsystem, name, type_ = opt.split(":") if opt.count(":") == 2 else (opt.split(":") + [None])
        if type_ == None:
            if value in ("true", "false"):
                type_ = bool_adapter
            elif all(x in "0123456789" for x in value):
                type_ = int
            else:
                type_ = str
        elif type_ not in ("bool", "int", "str"):
            click.echo("Invalid argument type {}".format(type_))
        else:
            type_ = {"bool": bool_adapter, "int": int, "str": str}
        value = type_(value)
        d = glob_opts if str(subsystem) == "global" else intern_opts.get(subsystem, None)
        if d is None:
            intern_opts[subsystem] = {}
            d = intern_opts[subsystem]
        if name in d and type(d[name]) is (type_ if type_ is not bool_adapter else bool):
            d[name] = [d[name], value]
        elif name in d and type(d[name]) is list:
            d[name].append(value)
        else:
            d[name] = value
    return glob_opts, intern_opts
