from __future__ import annotations

from dataclasses import dataclass, field
from io import BytesIO
from typing import Iterable, Mapping, Protocol, Sequence

from fontTools.otlLib import builder as otl
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables import otTables as ot

from .fonts import Font, FontLike
from .glyphs import GlyphSource, Outline
from .shaping import ShapeOptions, is_rtl, shape

DEFAULT_PROBE = "ب"

CONTEXT_PROBES: dict[str, tuple[bool, bool]] = {
    "isolated": (False, False),
    "initial": (False, True),
    "final": (True, False),
    "medial": (True, True),
}
ALL_CONTEXTS = tuple(CONTEXT_PROBES)

FEATURE_ORDER: tuple[str, ...] = (
    "stch",
    "ccmp",
    "locl",
    "isol",
    "fina",
    "fin2",
    "fin3",
    "medi",
    "med2",
    "init",
    "rlig",
    "rclt",
    "calt",
    "liga",
    "clig",
    "mset",
)


class FontPatch(Protocol):
    def apply(self, tt: TTFont, source: Font) -> None: ...


def patch_font(font: FontLike, patches: Sequence[FontPatch]) -> Font:
    source = Font.load(font)
    if not patches:
        return source
    tt = source.ttfont()
    for patch in patches:
        patch.apply(tt, source)
    buffer = BytesIO()
    tt.save(buffer)
    return Font(buffer.getvalue(), name=f"{source.name}+{len(patches)} patch(es)")


@dataclass
class GlyphSubstitution:
    text: str
    glyph: GlyphSource | Mapping[str, GlyphSource]
    contexts: Sequence[str] = ALL_CONTEXTS
    feature: str = "rlig"
    probe: str = DEFAULT_PROBE
    shape_options: ShapeOptions | None = None
    name_hint: str | None = None

    def apply(self, tt: TTFont, source: Font) -> None:
        sequences = shaped_sequences(
            source,
            self.text,
            contexts=self.contexts,
            probe=self.probe,
            options=probe_options(self.feature, self.shape_options),
        )
        if not sequences:
            raise ValueError(f"{self.text!r} produced no glyphs in {source.name}")

        order = source.glyph_order
        injected: dict[int, str] = {}
        singles: dict[str, str] = {}
        ligatures: dict[tuple[str, ...], str] = {}

        for context, gids in sequences.items():
            glyph_source = self._source_for(context)
            if glyph_source is None:
                continue
            key = id(glyph_source)
            if key not in injected:
                base = self.name_hint or f"fm.{_slug(self.text)}"
                injected[key] = inject_glyph(tt, base, glyph_source)
            replacement = injected[key]
            names = tuple(order[gid] for gid in gids)
            if len(names) == 1:
                singles[names[0]] = replacement
            else:
                ligatures[names] = replacement

        lookups = []
        if singles:
            lookups.append(otl.buildLookup([otl.buildSingleSubstSubtable(singles)]))
        if ligatures:
            lookups.append(otl.buildLookup([otl.buildLigatureSubstSubtable(ligatures)]))
        for lookup in lookups:
            add_gsub_lookup(tt, lookup, self.feature)

    def _source_for(self, context: str) -> GlyphSource | None:
        if isinstance(self.glyph, Mapping):
            return self.glyph.get(context)
        return self.glyph


@dataclass
class AddGlyph:
    glyph: GlyphSource
    char: str | None = None
    name: str = "fm.glyph"
    injected_name: str | None = field(default=None, init=False)
    injected_gid: int | None = field(default=None, init=False)

    def apply(self, tt: TTFont, source: Font) -> None:
        self.injected_name = inject_glyph(tt, self.name, self.glyph)
        self.injected_gid = tt.getGlyphID(self.injected_name)
        if self.char:
            for table in tt["cmap"].tables:
                if table.isUnicode():
                    table.cmap[ord(self.char)] = self.injected_name


def probe_options(feature: str, options: ShapeOptions | None = None) -> ShapeOptions:
    base = options or ShapeOptions()
    tag = feature.strip()
    if tag not in FEATURE_ORDER:
        return base
    later = FEATURE_ORDER[FEATURE_ORDER.index(tag) + 1 :]
    features = dict(base.features)
    features.update({t: False for t in later})
    return ShapeOptions(
        direction=base.direction,
        script=base.script,
        language=base.language,
        features=features,
    )


def shaped_sequences(
    font: FontLike,
    text: str,
    *,
    contexts: Iterable[str] = ALL_CONTEXTS,
    probe: str = DEFAULT_PROBE,
    options: ShapeOptions | None = None,
) -> dict[str, tuple[int, ...]]:
    source = Font.load(font)
    rtl = is_rtl(text, options)
    out: dict[str, tuple[int, ...]] = {}
    for context in contexts:
        if context not in CONTEXT_PROBES:
            raise ValueError(f"unknown joining context {context!r}; pick from {ALL_CONTEXTS}")
        before, after = CONTEXT_PROBES[context]
        prefix = probe if before else ""
        suffix = probe if after else ""
        glyphs = shape(prefix + text + suffix, source, options)
        lo, hi = len(prefix), len(prefix) + len(text)
        gids = [g.gid for g in glyphs if lo <= g.cluster < hi]
        if rtl:
            gids.reverse()
        if gids:
            out[context] = tuple(gids)
    seen: dict[tuple[int, ...], str] = {}
    unique: dict[str, tuple[int, ...]] = {}
    for context, gids in out.items():
        if gids in seen:
            continue
        seen[gids] = context
        unique[context] = gids
    return unique


