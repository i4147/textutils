__version__ = "1.0.1"
import sys
import os
import re
from contextlib import contextmanager

COLORS = {
    "black": 30,
    "red": 31,
    "green": 32,
    "yellow": 33,
    "blue": 34,
    "magenta": 35,
    "cyan": 36,
    "white": 37,
    "bright_black": 90,
    "bright_red": 91,
    "bright_green": 92,
    "bright_yellow": 93,
    "bright_blue": 94,
    "bright_magenta": 95,
    "bright_cyan": 96,
    "bright_white": 97,
}
BG_COLORS = {
    "bg_black": 40,
    "bg_red": 41,
    "bg_green": 42,
    "bg_yellow": 43,
    "bg_blue": 44,
    "bg_magenta": 45,
    "bg_cyan": 46,
    "bg_white": 47,
    "bg_bright_black": 100,
    "bg_bright_red": 101,
    "bg_bright_green": 102,
    "bg_bright_yellow": 103,
    "bg_bright_blue": 104,
    "bg_bright_magenta": 105,
    "bg_bright_cyan": 106,
    "bg_bright_white": 107,
}
LOOKS = {
    "bold": 1,
    "dim": 2,
    "italic": 3,
    "underline": 4,
    "blink": 5,
    "reverse": 7,
    "hidden": 8,
    "strikethrough": 9,
}


class _Config:
    enabled = True


_custom_styles = {}
_predefined_styles = {}
_current_theme = {}


def _init_predefined_styles():
    for color_name in COLORS.keys():
        _predefined_styles[color_name] = {"color": color_name, "bg": None, "look": None}
    for bg_name in BG_COLORS.keys():
        _predefined_styles[bg_name] = {"color": None, "bg": bg_name, "look": None}
    for look_name in LOOKS.keys():
        _predefined_styles[look_name] = {"color": None, "bg": None, "look": look_name}


def _init_windows():
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            mode.value |= 0x0004
            kernel32.SetConsoleMode(handle, mode)
        except Exception:
            pass


def _init_config():
    if os.getenv("NO_COLOR"):
        _Config.enabled = False
        return
    if os.getenv("FORCE_COLOR"):
        _Config.enabled = True
        _init_windows()
        return
    if hasattr(sys.stdout, "isatty") and not sys.stdout.isatty():
        _Config.enabled = False
        return
    _init_windows()
    _Config.enabled = True


_init_config()
_init_predefined_styles()


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_ansi(r, g, b, background=False):
    prefix = 48 if background else 38
    return f"{prefix};2;{r};{g};{b}"


def _parse_color(color, background=False):
    if not color:
        return None
    color_dict = BG_COLORS if background else COLORS
    color_key = f"bg_{color}" if background and not color.startswith("bg_") else color
    if color_key in color_dict:
        return str(color_dict[color_key])
    if color in color_dict:
        return str(color_dict[color])
    if isinstance(color, str) and color.startswith("#"):
        r, g, b = _hex_to_rgb(color)
        return _rgb_to_ansi(r, g, b, background)
    if isinstance(color, (tuple, list)) and len(color) == 3:
        return _rgb_to_ansi(*color, background)
    return None


def enable():
    _Config.enabled = True


def disable():
    _Config.enabled = False


def style(text, color=None, bg=None, look=None):
    if not _Config.enabled:
        return text
    codes = []
    fg_code = _parse_color(color, background=False)
    if fg_code:
        codes.append(fg_code)
    bg_code = _parse_color(bg, background=True)
    if bg_code:
        codes.append(bg_code)
    if look:
        if isinstance(look, str) and look in LOOKS:
            codes.append(str(LOOKS[look]))
        elif isinstance(look, (list, tuple)):
            for l in look:
                if l in LOOKS:
                    codes.append(str(LOOKS[l]))
    if not codes:
        return text
    return f"\033[{';'.join(codes)}m{text}\033[0m"


def create(name, color=None, bg=None, look=None):
    if not name:
        raise ValueError("Style name cannot be empty")
    if not color and not bg and not look:
        raise ValueError("Must specify at least color, bg, or look")
    _custom_styles[name] = {"color": color, "bg": bg, "look": look}


def delete(name):
    if name in _custom_styles:
        del _custom_styles[name]
        return True
    return False


def strip(text):
    return re.sub(r"</?[\w_#-]+>", "", text)


def clean(text):
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text)


def length(text):
    return len(clean(text))


def set_theme(theme):
    global _current_theme
    if isinstance(theme, str):
        if theme == "dark":
            theme = {
                "error": {"color": "bright_red", "look": "bold"},
                "success": {"color": "bright_green", "look": "bold"},
                "warning": {"color": "bright_yellow", "look": "bold"},
                "info": {"color": "bright_cyan"},
                "debug": {"color": "bright_black"},
                "critical": {"color": "white", "bg": "red", "look": "bold"},
            }
        elif theme == "light":
            theme = {
                "error": {"color": "red", "look": "bold"},
                "success": {"color": "green", "look": "bold"},
                "warning": {"color": "yellow", "look": "bold"},
                "info": {"color": "blue"},
                "debug": {"color": "magenta"},
                "critical": {"color": "white", "bg": "red", "look": "bold"},
            }
        else:
            raise ValueError(f"Unknown theme: {theme}")
    _current_theme = theme
    for name, style_def in theme.items():
        create(name, **style_def)


