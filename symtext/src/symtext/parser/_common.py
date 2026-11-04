from __future__ import annotations

import tree_sitter


def node_text(node: tree_sitter.Node, source: bytes) -> str:
    return source[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def find_child_by_type(node: tree_sitter.Node, type_name: str) -> tree_sitter.Node | None:
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def find_children_by_type(node: tree_sitter.Node, type_name: str) -> list[tree_sitter.Node]:
    return [child for child in node.children if child.type == type_name]


def cyclomatic_complexity(body_node: tree_sitter.Node, branch_types: frozenset[str]) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body_node]
    while stack:
        n = stack.pop()
        if n.type in branch_types:
            complexity += 1
        for child in n.children:
            stack.append(child)
    return complexity
