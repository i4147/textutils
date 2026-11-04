from math import floor
import re
from os import get_terminal_size
from .boxes import boxes
from .colors import colors

NL = "\n"
WS = " "


def panel(
    text: str,
    border_style: any = "round",
    padding: int = 0,
    margin: int = 0,
    width: int = 0,
    expand: bool = False,
    border_color: str = "reset",
    text_alignment: str = "left",
    text_color: str = "reset",
    title: str = None,
    title_alignment: str = "center",
) -> str:
    if type(border_style) is dict:
        boxes["custom"] = border_style
        border_style = "custom"
    chars = boxes.get(border_style, boxes["single"])
    lines = _get_lines(text)
    max_line_len = max(map(lambda l: len(_ansi_escape(l)), lines + [title] if title else lines))
    term_cols, term_lines = get_terminal_size()

    if expand or width - 4 > term_cols:
        max_line_len = term_cols - 4
    elif width - 4 > max_line_len:
        max_line_len = width - 4
    margin_h, margin_v = margin * 3, margin
    if max_line_len == term_cols - 4:
        margin_h, margin_v = 0, 0

    vertical_margin = NL * margin_v
    horizontal_margin = WS * margin_h

    if title:
        len_title = len(_ansi_escape(title))
        if title_alignment == "left":
            top_line = (
                chars["top"] * (1 - len(WS))
                + WS
                + title
                + WS
                + chars["top"] * (max_line_len - len_title - len(WS) * 2 + 2)
            )
        elif title_alignment == "right":
            top_line = (
                chars["top"] * (max_line_len - len_title - len(WS) * 2 + 2)
                + WS
                + title
                + WS
                + chars["top"] * (1 - len(WS))
            )
        elif title_alignment == "center":
            max_chars = max_line_len + 1 * 2
            half_chars = floor((max_chars - len_title - len(WS) * 2) / 2)
            top_line = (
                chars["top"] * half_chars
                + WS
                + title
                + WS
                + chars["top"] * (max_chars - half_chars - len(WS) * 2 - len_title)
            )
    else:
        top_line = chars["top"] * (max_line_len + 1 * 2)

    top_bar = (
        colors[border_color] + horizontal_margin + chars["topLeft"] + top_line + chars["topRight"] + colors["reset"]
    )
    bottom_line = chars["bottom"] * (max_line_len + 1 * 2)
    bottom_bar = (
        colors[border_color]
        + horizontal_margin
        + chars["bottomLeft"]
        + bottom_line
        + chars["bottomRight"]
        + colors["reset"]
    )

    left = colors[border_color] + horizontal_margin + chars["left"] + WS + colors["reset"]
    right = colors[border_color] + WS + chars["right"] + colors["reset"]

    blank_line = NL + left + WS * max_line_len + right
    vertical_padding = blank_line * padding

    top = vertical_margin + top_bar + vertical_padding
    middle = ""
    for line in lines:
        line_length = len(_ansi_escape(line))
        fill = max_line_len - line_length
        if text_alignment == "left":
            fill = WS * fill
            middle += NL + left + colors[text_color] + line + fill + right
        elif text_alignment == "right":
            fill = WS * fill
            middle += NL + left + fill + line + right
        elif text_alignment == "center":
            left_fill = WS * floor(fill / 2)
            right_fill = WS * (fill - len(left_fill))
            middle += NL + left + left_fill + colors[text_color] + line + right_fill + right

    bottom = vertical_padding + NL + bottom_bar + vertical_margin

    return top + middle + bottom


def _ansi_escape(text: str) -> str:
    regex = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return regex.sub("", text)


def _get_lines(text: str) -> list:
    lines = text.splitlines()
    for line in range(len(lines)):
        lines[line] = lines[line].strip()
    return lines
