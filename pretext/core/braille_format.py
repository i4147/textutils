import lxml.etree as ET

from . import common

__module_warning = common.__module_warning

log = common.log

try:
    import louis
except ImportError:
    raise ImportError(__module_warning.format("louis"))


class Segment:
    def __init__(self, s):

        self.xml = s

        attrs = s.attrib
        if ("newpage" in attrs) and (attrs["newpage"] == "yes"):
            self.newpage = True
        else:
            self.newpage = False

        if ("ownpage" in attrs) and (attrs["ownpage"] == "yes"):
            self.ownpage = True
        else:
            self.ownpage = False

        if ("centered" in attrs) and (attrs["centered"] == "yes"):
            self.centered = True
        else:
            self.centered = False

        if ("breakable" in attrs) and (attrs["breakable"] == "no"):
            self.breakable = False
        else:
            self.breakable = True

        if "indentation" in attrs:
            self.indentation = int(attrs["indentation"])
        else:
            self.indentation = 0

        if "runover" in attrs:
            self.runover = int(attrs["runover"])
        else:
            self.runover = 0

        if "lines-before" in attrs:
            self.lines_before = int(attrs["lines-before"])
        else:
            self.lines_before = 0

        if "lines-after" in attrs:
            self.lines_after = int(attrs["lines-after"])
        else:
            self.lines_after = 0

        if "lines-following" in attrs:
            self.lines_following = int(attrs["lines-following"])
        else:
            self.lines_following = 0

        if "heading-id" in attrs:
            self.heading_id = attrs["heading-id"]
        else:
            self.heading_id = None


class Block:
    def __init__(self, b):

        self.xml = b

        attrs = b.attrib

        if ("newpage" in attrs) and (attrs["newpage"] == "yes"):
            self.newpage = True
        else:
            self.newpage = False

        if ("ownpage" in attrs) and (attrs["ownpage"] == "yes"):
            self.ownpage = True
        else:
            self.ownpage = False

        if ("breakable" in attrs) and (attrs["breakable"] == "no"):
            self.breakable = False
        else:
            self.breakable = True

        if "lines-before" in attrs:
            self.lines_before = int(attrs["lines-before"])
        else:
            self.lines_before = 0

        if "lines-after" in attrs:
            self.lines_after = int(attrs["lines-after"])
        else:
            self.lines_after = 0

        if "lines-following" in attrs:
            self.lines_following = int(attrs["lines-following"])
        else:
            self.lines_following = 0

        if "box" in attrs:
            self.box = attrs["box"]
        else:
            self.box = None

        if "punctuation" in attrs:
            self.punctuation = attrs["punctuation"]
        else:
            self.punctuation = None


class Position:
    def __init__(self, row, page):
        self.row = row
        self.page = page

    def copy(self):
        return Position(self.row, self.page)


class PageLayout:
    page_num_sep = 3

    def __init__(self, width, height, page_format):
        self.width = width
        self.height = height
        if page_format == "emboss":
            self.emboss = True
        elif page_format == "electronic":
            self.emboss = False
        else:
            log.bug("page format not recognized, so embossing")
            self.emboss = True

    def is_last_row(self, position):
        return self.emboss and (position.row == self.height)

    def text_width(self, position, reduction):
        width = self.width - reduction
        if self.is_last_row(position):
            width -= PageLayout.page_num_sep + len(braille_number(position.page))
        return width

    def advance(self, position):
        if self.emboss and (position.row == self.height):
            return Position(1, position.page + 1)
        else:
            return Position(position.row + 1, position.page)

    def at_page_start(self, position):

        return self.emboss and (position.row == 1)


_TABLES = ["en-ueb-g2.ctb"]

NEMETH_OPEN = "⠸⠩"
NEMETH_CLOSE = "⠸⠱"


def translate_print(aline):

    return louis.translateString(_TABLES, aline, None, 0)


def contains_unicode_braille(aline):

    return any(("\u2801" <= c) and (c <= "\u28ff") for c in aline)


_braille_numbers = {}


def braille_number(number):
    if number not in _braille_numbers:
        _braille_numbers[number] = translate_print(str(number))
    return _braille_numbers[number]