def inject_glyph(tt: TTFont, name: str, source: GlyphSource) -> str:
    upem = tt["head"].unitsPerEm
    outline = source.build(upem)
    name = _unique_name(tt, name)

    if "glyf" in tt:
        _inject_glyf(tt, name, outline)
    elif "CFF " in tt:
        _inject_cff(tt, name, outline)
    else:
        raise ValueError("font has neither a 'glyf' nor a 'CFF ' table")

    bounds = outline.bounds()
    lsb = int(round(bounds[0])) if bounds else 0
    tt["hmtx"].metrics[name] = (int(round(outline.advance)), lsb)
    tt["maxp"].numGlyphs = len(tt.getGlyphOrder())
    return name


def _inject_glyf(tt: TTFont, name: str, outline: Outline) -> None:
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    pen = TTGlyphPen(tt.getGlyphSet())
    outline.draw(Cu2QuPen(pen, max_err=tt["head"].unitsPerEm / 1000.0))
    _register_name(tt, name)
    tt["glyf"][name] = pen.glyph()


def _inject_cff(tt: TTFont, name: str, outline: Outline) -> None:
    cff = tt["CFF "].cff
    top_dict = cff[cff.fontNames[0]]
    if hasattr(top_dict, "FDSelect"):
        raise ValueError("cannot inject glyphs into a CID-keyed CFF font")

    pen = T2CharStringPen(outline.advance, glyphSet=None)
    outline.draw(pen)
    charstring = pen.getCharString(private=top_dict.Private)

    charstrings = top_dict.CharStrings
    charstrings.charStringsIndex.append(charstring)
    charstrings.charStrings[name] = len(charstrings.charStringsIndex) - 1
    top_dict.charset.append(name)
    _register_name(tt, name)


def _register_name(tt: TTFont, name: str) -> None:
    order = list(tt.getGlyphOrder())
    if name not in order:
        order.append(name)
        tt.setGlyphOrder(order)


def _unique_name(tt: TTFont, base: str) -> str:
    existing = set(tt.getGlyphOrder())
    if base not in existing:
        return base
    i = 1
    while f"{base}.{i}" in existing:
        i += 1
    return f"{base}.{i}"


def _slug(text: str) -> str:
    return "".join(f"{ord(c):04x}" for c in text)


def add_gsub_lookup(tt: TTFont, lookup: ot.Lookup, feature_tag: str) -> int:
    feature_tag = f"{feature_tag:<4}"[:4]
    if "GSUB" not in tt:
        tt["GSUB"] = _empty_gsub()
    gsub = tt["GSUB"].table

    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)
    index = gsub.LookupList.LookupCount - 1

    matching = [r.Feature for r in gsub.FeatureList.FeatureRecord if r.FeatureTag == feature_tag]
    if matching:
        for feature in matching:
            feature.LookupListIndex.append(index)
            feature.LookupCount = len(feature.LookupListIndex)
    else:
        _append_feature(gsub, feature_tag, [index])
    return index


def _append_feature(gsub: ot.GSUB, tag: str, lookup_indices: list[int]) -> None:
    feature = ot.Feature()
    feature.FeatureParams = None
    feature.LookupListIndex = list(lookup_indices)
    feature.LookupCount = len(feature.LookupListIndex)

    record = ot.FeatureRecord()
    record.FeatureTag = tag
    record.Feature = feature

    records = gsub.FeatureList.FeatureRecord
    position = 0
    while position < len(records) and records[position].FeatureTag <= tag:
        position += 1
    records.insert(position, record)
    gsub.FeatureList.FeatureCount = len(records)

    def remap(old: int) -> int:
        return old + 1 if old >= position else old

    for script_record in gsub.ScriptList.ScriptRecord:
        script = script_record.Script
        for lang_sys in _lang_systems(script):
            lang_sys.FeatureIndex = [remap(i) for i in lang_sys.FeatureIndex]
            if lang_sys.ReqFeatureIndex not in (None, 0xFFFF):
                lang_sys.ReqFeatureIndex = remap(lang_sys.ReqFeatureIndex)
            lang_sys.FeatureIndex.append(position)
            lang_sys.FeatureCount = len(lang_sys.FeatureIndex)


def _lang_systems(script: ot.Script) -> list[ot.LangSys]:
    systems = []
    if script.DefaultLangSys is not None:
        systems.append(script.DefaultLangSys)
    systems.extend(record.LangSys for record in script.LangSysRecord or [])
    return systems


def _empty_gsub():
    table = newTable("GSUB")
    gsub = ot.GSUB()
    gsub.Version = 0x00010000

    lang_sys = ot.LangSys()
    lang_sys.LookupOrder = None
    lang_sys.ReqFeatureIndex = 0xFFFF
    lang_sys.FeatureIndex = []
    lang_sys.FeatureCount = 0

    script = ot.Script()
    script.DefaultLangSys = lang_sys
    script.LangSysRecord = []
    script.LangSysCount = 0

    record = ot.ScriptRecord()
    record.ScriptTag = "DFLT"
    record.Script = script

    gsub.ScriptList = ot.ScriptList()
    gsub.ScriptList.ScriptRecord = [record]
    gsub.ScriptList.ScriptCount = 1
    gsub.FeatureList = ot.FeatureList()
    gsub.FeatureList.FeatureRecord = []
    gsub.FeatureList.FeatureCount = 0
    gsub.LookupList = ot.LookupList()
    gsub.LookupList.Lookup = []
    gsub.LookupList.LookupCount = 0

    table.table = gsub
    return table
