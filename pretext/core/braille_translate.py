import lxml.etree as ET

from . import common

__module_warning = common.__module_warning
log = common.log

try:
    import louis
except ImportError:
    raise ImportError(__module_warning.format("louis"))

_TABLES = ["en-ueb-g2.ctb"]

#     emph_1 = italic = 0x0001
#     emph_3 = bold = 0x0004
_TYPEFORM_BITS = {
    "italic": 0x0001,
    "bold": 0x0004,
    "code": louis.getTypeformForEmphClass(_TABLES, "trans1"),
}


def _typeform_bits(typeform):
    bits = 0
    for token in typeform.split():
        if token in _TYPEFORM_BITS:
            bits |= _TYPEFORM_BITS[token]
        else:
            log.bug('the typeform token "{}" is not recognized, and is ignored'.format(token))
    return bits


def _translate_chunk(chunk):
    pieces = []
    typeforms = []
    for element, slot, bits in chunk:
        piece = getattr(element, slot) or ""
        pieces.append(piece)
        typeforms.extend([bits] * len(piece))
    whole = "".join(pieces)
    if whole == "":
        return
    if not any(typeforms):
        typeforms = None
    braille = louis.translateString(_TABLES, whole, typeforms, 0)
    (element, slot, _) = chunk[0]
    setattr(element, slot, braille)
    for element, slot, _ in chunk[1:]:
        setattr(element, slot, None)


def _translate_segment(segment):
    chunk = [(segment, "text", 0)]
    for child in segment:
        if child.tag == "math":
            _translate_chunk(chunk)
            chunk = [(child, "tail", 0)]
        elif child.tag == "run":
            chunk.append((child, "text", _typeform_bits(child.get("typeform", ""))))
            chunk.append((child, "tail", 0))
        else:
            log.bug('unexpected element "{}" inside a segment; its content is treated as plain text'.format(child.tag))
            chunk.append((child, "text", 0))
            chunk.append((child, "tail", 0))
    _translate_chunk(chunk)
    for child in list(segment):
        if child.tag == "run":
            segment.remove(child)


def translate_document(xml_in, xml_out):
    huge_parser = ET.XMLParser(huge_tree=True)
    tree = ET.parse(xml_in, parser=huge_parser)
    root = tree.getroot()
    for segment in root.iter("segment"):
        in_nemeth_box = any(
            (ancestor.tag == "block") and (ancestor.get("box") == "nemeth") for ancestor in segment.iterancestors()
        )
        if not in_nemeth_box:
            _translate_segment(segment)
    root.set("translated", "yes")
    tree.write(xml_out, xml_declaration=True, encoding="UTF-8")