class LineComposer:
    def __init__(self, layout, position, seg, symbols_early, reduction):
        self.layout = layout
        self.position = position.copy()
        self.seg = seg
        self.symbols_early = symbols_early

        self.reduction = reduction
        self.lines = []
        self.contents = ""
        self.first_line = True

    def at_line_start(self):
        return self.contents == ""

    def remaining_characters(self):
        return self.layout.text_width(self.position, self.reduction) - len(self.contents)

    def is_room(self, text):
        return self.remaining_characters() - len(text) >= 0

    def break_line(self):

        contents = self.contents.replace("\xa0", " ")

        if (contents != "") and (contents[-1] == " "):
            contents = contents[:-1]
        self.lines.append(contents)
        self.contents = ""
        self.position = self.layout.advance(self.position)

    def blank_line(self):
        assert self.at_line_start(), "BUG: creating a blank line, but not at the start of a line"
        self.break_line()

    def write_fragment(self, typeface, aline, math_punctuation):

        if typeface == "math":
            aline = self.massage_math(aline, math_punctuation)
        elif self.symbols_early and (typeface == "display-math") and not (contains_unicode_braille(aline)):
            aline = aline.replace("\xa0", " ")
        elif (typeface == "print") or contains_unicode_braille(aline):
            aline = translate_print(aline)

        prior_space = ""

        while aline != None:
            pieces = aline.split(" ", 1)
            word = pieces[0]
            next_text = prior_space + word

            if self.at_line_start():
                if self.first_line:
                    pad = self.seg.indentation
                    self.first_line = False
                else:
                    pad = self.seg.runover
                next_text = (" " * pad) + next_text

            if self.is_room(next_text):
                self.contents += next_text
                prior_space = " "
                if len(pieces) == 2:
                    aline = pieces[1]
                else:
                    aline = None
            elif not (self.at_line_start()):
                prior_space = ""
                self.break_line()
            else:
                room = self.remaining_characters()
                whole_line = word[: (room - 1)] + "-"
                aline = word[(room - 1) :]
                if len(pieces) == 2:
                    aline += " " + pieces[1]
                self.contents += whole_line

    def massage_math(self, aline, punctuation):

        width = self.layout.width

        nemeth_open = NEMETH_OPEN
        nemeth_close = NEMETH_CLOSE

        aline = aline.replace("\u2800", " ").replace("\xa0", " ")

        if punctuation:
            nemeth_close += punctuation
            punct_len = len(punctuation)
        else:
            punct_len = 0

        early_form = self.symbols_early and not (contains_unicode_braille(aline))

        if early_form:
            nemeth_open = translate_print(nemeth_open)
            nemeth_close = translate_print(nemeth_close)

        math_len = len(aline) + 6 + punct_len

        if math_len <= width:
            aline = nemeth_open + "\xa0" + aline.replace(" ", "\xa0") + "\xa0" + nemeth_close
        elif math_len <= width + 3:
            aline = nemeth_open + "\xa0" + aline.replace(" ", "\xa0") + " " + nemeth_close
        elif math_len <= width + 6 + punct_len:
            aline = nemeth_open + " " + aline.replace(" ", "\xa0") + " " + nemeth_close
        else:
            aline = nemeth_open + "\xa0" + aline + "\xa0" + nemeth_close

        if early_form:
            return aline

        return translate_print(aline)


