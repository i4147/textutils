from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import effects as fx
from .glyphs import BorrowedGlyph, SVGGlyph
from .kashida import Kashida, KashidaForms
from .layout import Layout
from .patching import GlyphSubstitution
from .sweeps import TadakhulMerged, TadakhulQuantised, TadakhulScaled
from .synth import Synthesizer
from .textrules import orthographic_variation

SWEEPS = {
    "merged": TadakhulMerged,
    "quantised": TadakhulQuantised,
    "scaled": TadakhulScaled,
}

PRESETS = {
    "none": [],
    "light": [fx.InkBleed(1.0, strength=0.6), fx.Speckle(0.001, strength=0.4)],
    "smudged": [
        fx.Smudge(length=6, strength=0.7),
        fx.Blobify(),
        fx.InkBleed(1.0, strength=0.5),
    ],
    "heavy": [
        fx.Warp(amplitude=1.5),
        fx.Smudge(length=10, strength=0.9, select=fx.ComponentFilter(min_area=10, count=12)),
        fx.Blobify(probability=0.9),
        fx.InkBleed(1.5),
        fx.Speckle(0.004, holes=0.02),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="textsynth",
        description="Render Perso-Arabic text to an image. Font patches and ink effects are optional.",
    )
    parser.add_argument("text", help="the text to render; use - to read stdin")
    parser.add_argument("-f", "--font", required=True, help="the path to the font file")
    parser.add_argument("-o", "--out", default="out.png", help="the path of the output image")
    parser.add_argument("-s", "--size", type=float, default=64.0, help="the em size in pixels")
    parser.add_argument("--tracking", type=float, default=0.0, help="the pixels to add between glyphs")
    parser.add_argument("--padding", type=int, default=40)
    parser.add_argument("--supersample", type=int, default=2)
    parser.add_argument("--foreground", default="black")
    parser.add_argument("--background", default="white")
    parser.add_argument(
        "--fallback", action="append", default=[], help="a fallback font; you can give this more than one time"
    )
    parser.add_argument("--distress", choices=sorted(PRESETS), default="none", help="the ink effect preset")
    parser.add_argument(
        "--vary",
        type=float,
        default=0.0,
        help="the probability of an equivalent letter, to vary the spelling",
    )
    parser.add_argument(
        "--substitute",
        action="append",
        default=[],
        metavar="SEQ=SOURCE",
        help="draw SEQ with a glyph from SOURCE, an .svg file or font.ttf:CHAR; you can give this more than one time",
    )
    parser.add_argument(
        "--kashida",
        type=int,
        default=0,
        metavar="N",
        help="make each word longer by N tatweels, and move the dots to agree",
    )
    parser.add_argument(
        "--kashida-contrast",
        type=float,
        default=0.8,
        help="0 puts the elongation equally along a word, 1 puts all of it in one place",
    )
    parser.add_argument(
        "--sweep",
        choices=sorted(SWEEPS),
        default=None,
        help="give the letters a terminal stroke that sweeps below the word",
    )
    parser.add_argument("--sweep-letters", default="و", help="the letters that can sweep; the default is waw")
    parser.add_argument("--sweep-length", type=int, default=2, help="the length of a sweep, in letters")
    parser.add_argument("--seed", type=int, default=None)
    return parser


def _parse_substitution(spec: str) -> GlyphSubstitution:
    sequence, _, source = spec.partition("=")
    if not sequence or not source:
        raise SystemExit(f"--substitute expects SEQ=SOURCE, got {spec!r}")
    if source.lower().endswith(".svg"):
        return GlyphSubstitution(sequence, SVGGlyph(source))
    font, _, char = source.rpartition(":")
    if not font:
        raise SystemExit(f"cannot read glyph source {source!r}: expected an .svg or font.ttf:CHAR")
    return GlyphSubstitution(sequence, BorrowedGlyph(font, char))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = sys.stdin.read() if args.text == "-" else args.text

    text_rules = []
    patches = [_parse_substitution(spec) for spec in args.substitute]
    if args.vary:
        text_rules.append(orthographic_variation(swap=args.vary))
    if args.kashida:
        text_rules.append(Kashida(frequency=args.kashida, contrast=args.kashida_contrast))
        patches.append(KashidaForms(max_run=args.kashida))
    glyph_rules = []
    if args.sweep:
        glyph_rules.append(SWEEPS[args.sweep](letters=args.sweep_letters, length=args.sweep_length))

    synth = Synthesizer(
        font=args.font,
        layout=Layout(
            size=args.size,
            tracking=args.tracking,
            padding=args.padding,
            supersample=args.supersample,
        ),
        text_rules=text_rules,
        font_patches=patches,
        glyph_rules=glyph_rules,
        effects=PRESETS[args.distress],
        fallbacks=args.fallback,
        foreground=args.foreground,
        background=args.background,
        seed=args.seed,
    )
    image = synth(text.rstrip("\n"))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    image.save(args.out)
    print(f"{args.out} ({image.width}x{image.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
