from __future__ import annotations

from pathlib import Path

import numpy as np

from textsynth import (
    Blobify,
    BorrowedGlyph,
    ComponentFilter,
    GlyphSubstitution,
    InkBleed,
    Layout,
    Synthesizer,
    Smudge,
    Speckle,
    orthographic_variation,
    shaped_sequences,
)

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUT = ROOT / "out"

FONT = ASSETS / "fonts" / "Amiri-Regular.ttf"
DONOR = ASSETS / "fonts" / "Oblegg-Jawi.otf"

TEXT = "سايا ممباچ سورت خبر"


def main() -> None:
    OUT.mkdir(exist_ok=True)

    plain = Synthesizer(font=FONT, layout=Layout(size=72))
    plain(TEXT).save(OUT / "1-plain.png")

    tight = Synthesizer(font=FONT, layout=Layout(size=72, tracking=-1, supersample=2))
    tight(TEXT).save(OUT / "2-tight.png")

    mim_mim = GlyphSubstitution("مم", BorrowedGlyph(DONOR, "A"))
    print("mim-mim shapes into:", shaped_sequences(FONT, "مم"))

    patched = Synthesizer(
        font=FONT,
        layout=Layout(size=72, tracking=-1, supersample=2),
        font_patches=[mim_mim],
    )
    patched(TEXT).save(OUT / "3-patched.png")

    distressed = Synthesizer(
        font=FONT,
        layout=Layout(size=72, tracking=-1, supersample=2, jitter_y=0.6),
        font_patches=[mim_mim],
        effects=[
            Smudge(length=7, strength=0.75, select=ComponentFilter(min_area=20, count=6)),
            Blobify(merge_radius=4, probability=0.8),
            InkBleed(1.0, strength=0.6),
            Speckle(density=0.0015, holes=0.01),
        ],
        seed=7,
    )
    distressed(TEXT).save(OUT / "4-distressed.png")

    varied = Synthesizer(
        font=FONT,
        layout=Layout(size=72, tracking=-1, supersample=2, jitter_x=0.5, jitter_y=0.8),
        text_rules=[orthographic_variation(swap=0.35, drop_letters=0.1)],
        font_patches=[mim_mim],
        effects=[Smudge(length=5), Blobify(), InkBleed(1.0, strength=0.5)],
    )
    for i in range(4):
        varied.render(TEXT, seed=i).save(OUT / f"5-variant-{i}.png")
        print(f"variant {i}:", varied.apply_text_rules(TEXT, np.random.default_rng(i)))

    print(f"wrote images to {OUT}")


if __name__ == "__main__":
    main()
