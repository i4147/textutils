import os

from .ansi import ESC, RESET, Bg, Fg, Frmt, bg_hex, bg_rgb, fg_hex, fg_rgb


def style(
    text: str,
    fg: Fg | str | tuple[int, int, int] = Fg.DEFAULT,
    bg: Bg | str | tuple[int, int, int] = Bg.DEFAULT,
    frmt: list[Frmt] | None = None,
    *,
    force_color: bool = False,
) -> str:
    no_color = os.environ.get("NO_COLOR", "0") in ("1", "true")
    if no_color and not force_color:
        return text

    if isinstance(fg, str):
        fore = fg_hex(fg)
    if isinstance(fg, tuple):
        fore = fg_rgb(fg)
    if isinstance(fg, Fg):
        fore = f"{fg.value}"

    if isinstance(bg, str):
        back = bg_hex(bg)
    if isinstance(bg, tuple):
        back = bg_rgb(bg)
    if isinstance(bg, Bg):
        back = f"{bg.value}"

    if frmt is None:
        frmt = []
    else:
        frmt.sort()

    frmt_string = ""
    for f in frmt:
        frmt_string += f";{f.value}"

    return f"{ESC}{fore};{back}{frmt_string}m{text}{RESET}"
