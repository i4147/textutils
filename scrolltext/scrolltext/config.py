from pathlib import Path
import configparser
import sys


IS_WINDOWS = sys.platform in ["msys", "win32", "nt"]
DEF_SCROLL_TEXT = """\
Hello, this is a  classic side scrolling text. You can override it by setting the \
environment variable 'SCROLL_TEXT'. It is supposed to be a simple example."""
SCROLL_SPEEDS = [0.25, 0.20, 0.18, 0.15, 0.125, 0.1, 0.09, 0.08, 0.075, 0.07, 0.0675]


initial_config = {
    "main": {"action": "linescroller", "color": 0, "endless": "0"},
    "cursestext": {"box": "1"},
    "scrolltext.text 1": {
        "direction": "0",
        "text": DEF_SCROLL_TEXT,
        "line": "0",
        "speed": "0",
    },
}


def get_speedsec_float(speed_index):
    if speed_index < 0 or speed_index >= len(SCROLL_SPEEDS):
        speed_index = 4
    scrollspeedsec = SCROLL_SPEEDS[speed_index]
    return scrollspeedsec


def init_config(write_config):
    if not IS_WINDOWS:
        config_path = Path("~/.config/scrolltextrc").expanduser()
    else:
        config_path = Path("scrolltextrc")

    cfg, really_write = _read_config(config_path)
    if write_config and really_write:
        _write_config(cfg, config_path)
    return cfg


def _read_config(config_path):
    really_write = False
    cfg = configparser.ConfigParser(default_section="main")
    read_config_files = cfg.read(config_path)

    if not read_config_files:
        really_write = True
        cfg.update(initial_config)
    _validate(cfg)
    return cfg, really_write


def _write_config(cfg, config_path):
    with open(config_path, "w", encoding="utf-8") as newfile:
        cfg.write(newfile)


def _validate(cfg):
    for section, entries in initial_config.items():
        if "%d" in section:
            section = section.replace("%d", "1")
        if section not in cfg:
            raise NameError("Section '" + section + "' is missing in config")
        _validate_section_entries(cfg, section, entries)

    # for index in range(2, 9):
    #     scrolltext_section = "scrolltext.text " + str(index)
    #     if not scrolltext_section in cfg:
    #         cfg["main"]["max_index"] = str(index - 1)
    #         break
    _fix_scrolltext_section(cfg, "scrolltext.text 1")
    if "cursestext" not in cfg:
        cfg["cursestext"] = {"box": "1"}


def _validate_section_entries(cfg, section, entries):
    for entry in entries:
        if entry not in cfg[section]:
            raise NameError("Entry '" + entry + "' is missing in Section '" + section + "'")


def _fix_scrolltext_section(cfg, section_name):
    text_lines = cfg[section_name]["text"]
    text = "".join(text_lines.split("\n"))
    cfg[section_name]["text"] = text