class PageComposer:
    def __init__(self, layout, symbols_early):
        self.layout = layout
        self.symbols_early = symbols_early
        self.position = Position(1, 1)

        self.output = []

        self.toc_dict = {}

        self.toc_mode = False

    def at_page_start(self):
        return self.layout.at_page_start(self.position)

    def remaining_lines(self):

        return self.layout.height - self.position.row + 1

    def emit_line(self, contents):
        if self.layout.is_last_row(self.position):
            number = braille_number(self.position.page)
            gap = " " * (self.layout.width - len(contents) - len(number))
            contents = contents + gap + number
        self.output.append(contents)
        rollover = self.layout.is_last_row(self.position)
        self.position = self.layout.advance(self.position)
        if rollover:
            self.output[-1] += "\n\x0c"
        else:
            self.output[-1] += "\n"

    def blank_line(self):
        self.emit_line("")

    def advance_page(self):

        if not (self.layout.emboss):
            return
        for i in range(self.remaining_lines()):
            self.blank_line()

    def compose_segment(self, seg, position):

        reduction = 0
        if seg.centered:
            reduction += 6
        if self.toc_mode:
            reduction += 6

        composer = LineComposer(self.layout, position, seg, self.symbols_early, reduction)

        sxml = seg.xml
        if sxml.text:
            composer.write_fragment("text", sxml.text, None)
        for c in sxml:
            typeface = c.tag
            if typeface != "math":
                log.bug(
                    'unexpected element "{}" inside a segment; its text is rendered plain and any nested content is dropped'.format(
                        c.tag
                    )
                )
                typeface = "text"
            if c.text:
                if "punctuation" in c.attrib:
                    math_punctuation = c.attrib["punctuation"]
                else:
                    math_punctuation = None
                composer.write_fragment(typeface, c.text, math_punctuation)
            if c.tail:
                composer.write_fragment("text", c.tail, None)

        if self.toc_mode:
            composer.reduction -= 6
            if self.layout.emboss:
                page_num = str(self.toc_dict[seg.heading_id])
                guide_dots = composer.remaining_characters() - (1 + len(page_num))
                guide = ["", "", ""]
                if guide_dots > 0:
                    guide[0] = " "
                    guide_dots -= 1
                if guide_dots > 0:
                    guide[2] = " "
                    guide_dots -= 1
                if guide_dots > 0:
                    guide[1] = "⠐" * guide_dots
                composer.write_fragment("print", "".join(guide) + page_num, None)

        if not (composer.at_line_start()):
            composer.break_line()

        lines = composer.lines

        if seg.centered:
            centered = []
            for line in lines:
                if line == "":
                    centered.append(line)
                else:
                    pad = " " * ((self.layout.width - len(line)) // 2)
                    centered.append(pad + line)
            lines = centered
        return lines

    def compose_display_segment(self, seg, position):
        composer = LineComposer(self.layout, position, seg, self.symbols_early, 0)
        sxml = seg.xml
        if sxml.text:
            composer.write_fragment("display-math", sxml.text, None)
        if not (composer.at_line_start()):
            composer.break_line()
        return composer.lines

    def segment_lines(self, seg, position, in_nemeth_box):
        if in_nemeth_box:
            return self.compose_display_segment(seg, position)
        else:
            return self.compose_segment(seg, position)

    def needs_page_advance(self, lines_count, lines_following):
        if not (self.layout.emboss):
            return False
        total = lines_count + lines_following
        remaining = self.remaining_lines()

        if total <= remaining:
            return False

        if total > self.layout.height:
            return False

        return True

    def lay_block(self, blk, position):
        lines = []
        position = position.copy()

        def emit(line):
            nonlocal position
            lines.append(line)
            position = self.layout.advance(position)

        def fill_page():
            nonlocal position
            if not (self.layout.emboss):
                return
            for i in range(self.layout.height - position.row + 1):
                emit("")

        if blk.box == "standard":
            emit("7" * self.layout.text_width(position, 0))
        elif blk.box == "nemeth":
            emit(translate_print(NEMETH_OPEN))

        for child in blk.xml.xpath("segment|block"):
            if child.tag == "segment":
                seg = Segment(child)
                if seg.newpage and self.layout.emboss:
                    fill_page()
                if seg.ownpage and self.layout.emboss:
                    fill_page()
                blanks = 0 if self.layout.at_page_start(position) else seg.lines_before
                if not (seg.breakable) and self.layout.emboss and not (seg.ownpage or seg.newpage):
                    trial_position = position.copy()
                    for i in range(blanks):
                        trial_position = self.layout.advance(trial_position)
                    trial = self.segment_lines(seg, trial_position, blk.box == "nemeth")
                    remaining = self.layout.height - position.row + 1
                    total = blanks + len(trial) + seg.lines_after + seg.lines_following
                    if (total > remaining) and (total <= self.layout.height):
                        fill_page()
                        blanks = 0
                for i in range(blanks):
                    emit("")
                for line in self.segment_lines(seg, position, blk.box == "nemeth"):
                    emit(line)
                for i in range(seg.lines_after):
                    emit("")
                if seg.ownpage and self.layout.emboss:
                    fill_page()
            elif child.tag == "block":
                inner = Block(child)
                (inner_lines, position) = self.lay_inner_block(inner, position)
                for line in inner_lines:
                    lines.append(line)

        if blk.box == "standard":
            emit("g" * self.layout.text_width(position, 0))
        elif blk.box == "nemeth":
            close_brf = NEMETH_CLOSE
            if blk.punctuation:
                close_brf += blk.punctuation
            emit(translate_print(close_brf))

        return (lines, position)

    def lay_inner_block(self, blk, position):
        lines = []
        position = position.copy()

        def emit(line):
            nonlocal position
            lines.append(line)
            position = self.layout.advance(position)

        def fill_page():
            nonlocal position
            if not (self.layout.emboss):
                return
            for i in range(self.layout.height - position.row + 1):
                emit("")

        if blk.ownpage and self.layout.emboss:
            fill_page()

        initial_lines = 1
        if blk.box:
            initial_lines += 2
        if self.layout.emboss and ((self.layout.height - position.row + 1) < initial_lines):
            fill_page()
        blanks = 0 if self.layout.at_page_start(position) else blk.lines_before
        if not (blk.breakable) and self.layout.emboss and not (blk.ownpage):
            trial_position = position.copy()
            for i in range(blanks):
                trial_position = self.layout.advance(trial_position)
            (trial, _) = self.lay_block(blk, trial_position)
            remaining = self.layout.height - position.row + 1
            total = blanks + len(trial) + blk.lines_after + blk.lines_following
            if (total > remaining) and (total <= self.layout.height):
                fill_page()
                blanks = 0
        for i in range(blanks):
            emit("")
        (block_lines, position) = self.lay_block(blk, position)
        for line in block_lines:
            lines.append(line)
        for i in range(blk.lines_after):
            emit("")
        if blk.ownpage and self.layout.emboss:
            fill_page()
        return (lines, position)

    def write_segment(self, seg):
        if seg.newpage and self.layout.emboss:
            self.advance_page()
        if seg.ownpage and self.layout.emboss:
            self.advance_page()

        blanks = 0 if self.at_page_start() else seg.lines_before

        if not (seg.breakable) and self.layout.emboss and not (seg.ownpage or seg.newpage):
            position = self.position.copy()
            for i in range(blanks):
                position = self.layout.advance(position)
            trial = self.segment_lines(seg, position, False)
            if self.needs_page_advance(blanks + len(trial) + seg.lines_after, seg.lines_following):
                self.advance_page()

                blanks = 0

        for i in range(blanks):
            self.blank_line()

        if seg.heading_id and self.layout.emboss and not (self.toc_mode):
            self.toc_dict[seg.heading_id] = self.position.page

        for line in self.segment_lines(seg, self.position, False):
            self.emit_line(line)

        for i in range(seg.lines_after):
            self.blank_line()

        if seg.ownpage and self.layout.emboss:
            self.advance_page()

    def write_block(self, blk):
        if blk.ownpage and self.layout.emboss:
            self.advance_page()

        initial_lines = 1
        if blk.box:
            initial_lines += 2
        if self.layout.emboss and (self.remaining_lines() < initial_lines):
            self.advance_page()

        blanks = 0 if self.at_page_start() else blk.lines_before

        if not (blk.breakable) and self.layout.emboss and not (blk.ownpage):
            position = self.position.copy()
            for i in range(blanks):
                position = self.layout.advance(position)
            (trial, _) = self.lay_block(blk, position)
            if self.needs_page_advance(blanks + len(trial) + blk.lines_after, blk.lines_following):
                self.advance_page()
                blanks = 0

        for i in range(blanks):
            self.blank_line()

        (block_lines, _) = self.lay_block(blk, self.position)
        for line in block_lines:
            self.emit_line(line)

        for i in range(blk.lines_after):
            self.blank_line()

        if blk.ownpage and self.layout.emboss:
            self.advance_page()

    def get_brf(self):
        return "".join(self.output)


def parse_segments(xml_simple, out_file, page_format):

    huge_parser = ET.XMLParser(huge_tree=True)
    src_tree = ET.parse(xml_simple, parser=huge_parser)

    if src_tree.getroot().get("translated") != "yes":
        raise ValueError(
            "the braille renderer requires input from the translation pass, and this file has not been through it"
        )

    symbols = src_tree.getroot().get("brf-symbols", "late")
    symbols_early = symbols == "early"

    page_width = int(src_tree.getroot().get("page-width", "40"))
    page_height = int(src_tree.getroot().get("page-height", "25"))

    layout = PageLayout(page_width, page_height, page_format)

    body = PageComposer(layout, symbols_early)
    for elt in src_tree.xpath("/brf/segment|/brf/block"):
        if elt.tag == "segment":
            body.write_segment(Segment(elt))
        elif elt.tag == "block":
            body.write_block(Block(elt))

    front = PageComposer(layout, symbols_early)
    front.toc_mode = True
    front.toc_dict = body.toc_dict
    for head in src_tree.xpath("/brf/segment[@heading-id]"):
        seg = Segment(head)
        seg.newpage = False
        seg.ownpage = False
        seg.centered = False
        seg.breakable = False
        seg.lines_before = 0
        seg.lines_after = 0
        seg.lines_following = 0
        front.write_segment(seg)

    if page_format == "emboss":
        front.advance_page()

    with open(out_file, "w", encoding="utf-8") as brf_file:
        brf_file.write(front.get_brf())
        brf_file.write(body.get_brf())
