from __future__ import annotations

from .ast import FileAST
from .budget import fill
from .render import Brief

DEFAULT_BUDGET = 2000


def brief(ast: FileAST, budget: int = DEFAULT_BUDGET) -> str:
    return fill(ast, budget).text


def brief_with_facts(ast: FileAST, budget: int = DEFAULT_BUDGET) -> Brief:
    return fill(ast, budget)
