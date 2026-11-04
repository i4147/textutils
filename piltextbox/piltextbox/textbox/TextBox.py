from PIL import Image, ImageDraw, ImageFont
from .formatting import FWord, FLine, PLine, UnwrittenLines
from .formatting import format_parse_deep, all_parse, parse_into_line


class TextBox:
    def __init__(
        self,
        size: tuple,
        typeface=None,
        font_size=12,
        bg_RGBA=(255, 255, 255, 255),
        font_RGBA=(0, 0, 0, 255),
        paragraph_indent=0,
        new_line_indent=0,
        spacing=4,
        margins=None,
    ):

        self._bg_RGBA = bg_RGBA
        self._size = size
        self._margins = margins

        self.im = None
        self.text_draw = None
        self._new_tb()

        self.font = ImageFont.load_default()
        self.formatted_fonts = {"main": self.font}
        self.typeface = typeface
        self.font_size = font_size
        self.font_RGBA = font_RGBA
        if None not in [typeface, font_size]:
            self.set_truetype_font(font_size, typeface)

        self.paragraph_indent = paragraph_indent
        self.new_line_indent = new_line_indent

        self.spacing = spacing

        self.text_cursor = (0, 0)

    @staticmethod
    def new_same_as(tb):
        new_tb = TextBox(
            size=tb._size,
            typeface=tb.typeface,
            font_size=tb.font_size,
            bg_RGBA=tb._bg_RGBA,
            font_RGBA=tb.font_RGBA,
            paragraph_indent=tb.paragraph_indent,
            new_line_indent=tb.new_line_indent,
            spacing=tb.spacing,
            margins=tb._margins,
        )
        new_tb.formatted_fonts = tb.formatted_fonts.copy()
        return new_tb

    def _new_tb(self):
        tb_wid, im_height = self._size
        margins = self._margins
        if margins is not None:
            left_right_marg = margins[0] + margins[2]
            upper_lower_marg = margins[1] + margins[3]
            tb_wid -= left_right_marg
            im_height -= upper_lower_marg
            if tb_wid <= 0 or im_height <= 0:
                raise ValueError("Specified margins are larger than the size of the TextBox")

        self.im = Image.new("RGBA", (tb_wid, im_height), color=self._bg_RGBA)
        self.text_draw = ImageDraw.Draw(self.im, "RGBA")

    def render(self) -> Image:
        if self._margins is None:
            return self.im.copy()
        left, upper, _, _ = self._margins
        margin_im = Image.new("RGBA", self._size, color=self._bg_RGBA)
        margin_im.paste(self.im, (left, upper))
        return margin_im

    @property
    def text_line_height(self):
        return self.text_draw.textsize("XT", font=self.font)[1]

    def lines_left(self, cursor="text_cursor") -> int:
        _, y_current = getattr(self, cursor, self.text_cursor)
        y_max = self.im.height
        y_remain = y_max - y_current

        line_height = self.text_line_height

        y_remain -= line_height
        if y_remain < 0:
            return 0

        return 1 + (y_remain // (line_height + self.spacing))

    def on_last_line(self, cursor="text_cursor") -> bool:

        return self.lines_left(cursor) == 1

    def is_exhausted(self, cursor="text_cursor") -> bool:
        return self.lines_left(cursor) == 0

    def at_new_line(self, cursor="text_cursor") -> bool:
        x, y = getattr(self, cursor, self.text_cursor)
        return x == 0

    def set_truetype_font(self, size=None, typeface=None, RGBA=None, style="main"):

        if RGBA is not None:
            if not isinstance(RGBA, tuple):
                raise TypeError(
                    "`RGBA` must be tuple containing 4 ints from 0 to 255. "
                    f"(Argument of type '{type(RGBA)}' was passed)"
                )
            elif len(RGBA) != 4:
                raise ValueError(
                    f"`RGBA` must be tuple containing 4 ints from 0 to 255. "
                    f"(Passed tuple contained {len(RGBA)} elements."
                )
            for val in RGBA:
                if not isinstance(val, int):
                    raise TypeError(
                        "`RGBA` must be tuple containing 4 ints from 0 to 255. "
                        f"(Passed tuple contained element of "
                        f"type '{type(val)}'"
                    )
                if val < 0 or val > 255:
                    raise ValueError(f"`RGBA` must contain ints from 0 to 255. (The passed tuple contained int {val})")
            self.font_RGBA = RGBA

        if typeface is None and size is None:
            return

        if typeface is None:
            typeface = self.typeface
        if typeface is None:
            self.font = ImageFont.load_default()
            return

        if size is None:
            size = self.font_size

        fs = ("main", "bold", "ital", "boldital")
        if style not in fs:
            raise ValueError("`formatting` must be 'main', 'bold', 'ital', or 'boldital'")

        self.formatted_fonts[style] = ImageFont.truetype(typeface, size)

        if style == "main":
            self.font = ImageFont.truetype(typeface, size)

            self.font_size = size
            self.typeface = typeface

    def write_paragraph(
        self,
        text,
        cursor="text_cursor",
        font_RGBA=None,
        reserve_last_line=False,
        override_legal_check=False,
        paragraph_indent=None,
        new_line_indent=None,
        justify=False,
        formatting=False,
        discard_formatting=False,
    ):

        if font_RGBA is None:
            font_RGBA = self.font_RGBA

        if paragraph_indent is None:
            paragraph_indent = self.paragraph_indent

        if new_line_indent is None:
            new_line_indent = self.new_line_indent

        if not isinstance(text, UnwrittenLines):
            text = self._wrap_text(
                text,
                paragraph_indent=paragraph_indent,
                new_line_indent=new_line_indent,
                formatting=formatting,
                discard_formatting=discard_formatting,
            )

        unwritten = text

        while unwritten.remaining > 0:
            if reserve_last_line and self.on_last_line(cursor=cursor):
                return unwritten
            line = unwritten._stage_next_line()

            unwrit_line = self.write_line(
                line,
                cursor=cursor,
                font_RGBA=font_RGBA,
                indent=None,
                reserve_last_line=reserve_last_line,
                override_legal_check=override_legal_check,
                justify=justify,
            )

            if unwrit_line is not None:
                unwritten._unstage()
                return unwritten

            unwritten._successful_write()

        if unwritten.remaining == 0:
            return None

        return unwritten

    def continue_paragraph(
        self,
        continue_lines: UnwrittenLines,
        cursor="text_cursor",
        font_RGBA=None,
        reserve_last_line=False,
        override_legal_check=False,
        justify=False,
    ):
        unwrit_lines = self.write_paragraph(
            text=continue_lines,
            cursor=cursor,
            font_RGBA=font_RGBA,
            reserve_last_line=reserve_last_line,
            override_legal_check=override_legal_check,
            justify=justify,
        )
        return unwrit_lines

    def write_line(
        self,
        text,
        cursor="text_cursor",
        font_RGBA=None,
        reserve_last_line=False,
        override_legal_check=False,
        indent=None,
        justify=False,
        formatting=False,
        discard_formatting=False,
    ):

        bad_text_error = TypeError("`text` must be type: str, FLine, or PLine")

        if isinstance(text, str):
            justifiable = True
            text = parse_into_line(text, formatting, justifiable, discard_formatting)
        elif isinstance(text, PLine):
            justifiable = text.justifiable
            formatting = False
        elif isinstance(text, FLine):
            justifiable = text.justifiable
            formatting = True
        else:
            raise bad_text_error

        if not self.at_new_line(cursor):
            self.next_line_cursor(cursor)

        if reserve_last_line and self.on_last_line(cursor=cursor):
            return text

        if font_RGBA is None:
            font_RGBA = self.font_RGBA

        if formatting:
            return self._write_fline(
                text, cursor, font_RGBA, override_legal_check, indent, justify=(justify and justifiable)
            )
        elif justify and justifiable and not formatting:
            copy_pline = PLine(txt=text.txt, justifiable=text.justifiable)

            orig_len = len(copy_pline.txt)
            copy_pline.txt = copy_pline.txt.lstrip(" ")
            deduced_indent = orig_len - len(copy_pline.txt)
            conv_line = copy_pline.to_fline()

            if indent is not None:
                deduced_indent += indent

            success_check = self._write_fline(
                conv_line, cursor, font_RGBA, override_legal_check, indent=deduced_indent, justify=justify
            )

            if success_check is not None:
                return text
        else:
            return self._write_pline(text, cursor, self.font, font_RGBA, override_legal_check, indent)

    def _write_pline(self, pline_obj: PLine, cursor, font, font_RGBA, override_legal_check=False, indent=None):

        if indent is not None:
            indent = " " * indent
        staged_line = pline_obj._stage(indent=indent)

        coord = getattr(self, cursor, self.text_cursor)
        legal = self._check_legal_textwrite(staged_line, font, cursor)
        if legal or override_legal_check:
            xy_delta = self._write_text(coord, staged_line, font, font_RGBA)
        else:
            pline_obj._unstage()
            return pline_obj

        self.next_line_cursor(cursor=cursor, commit=True)

        return None

    def _write_fline(
        self,
        fline_obj: FLine,
        cursor,
        font_RGBA,
        override_legal_check=False,
        indent=None,
        justify=False,
        fword_info=None,
    ):

        def update_coord(coord, xy_delta, new_xy_delta) -> tuple:

            x0, y0 = coord
            x_delta, y_delta = xy_delta
            new_x_delta, new_y_delta = new_xy_delta

            coord = (x0 + new_x_delta, y0)

            x_delta += new_x_delta
            if new_y_delta > y_delta:
                y_delta = new_y_delta

            xy_delta = (x_delta, y_delta)

            return coord, xy_delta

        if indent is not None:
            indent = " " * indent

        fwords = fline_obj._stage(indent=indent)

        if fword_info is None:
            fword_info = FWord._examine_fwords(fwords, fonts=self.formatted_fonts)
        line_info = fline_obj._extract_fword_info(fword_info, use_staged=True)

        px_all_spaces = self.im.width - line_info["line_word_w"]

        spwd = line_info["space_w"]
        bonus_sp_px = 0
        if line_info["total_spaces"] > 0:
            spwd = px_all_spaces // line_info["total_spaces"]
            bonus_sp_px = px_all_spaces % line_info["total_spaces"]

        illegal_width = False
        if px_all_spaces < 0 or spwd < line_info["space_w"]:
            illegal_width = True
        if illegal_width and (justify or not override_legal_check):
            fline_obj._unstage()
            return fline_obj

        is_legal = True
        if not override_legal_check:
            is_legal = self._check_legal_cursor((0, line_info["line_word_h"]), cursor=cursor)
        if not is_legal:
            fline_obj._unstage()
            return fline_obj

        coord = getattr(self, cursor, self.text_cursor)
        xy_delta = (0, 0)

        fwords_left = len(fwords)
        for fword in fwords:
            self.text_draw.text(coord, fword.txt, font=fword_info["font_dict"][fword], fill=font_RGBA)

            new_xy_delta = fword_info["word_px_dict"][fword]
            coord, xy_delta = update_coord(coord, xy_delta, new_xy_delta)

            if fwords_left > 1 and fword.xspace:
                space = spwd
                if bonus_sp_px > 0:
                    space += 1
                    bonus_sp_px -= 1
                if not justify:
                    space = fword_info["space_w"]
                coord, xy_delta = update_coord(coord, xy_delta, (space, 0))

            fwords_left -= 1

        self.next_line_cursor(cursor=cursor, commit=True)
        return None

    def write(
        self,
        text,
        cursor="text_cursor",
        font_RGBA=None,
        reserve_last_line=False,
        formatting=False,
        discard_formatting=False,
        paragraph_indent=None,
        new_line_indent=None,
    ):

        if paragraph_indent is None:
            paragraph_indent = self.paragraph_indent

        if new_line_indent is None:
            new_line_indent = self.new_line_indent

        def insert_new_indent(fwords_list, indent_chars):
            if indent_chars in [None, 0]:
                return
            ind_fw = FWord(" " * indent_chars, bold=False, ital=False, xspace=False, is_indent=True)
            fwords_list.insert(0, ind_fw)
            return

        next_indent = paragraph_indent
        if isinstance(text, str):
            fwords = all_parse(text, formatting, discard_formatting)
        elif isinstance(text, list):
            fwords = text
            next_indent = new_line_indent
        else:
            raise TypeError("`text` must be passed as a string, or as a list of FWord objects")

        if reserve_last_line and self.on_last_line(cursor=cursor):
            return fwords

        if font_RGBA is None:
            font_RGBA = self.font_RGBA

        coord = getattr(self, cursor, "text_cursor")

        if self.at_new_line(cursor=cursor):
            insert_new_indent(fwords, next_indent)

        next_indent = new_line_indent

        last_inserted_indent = False
        consecutive_unsuccessful = 0
        while len(fwords) > 0:
            fword = fwords.pop(0)
            style = f"{'bold' * fword.bold}{'ital' * fword.ital}"
            if style == "":
                style = "main"
            font = self.formatted_fonts.get(style, self.font)

            legal = self._check_legal_textwrite(fword.txt, font, cursor)
            if legal:
                xy_delta = self._write_text(coord, fword.txt, font=font, font_RGBA=font_RGBA)
                coord = self.same_line_cursor(xy_delta, cursor=cursor, add_space=fword.xspace, space_font=font)
                consecutive_unsuccessful = 0
                last_inserted_indent = False
            else:
                coord = self.next_line_cursor(cursor=cursor)
                fwords.insert(0, fword)
                consecutive_unsuccessful += 1

            if consecutive_unsuccessful > 1 or (reserve_last_line and self.on_last_line(cursor=cursor)):
                if last_inserted_indent:
                    fwords.pop(0)
                return fwords

            if self.at_new_line(cursor=cursor) and not last_inserted_indent:
                insert_new_indent(fwords, next_indent)
                last_inserted_indent = True

        return None

    @staticmethod
    def simplify_unwritten(unwritten, exclude_indent=False):
        if isinstance(unwritten, UnwrittenLines):
            lst = unwritten.simplify(exclude_indent=exclude_indent)
            return "\n".join(lst)
        elif isinstance(unwritten, (PLine, FLine)):
            return unwritten.simplify(exclude_indent=exclude_indent)
        elif not isinstance(unwritten, list):
            raise TypeError("`unwritten` must be of type FLine, PLine, UnwrittenLines; or  a list of FWord objects")

        return FWord.recompile_fwords(unwritten, exclude_indent=exclude_indent)

    def _write_text(self, coord: tuple, text: str, font, font_RGBA) -> tuple:

        w, h = self.text_draw.textsize(text, font=font)
        self.text_draw.text(coord, text, font=font, fill=font_RGBA)
        return (w, h)

    def _check_legal_textwrite(self, text, font, cursor="text_cursor") -> bool:

        w, h = self.text_draw.textsize(text, font=font)
        legal = self._check_legal_cursor((w, h), cursor=cursor)
        return legal

    def _wrap_text(self, text, paragraph_indent: int, new_line_indent: int, formatting=False, discard_formatting=False):

        final_lines = UnwrittenLines(lines=None, formatting=formatting)
        max_w = self.im.width

        text = text.strip("\r\n")
        text = text.replace("\r", "\n")
        rough_lines = text.split("\n")

        first_indent = FWord(" " * paragraph_indent, bold=False, ital=False, xspace=False, is_indent=True)
        later_indent = FWord(" " * new_line_indent, bold=False, ital=False, xspace=False, is_indent=True)

        fwi = FWord._examine_fwords(fwords=[first_indent, later_indent], fonts=self.formatted_fonts)
        space_w = fwi["space_w"]

        rl_count = 0
        last_bold = False
        last_ital = False
        for rough_line in rough_lines:
            justifiable = True
            indent = later_indent
            if rl_count == 0:
                indent = first_indent

            rough_line = rough_line.strip()

            if formatting:
                fwords, last_bold, last_ital = format_parse_deep(
                    rough_line, discard_formatting=discard_formatting, start_bold=last_bold, start_ital=last_ital
                )
            else:
                fwords = all_parse(rough_line, formatting, discard_formatting)

            if len(fwords) == 0:
                continue

            fwi = FWord._examine_fwords(fwords, self.formatted_fonts, fwi)

            cur_w = 0

            current_line_to_add = []
            candidate_line_list = []
            last_word_is_candidate = False
            at_new_line = True
            while len(fwords) > 0:
                cand_w = cur_w

                new_fword = indent
                if not at_new_line:
                    new_fword = fwords.pop(0)
                at_new_line = False
                candidate_line_list = current_line_to_add.copy()
                candidate_line_list.append(new_fword)

                w, h = fwi["word_px_dict"][new_fword]
                cand_w += w
                if cand_w > max_w:
                    nl = FLine(fwords=current_line_to_add, justifiable=justifiable, fword_info=fwi)
                    if not formatting:
                        nl = nl.to_pline()

                    final_lines.lines.append(nl)
                    indent = later_indent
                    if not new_fword.is_indent:
                        fwords.insert(0, new_fword)
                    current_line_to_add = []
                    last_word_is_candidate = True
                    at_new_line = True

                    cur_w = 0
                    for fword in current_line_to_add:
                        cur_w += fwi["word_px_dict"][fword][0]
                else:
                    last_word_is_candidate = False
                    current_line_to_add = candidate_line_list
                    cur_w = cand_w
                    if new_fword.xspace:
                        cur_w += space_w

            if current_line_to_add == candidate_line_list or last_word_is_candidate:
                justifiable = False

                nl = FLine(fwords=current_line_to_add, justifiable=justifiable, fword_info=fwi)
                if not formatting:
                    nl = nl.to_pline()
                final_lines.lines.append(nl)

            rl_count += 1

        final_lines.fword_info = fwi

        return final_lines

    def reset_cursor(self, cursor="text_cursor") -> tuple:
        self.set_cursor((0, 0), cursor)
        return (0, 0)

    def set_cursor(self, coord, cursor="text_cursor"):
        setattr(self, cursor, coord)

    def same_line_cursor(
        self, xy_delta, cursor="text_cursor", commit=True, add_space=True, space_font=None, prevent_linebreak=False
    ) -> tuple:
        x0, y0 = getattr(self, cursor, self.text_cursor)
        x_delta, _ = xy_delta
        space_px = 0
        if add_space:
            if space_font is None:
                space_font = self.font
            space_px, _ = self.text_draw.textsize(" ", space_font)
        x1 = x0 + x_delta + space_px
        if not prevent_linebreak and x1 >= self.im.width:
            return self.next_line_cursor(cursor=cursor, commit=commit)
        coord = (x1, y0)
        if commit:
            self.set_cursor(coord, cursor=cursor)
        return coord

    def next_line_cursor(self, cursor="text_cursor", commit=True) -> tuple:

        x = 0

        _, y0 = getattr(self, cursor, self.text_cursor)

        coord = (x, y0 + self.text_line_height + self.spacing)

        if commit:
            self.set_cursor(coord, cursor=cursor)

        return coord

    def update_cursor(self, xy_delta, cursor="text_cursor", commit=True) -> tuple:

        x_delta, y_delta = xy_delta
        x0, y0 = getattr(self, cursor, self.text_cursor)
        coord = (x0 + x_delta, y0 + y_delta)

        if commit:
            setattr(self, cursor, coord)

        return coord

    def _check_cursor_overshoot(self, xy_delta: tuple, cursor="text_cursor") -> tuple:

        cursor_check = getattr(self, cursor, None)
        if not isinstance(cursor_check, tuple):
            cursor = "text_cursor"

        x, y = self.update_cursor(xy_delta, cursor, commit=False)

        x_overshot = x - self.im.width
        y_overshot = y - self.im.height

        return (x_overshot, y_overshot)

    def _check_legal_cursor(self, xy_delta: tuple, cursor="text_cursor") -> bool:

        x_overshot, y_overshot = self._check_cursor_overshoot(xy_delta, cursor)
        if x_overshot > 0 or y_overshot > 0:
            return False
        return True
