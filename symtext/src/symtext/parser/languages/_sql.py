from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    find_child_by_type,
    find_children_by_type,
    node_text,
)
from symtext.parser.parser import (
    FileParseResult,
    ParsedCall,
    ParsedClass,
    ParsedFunction,
)


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        stripped = text.lstrip("-").strip()
        if stripped:
            lines.append(stripped)
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _object_name(node: tree_sitter.Node, source: bytes) -> str:
    obj_ref = find_child_by_type(node, "object_reference")
    if obj_ref is None:
        return ""
    id_node = find_child_by_type(obj_ref, "identifier")
    return node_text(id_node, source) if id_node else ""


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for child in root.children:
        if child.type == "ERROR":
            continue
        if child.type == "statement":
            _handle_statement(child, source, result)
        elif child.type == "comment":
            pass


def _handle_statement(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for child in node.children:
        if child.type == "create_table":
            _handle_create_table(child, source, result)
        elif child.type == "create_view":
            _handle_create_view(child, source, result)
        elif child.type == "create_function":
            _handle_create_function(child, source, result)
        elif child.type == "create_index":
            _handle_create_index(child, source, result)
        elif child.type == "create_trigger":
            _handle_create_trigger(child, source, result)


def _handle_create_table(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name = _object_name(node, source)
    if not name:
        return

    stmt = node.parent
    docstring = _extract_doc_comment(stmt, source) if stmt else ""

    col_defs = find_child_by_type(node, "column_definitions")
    attributes: list[str] = []
    if col_defs:
        for col in find_children_by_type(col_defs, "column_definition"):
            id_node = find_child_by_type(col, "identifier")
            if id_node:
                attributes.append(node_text(id_node, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="table",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_create_view(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name = _object_name(node, source)
    if not name:
        return

    stmt = node.parent
    docstring = _extract_doc_comment(stmt, source) if stmt else ""

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="view",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )


def _handle_create_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name = _object_name(node, source)
    if not name:
        return

    stmt = node.parent
    docstring = _extract_doc_comment(stmt, source) if stmt else ""

    args: list[str] = []
    func_args = find_child_by_type(node, "function_arguments")
    if func_args:
        for fa in find_children_by_type(func_args, "function_argument"):
            id_node = find_child_by_type(fa, "identifier")
            if id_node:
                args.append(node_text(id_node, source))

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context="",
            cyclomatic_complexity=1,
            is_async=False,
            return_type="",
        )
    )


def _handle_create_index(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    if id_node is None:
        return
    name = node_text(id_node, source)
    if name:
        result.variables.append(name)


def _handle_create_trigger(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    obj_refs = find_children_by_type(node, "object_reference")
    if not obj_refs:
        return
    trigger_name_node = find_child_by_type(obj_refs[0], "identifier")
    name = node_text(trigger_name_node, source) if trigger_name_node else ""
    if not name:
        return

    stmt = node.parent
    docstring = _extract_doc_comment(stmt, source) if stmt else ""

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="trigger",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    if len(obj_refs) >= 3:
        func_ref = obj_refs[-1]
        func_id = find_child_by_type(func_ref, "identifier")
        if func_id:
            func_name = node_text(func_id, source)
            result.calls.append(
                ParsedCall(
                    name=func_name,
                    line_number=func_ref.start_point[0] + 1,
                    caller=name,
                    full_call_name=func_name,
                )
            )
