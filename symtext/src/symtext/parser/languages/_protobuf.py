from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    find_child_by_type,
    find_children_by_type,
    node_text,
)
from symtext.parser.parser import (
    FileParseResult,
    ParsedClass,
    ParsedFunction,
    ParsedImport,
)


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        stripped = text.lstrip("/").strip()
        if stripped:
            lines.append(stripped)
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
    for child in root.children:
        if child.type == "message":
            _handle_message(child, source, result)
        elif child.type == "enum":
            _handle_enum(child, source, result)
        elif child.type == "service":
            _handle_service(child, source, result)
        elif child.type == "import":
            _handle_import(child, source, result)
        elif child.type == "package":
            _handle_package(child, source, result)


def _handle_message(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "message_name")
    if name_node is None:
        return
    id_node = find_child_by_type(name_node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)
    body = find_child_by_type(node, "message_body")
    attributes = _extract_field_names(body, source) if body else []

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="message",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )

    if body:
        for child in body.children:
            if child.type == "message":
                _handle_message(child, source, result)
            elif child.type == "enum":
                _handle_enum(child, source, result)


def _handle_enum(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "enum_name")
    if name_node is None:
        return
    id_node = find_child_by_type(name_node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)
    body = find_child_by_type(node, "enum_body")
    attributes = _extract_enum_values(body, source) if body else []

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="enum",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_service(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "service_name")
    if name_node is None:
        return
    id_node = find_child_by_type(name_node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)
    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="service",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    for child in node.children:
        if child.type == "rpc":
            _handle_rpc(child, source, result, class_context=name)


def _handle_rpc(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "rpc_name")
    if name_node is None:
        return
    id_node = find_child_by_type(name_node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    args: list[str] = []
    req_type = find_child_by_type(node, "message_or_enum_type")
    if req_type:
        req_id = find_child_by_type(req_type, "identifier")
        if req_id:
            args.append(node_text(req_id, source))

    return_type = ""
    msg_types = find_children_by_type(node, "message_or_enum_type")
    if len(msg_types) >= 2:
        resp_id = find_child_by_type(msg_types[1], "identifier")
        if resp_id:
            return_type = node_text(resp_id, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=1,
            is_async=False,
            return_type=return_type,
        )
    )


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    str_node = find_child_by_type(node, "string")
    if str_node is None:
        return
    text = node_text(str_node, source).strip('"')
    if text:
        result.imports.append(
            ParsedImport(
                module=text,
                line_number=node.start_point[0] + 1,
            )
        )


def _handle_package(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    full_ident = find_child_by_type(node, "full_ident")
    if full_ident is None:
        return
    ids = find_children_by_type(full_ident, "identifier")
    name = ".".join(node_text(i, source) for i in ids)
    if name:
        result.variables.append(name)


def _extract_field_names(body: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    for child in body.children:
        if child.type == "field":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                attrs.append(node_text(id_node, source))
    return attrs


def _extract_enum_values(body: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    for child in body.children:
        if child.type == "enum_field":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                attrs.append(node_text(id_node, source))
    return attrs
