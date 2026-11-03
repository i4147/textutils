import re
import unicodedata
import shutil


class Error(Exception):
    pass


class SyntextError(Error):
    pass


class LineStream:
    def __init__(self, text=None):
        if isinstance(text, str):
            self.lines = [line.rstrip() for line in text.splitlines()]
        else:
            self.lines = text or []
        self.index = 0

    def __str__(self):
        return "\n".join(self.lines[self.index :])

    def __len__(self):
        return len(self.lines)

    def append(self, line):
        self.lines.append(line)
        return self

    def prepend(self, line):
        self.lines.insert(0, line)

    def dedent(self):
        def countspaces(line):
            for index, char in enumerate(line):
                if char != " ":
                    return index

        mindent = min((countspaces(l) for l in self.lines if l), default=0)
        for index, line in enumerate(self.lines):
            if line:
                self.lines[index] = line[mindent:]
        return self

    def indent(self, n=4):
        for index, line in enumerate(self.lines):
            if line:
                self.lines[index] = " " * n + line
        return self

    def trim(self):
        while self.lines and self.lines[0] == "":
            self.lines.pop(0)
        while self.lines and self.lines[-1] == "":
            self.lines.pop()
        return self

    def peek(self):
        return self.lines[self.index]

    def next(self):
        self.index += 1
        return self.lines[self.index - 1]

    def rewind(self, n):
        self.index -= n

    def has_next(self):
        return self.index < len(self.lines)

    def has_trailing_blank(self):
        if self.lines and self.lines[-1] == "":
            return True
        return False

    def contains_blank(self):
        for line in self.lines:
            if line == "":
                return True
        return False


class ArgParser:
    args_regex = re.compile(
        r"""
        (?:([^\s'"=]+)=)?           # an optional key, followed by...
        (
            "((?:[^\\"]|\\.)*)"     # a double-quoted value, or
            |
            '((?:[^\\']|\\.)*)'     # a single-quoted value
        )
        |
        ([^\s'"=]+)=(\S+)           # a key followed by an unquoted value
        |
        (\S+)                       # an unkeyed, unquoted value
    """,
        re.VERBOSE,
    )

    def parse(self, argstr):
        pargs, kwargs, classes = [], {}, []
        for match in self.args_regex.finditer(argstr):
            if match.group(2) or match.group(5):
                key = match.group(1) or match.group(5)
                value = match.group(3) or match.group(4) or match.group(6)
                if match.group(3) or match.group(4):
                    value = bytes(value, "utf-8").decode("unicode_escape")
                if key:
                    kwargs[key] = value
                else:
                    pargs.append(value)
            else:
                pargs.append(match.group(7))
        for arg in pargs[:]:
            if arg.startswith("."):
                classes.append(arg[1:])
                pargs.remove(arg)
            if arg.startswith("#"):
                kwargs["id"] = arg[1:]
                pargs.remove(arg)
            if arg.startswith("&"):
                kwargs[arg.lstrip("&")] = None
                pargs.remove(arg)
        if "class" in kwargs:
            classes.extend(kwargs["class"].split())
        if classes:
            kwargs["class"] = " ".join(sorted(classes))
        return pargs, kwargs


def title(text):
    cols, _ = shutil.get_terminal_size()
    line = "\u001b[90m" + "─" * cols + "\u001b[0m"
    return line + "\n" + text.center(cols) + "\n" + line


def strip_tags(text):
    return re.sub(r"<[^>]*>", "", text)


def idify(s):
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    s = s.lower()
    s = s.replace("'", "")
    s = re.sub(r"&[#a-zA-Z0-9]+;", "-", s)
    s = re.sub(r"[^a-z0-9-]+", "-", s)
    s = re.sub(r"--+", "-", s).strip("-")
    s = re.sub(r"^(\d)", r"id-\1", s)
    return s or "id"
