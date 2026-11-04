from __future__ import annotations

import math

import dataclasses

from .ast import FileAST
from .render import Brief, Detail, render

LINE_GUARD = 240

_encoder = None
_encoder_tried = False


def _tiktoken_len(text: str) -> int | None:
    global _encoder, _encoder_tried
    if not _encoder_tried:
        _encoder_tried = True
        try:
            import tiktoken

            _encoder = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _encoder = None
    if _encoder is None:
        return None
    return len(_encoder.encode(text))


def fallback_len(text: str) -> int:
    return math.ceil(len(text) / 4)


def count_tokens(text: str) -> int:
    exact = _tiktoken_len(text)
    approx = fallback_len(text)
    return approx if exact is None else max(exact, approx)


LADDER: tuple[Detail, ...] = (
    Detail(),
    Detail(samples=1),
    Detail(samples=0),
    Detail(samples=0, col_mode="compact"),
    Detail(samples=0, col_mode="compact", meta_mode="keys", prose_mode="skip"),
    Detail(
        samples=0,
        col_mode="packed",
        meta_mode="keys",
        prose_mode="skip",
        map_mode="compact",
    ),
    Detail(
        samples=0,
        col_mode="runs",
        meta_mode="keys",
        prose_mode="skip",
        map_mode="compact",
    ),
    Detail(
        samples=0,
        col_mode="runs",
        meta_mode="keys",
        prose_mode="skip",
        map_mode="compact",
        recipe_mode="compact",
    ),
    Detail(
        samples=0,
        col_mode="floor",
        meta_mode="keys",
        prose_mode="skip",
        map_mode="compact",
        recipe_mode="compact",
    ),
    Detail(
        samples=0,
        col_mode="floor",
        meta_mode="count",
        prose_mode="skip",
        map_mode="floor",
        table_mode="floor",
        quirk_mode="compact",
        recipe_mode="floor",
    ),
)


def fits(brief: Brief, budget: int) -> bool:
    return count_tokens(brief.text) <= budget and len(brief.text.splitlines()) <= LINE_GUARD


def floor_brief(ast: FileAST) -> Brief:
    briefs = [render(ast, detail) for detail in LADDER]
    return min(
        briefs,
        key=lambda b: (
            len(b.text.splitlines()) > LINE_GUARD,
            len(b.text.splitlines()) if len(b.text.splitlines()) > LINE_GUARD else 0,
            count_tokens(b.text),
        ),
    )


def floor_tokens(ast: FileAST) -> int:
    return count_tokens(floor_brief(ast).text)


def _wide(ast: FileAST) -> bool:
    n_cols = sum(len(t.stats.columns) for t in ast.tables)
    return n_cols > LINE_GUARD


def _n_groups(ast: FileAST) -> int:
    from .rank import group_runs

    return sum(len(group_runs(t.stats.columns)) for t in ast.tables)


def packed_best(ast: FileAST) -> Brief:
    return fill(ast, 10**9)


def fill(ast: FileAST, budget: int) -> Brief:
    wide = _wide(ast)
    for detail in LADDER:
        if detail.col_mode == "packed":
            if not wide:
                continue
            brief = render(ast, detail)
            if fits(brief, budget):
                return brief
            lo, hi, best = 0, _n_groups(ast) - 1, None
            while lo <= hi:
                mid = (lo + hi) // 2
                trial = render(ast, dataclasses.replace(detail, col_expand=mid))
                if fits(trial, budget):
                    best, lo = trial, mid + 1
                else:
                    hi = mid - 1
            if best is not None:
                return best
            continue
        brief = render(ast, detail)
        if fits(brief, budget):
            return brief
    return floor_brief(ast)
