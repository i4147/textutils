from typing import TypedDict

from .style import style

DEFAULT_SYNTAX_HIGHLIGHT_COLORS = {
    "key": "#e06c75",
    "arr": "#ffd700",
    "dict": "#ffd700",
    "str": "#98c379",
    "num": "#d19a58",
    "bool": "#d19a66",
}


class SyntaxHighlightingOptions(TypedDict):
    indent: int
    """Amount of spaces to indent."""
    curr_indent: int
    """Current indent level."""
    trailing_comma: bool
    """Whether to add a trailing comma to the last item in a list or dict."""
    pre_indent: bool
    """Whether to indent the first line of a list or dict."""
    colors: dict[str, str]
    """Colors to use for syntax highlighting."""


DEFAULT_SYNTAX_HIGHLIGHTING_OPTIONS: SyntaxHighlightingOptions = {
    "indent": 2,
    "curr_indent": 0,
    "trailing_comma": False,
    "pre_indent": True,
    "colors": DEFAULT_SYNTAX_HIGHLIGHT_COLORS,
}


def highlight(
    value: dict | list | str | float | bool | object,
    options: SyntaxHighlightingOptions | None = None,
) -> str:
    opts = _parse_options(options, DEFAULT_SYNTAX_HIGHLIGHTING_OPTIONS)

    if isinstance(value, dict):
        return pretty_dict(
            value,
            options=options,
        )
    if isinstance(value, list):
        return pretty_list(value, options=options)
    if isinstance(value, str):
        return style(repr(value), fg=opts["colors"]["str"])
    if isinstance(value, (int, float)):
        return style(repr(value), fg=opts["colors"]["num"])
    if isinstance(value, bool):
        return style(repr(value), fg=opts["colors"]["bool"])

    if not hasattr(value, "__dict__"):
        msg = (
            f"Unsupported type for syntax highlighting: {type(value).__name__}. "
            "Expected dict, list, str, int, float, bool, or an object with a __dict__ attribute."
        )
        raise TypeError(msg)

    return highlight(value.__dict__, options=options)


def pretty_dict(
    dictionary: dict,
    options: SyntaxHighlightingOptions | None = None,
) -> str:
    opts = _parse_options(options, DEFAULT_SYNTAX_HIGHLIGHTING_OPTIONS)

    lcub = style("{", fg=opts["colors"]["dict"])
    rcub = style("}", fg=opts["colors"]["dict"])

    pre_identation = " " * opts["curr_indent"] if opts["pre_indent"] else ""
    output_str = f"{pre_identation}{lcub}\n"

    for i, (key, val) in enumerate(dictionary.items()):
        pretty_key = style(repr(key), fg=opts["colors"]["key"])
        pretty_value = highlight(
            val,
            {
                "indent": opts["indent"],
                "curr_indent": opts["indent"] + opts["curr_indent"],
                "pre_indent": False,
                "trailing_comma": opts["trailing_comma"],
                "colors": opts["colors"],
            },
        )

        comma = "," if (i < len(dictionary) - 1) else ""
        output_str += f"{' ' * (opts['curr_indent'] + opts['indent'])}{pretty_key}: {pretty_value}{comma}\n"

    newline = "\n"
    output_str += f"{' ' * opts['curr_indent']}{rcub}{',' + newline if opts['trailing_comma'] else ''}"
    return output_str


def pretty_list(
    lst: list,
    options: SyntaxHighlightingOptions | None = None,
) -> str:
    opts = _parse_options(options, DEFAULT_SYNTAX_HIGHLIGHTING_OPTIONS)

    lsqb = style("[", fg=opts["colors"]["arr"])
    rsqb = style("]", fg=opts["colors"]["arr"])

    pre_identation = " " * opts["curr_indent"] if opts["pre_indent"] else ""
    output_str = f"{pre_identation}{lsqb}\n"

    for i, val in enumerate(lst):
        pretty_value = highlight(
            val,
            {
                "indent": opts["indent"],
                "curr_indent": opts["indent"] + opts["curr_indent"],
                "pre_indent": False,
                "trailing_comma": opts["trailing_comma"],
                "colors": opts["colors"],
            },
        )
        comma = "," if (i < len(lst) - 1) else ""
        output_str += f"{' ' * (opts['curr_indent'] + opts['indent'])}{pretty_value}{comma}\n"

    newline = "\n"
    output_str += f"{' ' * opts['curr_indent']}{rsqb}{',' + newline if opts['trailing_comma'] else ''}"
    return output_str


def _parse_options(
    options: SyntaxHighlightingOptions | None, defaults: SyntaxHighlightingOptions
) -> SyntaxHighlightingOptions:
    if options is None:
        return defaults

    for key in ("indent", "curr_indent", "trailing_comma", "pre_indent", "colors"):
        if key not in options:
            options[key] = defaults[key]

    return options
