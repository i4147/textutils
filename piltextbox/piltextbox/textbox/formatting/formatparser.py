class FWord:
    def __init__(self, txt, bold=False, ital=False, xspace=True, is_indent=False):
        self.txt = txt
        self.bold = bold
        self.ital = ital
        self.xspace = xspace
        self.is_indent = is_indent

    @staticmethod
    def _examine_fwords(fwords: list, fonts: dict, existing_dict=None):

        from PIL import Image, ImageDraw

        dr = ImageDraw.Draw(Image.new("RGBA", (1, 1)), "RGBA")

        if existing_dict is None:
            space_w, _ = dr.textsize(" ", font=fonts["main"])
            existing_dict = {
                "word_px_dict": {},
                "font_dict": {},
                "total_word_w": 0,
                "total_word_h": 0,
                "space_w": space_w,
            }

        for fword in fwords:
            styling = f"{'bold' * fword.bold}{'ital' * fword.ital}"
            if styling == "":
                styling = "main"

            font = fonts.get(styling, fonts["main"])

            word_w, word_h = dr.textsize(fword.txt, font=font)
            existing_dict["word_px_dict"][fword] = (word_w, word_h)
            existing_dict["font_dict"][fword] = font
            existing_dict["total_word_w"] += word_w
            if word_h > existing_dict["total_word_h"]:
                existing_dict["total_word_h"] = word_h

        return existing_dict

    @staticmethod
    def recompile_fwords(fwords: list, exclude_indent=False):
        fl = FLine(fwords=fwords)
        return fl.simplify(exclude_indent=exclude_indent)


class FLine:
    def __init__(self, fwords: list, justifiable=False, fword_info=None):
        self.fwords = fwords
        self.justifiable = justifiable
        self.staged = None
        self.fword_info = fword_info

    def _extract_fword_info(self, fword_info: dict, use_staged=True):
        target = self.staged
        if not use_staged or self.staged is None:
            target = self.fwords

        line_word_w = 0
        line_word_h = 0
        line_w = 0
        total_spaces = 0
        space_w = fword_info["space_w"]

        i = len(target)
        for fw in target:
            line_word_w += fword_info["word_px_dict"][fw][0]
            line_w += fword_info["word_px_dict"][fw][0]
            if fword_info["word_px_dict"][fw][1] > line_word_h:
                line_word_h = fword_info["word_px_dict"][fw][1]

            if i != 1 and fw.xspace:
                line_w += space_w
                total_spaces += 1
            i -= 1
        return {
            "line_word_w": line_word_w,
            "line_word_h": line_word_h,
            "line_w": line_w,
            "space_w": space_w,
            "total_spaces": total_spaces,
        }

    def simplify(self, exclude_indent=False):
        c_txt = ""
        if self.fwords is None:
            return None
        if len(self.fwords) == 0:
            return c_txt
        for i in range(len(self.fwords)):
            sp = ""
            if exclude_indent and self.fwords[i].is_indent:
                continue
            if i != len(self.fwords) - 1:
                sp = self.fwords[i].xspace * " "
            c_txt = f"{c_txt}{self.fwords[i].txt}{sp}"
        return c_txt

    def to_pline(self, exclude_indent=False):
        txt = self.simplify(exclude_indent=exclude_indent)
        return PLine(txt=txt, justifiable=self.justifiable)

    def _stage(self, indent=None):
        self.staged = self.fwords.copy()
        if isinstance(indent, str):
            indent = FWord(txt=indent, bold=False, ital=False, xspace=False)
            self.staged.insert(0, indent)
        return self.staged

    def _unstage(self):
        self.staged = None


class PLine:
    def __init__(self, txt, justifiable=False):
        self.txt = txt
        self.justifiable = justifiable
        self.staged = None

    def simplify(self, exclude_indent=False):
        if exclude_indent:
            return self.txt.lstrip(" ")
        return self.txt

    def to_fline(self, exclude_indent=False):
        txt = self.simplify(exclude_indent=exclude_indent)
        return FLine(fwords=flat_parse(txt), justifiable=self.justifiable)

    def _stage(self, indent=None):
        self.staged = self.txt
        if isinstance(indent, str):
            self.staged = indent + self.staged
        return self.staged

    def _unstage(self):
        self.staged = None