@contextmanager
def temporary(name, color=None, bg=None, look=None):
    create(name, color=color, bg=bg, look=look)
    try:
        yield
    finally:
        delete(name)


def format(text):
    if not _Config.enabled:
        return strip(text)
    all_styles = {**_predefined_styles, **_current_theme, **_custom_styles}
    tag_pattern = r"<([\w_#-]+)>(.*?)</\1>"

    def replace_tag(match):
        tag_name = match.group(1)
        content = match.group(2)
        if tag_name.startswith("#"):
            return style(content, color=tag_name)
        if tag_name in all_styles:
            style_def = all_styles[tag_name]
            return style(content, color=style_def.get("color"), bg=style_def.get("bg"), look=style_def.get("look"))
        return match.group(0)

    prev_text = None
    while prev_text != text:
        prev_text = text
        text = re.sub(tag_pattern, replace_tag, text)
    return text


def __getattr__(name):
    if name in _custom_styles:
        s = _custom_styles[name]
        return lambda text: style(text, color=s.get("color"), bg=s.get("bg"), look=s.get("look"))
    raise AttributeError(f"module 'textstyle' has no attribute '{name}'")


__all__ = [
    "style",
    "format",
    "create",
    "delete",
    "strip",
    "clean",
    "length",
    "enable",
    "disable",
    "set_theme",
    "temporary",
    "COLORS",
    "BG_COLORS",
    "LOOKS",
]
if __name__ == "__main__":
    print("=== Basic Style Function ===")
    print(style("Error", color="red", look="bold"))
    print(style("Success", color="green", bg="black", look="bold"))
    print(style("Warning", color="yellow", bg="blue"))
    print("\n=== Hex Colors ===")
    print(style("Hex Red", color="#FF0000"))
    print(style("Hex Green", color="#00FF00"))
    print(style("Custom Orange", color="#FF5733", look="bold"))
    print("\n=== RGB Colors ===")
    print(style("RGB Red", color=(255, 0, 0)))
    print(style("RGB Purple", color=(128, 0, 128), look="italic"))
    print("\n=== Background Colors ===")
    print(style("Alert", color="white", bg="red", look="bold"))
    print(style("Success", color="black", bg="green", look="bold"))
    print(style("Hex BG", color="white", bg="#FF5733"))
    print("\n=== Predefined Tags with Backgrounds ===")
    print(format("Normal <bg_red><white>Alert!</white></bg_red> text"))
    print(format("<bg_green><black>Success</black></bg_green>"))
    print("\n=== Hex Color Tags ===")
    print(format("This is <#FF5733>hex color</#FF5733> text"))
    print(format("<#00FF00>Green</#00FF00> and <#FF0000>Red</#FF0000>"))
    print("\n=== Custom Styles with Backgrounds ===")
    create("alert", color="white", bg="red", look="bold")
    create("ok", color="black", bg="green", look="bold")
    create("highlight", color="#FFFF00", bg="#000000", look="bold")
    print(format("<alert>ALERT!</alert> System critical"))
    print(format("<ok>OK</ok> All systems operational"))
    print(format("Please <highlight>note this</highlight> carefully"))
    print("\n=== Strip and Clean Functions ===")
    markup_text = "<red>Hello</red> <bold>World</bold>"
    print(f"Original: {markup_text}")
    print(f"Stripped: {strip(markup_text)}")
    styled_text = style("Hello World", color="red", look="bold")
    print(f"Styled length (with ANSI): {len(styled_text)}")
    print(f"Visible length: {length(styled_text)}")
    print(f"Cleaned: '{clean(styled_text)}'")
    print("\n=== Theme System (Dark) ===")
    set_theme("dark")
    print(format("<error>Error:</error> Connection failed"))
    print(format("<success>Success:</success> Connected to server"))
    print(format("<warning>Warning:</warning> Low disk space"))
    print(format("<info>Info:</info> Processing data"))
    print(format("<critical>CRITICAL</critical> System failure"))
    print("\n=== Theme System (Light) ===")
    set_theme("light")
    print(format("<error>Error:</error> Connection failed"))
    print(format("<success>Success:</success> Connected"))
    print("\n=== Custom Theme ===")
    set_theme({
        "primary": {"color": "#007AFF", "look": "bold"},
        "danger": {"color": "white", "bg": "#FF3B30", "look": "bold"},
        "muted": {"color": "bright_black"},
    })
    print(format("<primary>Primary action</primary>"))
    print(format("<danger>Danger zone</danger>"))
    print(format("<muted>Less important info</muted>"))
    print("\n=== Temporary Styles ===")
    with temporary("temp", color="magenta", look="italic"):
        print(format("<temp>This is temporary</temp>"))
    print(format("<temp>This will be plain text</temp>"))
    print("\n=== Complex Example ===")
    set_theme("dark")
    print(
        format("""
<critical>SYSTEM ERROR</critical>
<error>Failed to connect to database</error>
  <info>Host:</info> <#00FFFF>db.example.com</#00FFFF>
  <info>Port:</info> 5432
  <warning>Retrying in 5 seconds...</warning>
<success>Connection restored</success>
""")
    )
