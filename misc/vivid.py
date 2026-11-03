import logging
from time import sleep
from rich.console import Console


class VividText:
    def __init__(
        self,
        color="White",
        bold=False,
        dim=False,
        italic=False,
        underline=False,
        reverse=False,
        strikethrough=False,
        sleep=0.05,
        log_saves=False,
        log_path="vividtext.log",
    ):
        self.console = Console()
        self.style_options = {
            "color": color.lower(),
            "bold": bold,
            "dim": dim,
            "italic": italic,
            "underline": underline,
            "reverse": reverse,
            "strike": strikethrough,
        }
        self.sleep = min(sleep, 1)
        self.log_saves = log_saves
        self.log_path = log_path
        self.logger = None
        if self.log_saves:
            self.__setup_logger()

    def toggle_logging(self, enable=None, log_path=None):
        if enable is None:
            enable = not self.log_saves
        if enable and not self.log_saves:
            self.log_saves = True
            if log_path:
                self.log_path = log_path
            self.__setup_logger()
            if self.logger:
                self.logger.info("Logging enabled.")
        elif not enable and self.log_saves:
            self.log_saves = False
            if self.logger:
                self.logger.info("Logging disabled.")
                handlers = self.logger.handlers[:]
                for handler in handlers:
                    handler.close()
                    self.logger.removeHandler(handler)
                self.logger = None

    def reset_style(
        self,
        color="White",
        bold=False,
        dim=False,
        italic=False,
        underline=False,
        reverse=False,
        strikethrough=False,
        sleep=0.05,
    ):
        self.style_options = {
            "color": color.lower(),
            "bold": bold,
            "dim": dim,
            "italic": italic,
            "underline": underline,
            "reverse": reverse,
            "strike": strikethrough,
        }
        self.sleep = min(sleep, 1)
        if self.logger:
            self.logger.info(f"Changed style to: {self.style_options}, Speed: {self.sleep}")

    def __build_style(self):
        style_parts = []
        if self.style_options["color"]:
            style_parts.append(self.style_options["color"])
        for attr in ["bold", "dim", "italic", "underline", "reverse", "strike"]:
            if self.style_options[attr]:
                style_parts.append(attr)
        return " ".join(style_parts)

    def __setup_logger(self):
        self.logger = logging.getLogger("VividTextLogger")
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_path)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        self.logger.addHandler(fh)

    def typewriter(self, msg: str, end: str = "\n", input: bool = False):
        style = self.__build_style()
        if input:
            for i, c in enumerate(msg, 1):
                self.console.print(f"[{style}]{c}[/]", end="", soft_wrap=True)
                sleep(self.sleep)
            if end:
                for c in end:
                    self.console.print(f"[{style}]{c}[/]")
                    sleep(self.sleep)
        elif self.sleep != 0:
            for i, c in enumerate(msg, 1):
                self.console.print(f"[{style}]{c}[/]", end=end if i == len(msg) else "", soft_wrap=True)
                sleep(self.sleep)
        else:
            self.console.print(f"[{style}]{msg}[/]")

    def menuTypewriter(self, split: str, *words: str | list):
        if len(words) == 1 and isinstance(words[0], list):
            worded = words[0]
        else:
            worded = list(words)
        formatted = f"{split}".join(worded)
        self.typewriter(formatted)

    def inputTypewriter(self, msg: str, end: str = " > "):
        self.typewriter(msg, end=end, input=True)
        return input()

    def help(self):
        self.console.print("\n[bold underline bright_black]Rich Color Options:[/]\n")
        self.console.print("[bold bright_yellow]Named Colors:[/]")
        self.console.print(
            "red, green, blue, yellow, magenta, cyan, white, and black. You can add bright_[color] for the same colors to make them brighter."
        )
        self.console.print("\n[bold bright_yellow]Hex Colors:[/]")
        self.console.print("[#ff69b4]#ff69b4[/], [#00ffff]#00ffff[/], [#ffaa00]#ffaa00[/], any hex color will work")
        self.console.print("\n[bold bright_yellow]Palette Colors:[/]")
        self.console.print("Use 'color(0)' to 'color(255)'. For example: [color(201)]color(201)[/] is hot pink.")
        self.console.print("\n[bold bright_yellow]Attributes:[/]")
        self.console.print("bold, dim, italic, underline, reverse, strike, sleep time")