class UnwrittenLines:
    def __init__(self, lines=None, formatting=None):
        if lines is None:
            lines = []
        self.lines = lines

        self.staged = None

        if formatting is None:
            if not isinstance(lines, list):
                pass
            elif len(lines) == 0:
                pass
            elif isinstance(lines[0], PLine):
                formatting = False
            elif isinstance(lines[0], FLine):
                formatting = True
        self.formatting = formatting

        self.fword_info = {}

    def simplify(self, exclude_indent=False):
        simplified_lines = []
        for obj in self.lines:
            simplified_lines.append(obj.simplify(exclude_indent=exclude_indent))
        return simplified_lines

    def print(self):
        simple_lines = self.simplify()
        for line in simple_lines:
            print(line)

    @property
    def remaining(self):
        if self.lines is None:
            return None
        return len(self.lines)

    def _stage_next_line(self):
        if self.remaining in [0, None]:
            return None
        self.staged = self.lines[0]
        return self.staged

    def _successful_write(self):
        self.staged = None
        self.lines.pop(0)

    def _unstage(self):
        self.staged = None


def parse_into_line(text: str, formatting: bool, justifiable=True, discard_formatting=False):
    fwords = all_parse(text, formatting, discard_formatting)
    return compile_line(fwords, formatting, justifiable)


def compile_line(fwords: list, formatting: bool, justifiable=True):
    fline_version = FLine(fwords, justifiable)
    if formatting:
        return fline_version
    else:
        return fline_version.to_pline()


def all_parse(text: str, formatting: bool, discard_formatting=False):
    if formatting:
        return format_parse(text, discard_formatting=discard_formatting)
    else:
        return flat_parse(text)


def flat_parse(text) -> list:
    text = text.strip("\r\n")
    text = text.replace("\r", "\n")
    text = text.replace("\n", " ")

    raw_words = text.split(" ")
    fwords = []
    for word in raw_words:
        fwords.append(FWord(word, bold=False, ital=False))

    return fwords


def format_parse_deep(text, discard_formatting=False, start_bold=False, start_ital=False):

    format_codes = ("<b>", "</b>", "<i>", "</i>")

    bold = start_bold
    ital = start_ital

    text = text.strip("\r\n")
    text = text.replace("\r", "\n")
    text = text.replace("\n", " ")

    raw_words = text.split(" ")
    fwords = []
    for word in raw_words:
        txt = word

        while True:
            if not txt.startswith(format_codes):
                break
            if txt.startswith("<b>"):
                bold = True
                txt = txt[len("<b>") :]
            if txt.startswith("</b>"):
                bold = False
                txt = txt[len("</b>") :]
            if txt.startswith("<i>"):
                ital = True
                txt = txt[len("<i>") :]
            if txt.startswith("</i>"):
                ital = False
                txt = txt[len("</i>") :]

        all_bold = []
        all_ital = []

        while True:
            if not txt.endswith(format_codes):
                break
            if txt.endswith("<b>"):
                all_bold.append(True)
                txt = txt[: -len("<b>")]
            if txt.endswith("</b>"):
                all_bold.append(False)
                txt = txt[: -len("</b>")]
            if txt.endswith("<i>"):
                all_ital.append(True)
                txt = txt[: -len("<i>")]
            if txt.endswith("</i>"):
                all_ital.append(False)
                txt = txt[: -len("</i>")]

        if len(txt) > 0:
            if discard_formatting:
                fwords.append(FWord(txt, bold=False, ital=False))
            else:
                fwords.append(FWord(txt, bold=bold, ital=ital))

        all_bold.append(bold)
        all_ital.append(ital)

        bold = all_bold[0]
        ital = all_ital[0]

    return fwords, bold, ital


def format_parse(text, discard_formatting=False) -> list:
    fwords, _, __ = format_parse_deep(text, discard_formatting)

    return fwords
