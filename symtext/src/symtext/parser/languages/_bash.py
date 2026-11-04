from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    cyclomatic_complexity,
    find_child_by_type,
    node_text,
)
from symtext.parser.parser import (
    FileParseResult,
    ParsedCall,
    ParsedFunction,
    ParsedImport,
)

_COMPLEXITY_NODES: frozenset[str] = frozenset({
    "if_statement",
    "for_statement",
    "while_statement",
    "case_item",
    "elif_clause",
})


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("#"):
            lines.append(text[1:].strip())
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    _walk(root, source, result, caller="")


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "function_definition":
            _handle_function(child, source, result, caller)

        elif child.type == "command":
            _handle_command(child, source, result, caller)

        elif child.type == "declaration_command":
            _handle_declaration(child, source, result, caller)

        elif child.type == "pipeline":
            _handle_pipeline(child, source, result, caller)

        elif child.child_count > 0 and child.type not in ("string", "comment"):
            _walk(child, source, result, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    name_node = find_child_by_type(node, "word")
    if name_node is None:
        return
    name = node_text(name_node, source)

    docstring = _extract_doc_comment(node, source)
    body = find_child_by_type(node, "compound_statement")
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=[],
            decorators=[],
            docstring=docstring,
            class_context="",
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )
    if body:
        _walk(body, source, result, caller=name)


def _handle_command(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    cmd_name_node = find_child_by_type(node, "command_name")
    if cmd_name_node is None:
        return
    word_node = find_child_by_type(cmd_name_node, "word")
    if word_node is None:
        return
    cmd_name = node_text(word_node, source)

    if cmd_name in ("source", "."):
        _handle_source_import(node, source, result, cmd_name_node)
        return

    result.calls.append(
        ParsedCall(
            name=cmd_name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=cmd_name,
        )
    )


def _handle_source_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    cmd_name_node: tree_sitter.Node,
) -> None:
    for child in node.children:
        if child.id == cmd_name_node.id:
            continue
        if child.type == "word":
            path = node_text(child, source)
            result.imports.append(
                ParsedImport(
                    module=path,
                    line_number=node.start_point[0] + 1,
                )
            )
            return
        if child.type == "string":
            sc = find_child_by_type(child, "string_content")
            path = node_text(sc, source) if sc else node_text(child, source).strip("\"'")
            result.imports.append(
                ParsedImport(
                    module=path,
                    line_number=node.start_point[0] + 1,
                )
            )
            return


def _handle_declaration(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "variable_assignment":
            var_name_node = find_child_by_type(child, "variable_name")
            if var_name_node:
                result.variables.append(node_text(var_name_node, source))


def _handle_pipeline(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "command":
            _handle_command(child, source, result, caller)
