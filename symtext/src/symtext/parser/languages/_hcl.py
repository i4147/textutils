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
    ParsedImport,
)

_TWO_LABEL_BLOCKS: frozenset[str] = frozenset({"resource", "data"})

_ONE_LABEL_BLOCKS: frozenset[str] = frozenset({"variable", "output", "module", "provider"})


def _string_label_text(node: tree_sitter.Node, source: bytes) -> str:
    tl = find_child_by_type(node, "template_literal")
    if tl:
        return node_text(tl, source)
    return node_text(node, source).strip('"')


def _extract_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("//"):
            lines.append(text[2:].strip())
        elif text.startswith("#"):
            lines.append(text[1:].strip())
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_attributes(body: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    for child in body.children:
        if child.type == "attribute":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                attrs.append(node_text(id_node, source))
    return attrs


def _extract_references(body: tree_sitter.Node, source: bytes, result: FileParseResult) -> None:
    stack: list[tree_sitter.Node] = [body]
    while stack:
        n = stack.pop()
        if n.type == "variable_expr":
            _maybe_record_ref(n, source, result)
        for child in n.children:
            stack.append(child)


def _maybe_record_ref(var_node: tree_sitter.Node, source: bytes, result: FileParseResult) -> None:
    id_node = find_child_by_type(var_node, "identifier")
    if id_node is None:
        return
    prefix = node_text(id_node, source)
    if prefix not in ("var", "local", "module", "data"):
        return
    parent = var_node.parent
    if parent is None:
        return
    found_self = False
    for child in parent.children:
        if child.id == var_node.id:
            found_self = True
            continue
        if found_self and child.type == "get_attr":
            attr_id = find_child_by_type(child, "identifier")
            if attr_id:
                ref_name = node_text(attr_id, source)
                full_name = f"{prefix}.{ref_name}"
                result.calls.append(
                    ParsedCall(
                        name=ref_name,
                        line_number=var_node.start_point[0] + 1,
                        caller="",
                        full_call_name=full_name,
                    )
                )
            break


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    body = find_child_by_type(root, "body")
    if body is None:
        return
    for child in body.children:
        if child.type == "block":
            _handle_block(child, source, result)


def _handle_block(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    if id_node is None:
        return
    block_type = node_text(id_node, source)
    labels = find_children_by_type(node, "string_lit")
    body = find_child_by_type(node, "body")
    docstring = _extract_comment(node, source)

    if block_type in _TWO_LABEL_BLOCKS and len(labels) >= 2:
        type_name = _string_label_text(labels[0], source)
        res_name = _string_label_text(labels[1], source)
        name = f"{type_name}.{res_name}"
        attrs = _extract_attributes(body, source) if body else []
        result.classes.append(
            ParsedClass(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line_number=node.end_point[0] + 1,
                kind=block_type,
                bases=[],
                attributes=attrs,
                docstring=docstring,
            )
        )
        if body:
            _extract_references(body, source, result)

    elif block_type in _ONE_LABEL_BLOCKS and len(labels) >= 1:
        name = _string_label_text(labels[0], source)
        attrs = _extract_attributes(body, source) if body else []
        result.classes.append(
            ParsedClass(
                name=name,
                line_number=node.start_point[0] + 1,
                end_line_number=node.end_point[0] + 1,
                kind=block_type,
                bases=[],
                attributes=attrs,
                docstring=docstring,
            )
        )
        if block_type == "module" and body:
            _extract_module_source(body, source, result, node.start_point[0] + 1)
            _extract_references(body, source, result)
        elif body:
            _extract_references(body, source, result)

    elif block_type == "locals":
        if body:
            for attr_name in _extract_attributes(body, source):
                result.variables.append(attr_name)
            _extract_references(body, source, result)

    elif block_type == "terraform":
        result.classes.append(
            ParsedClass(
                name="terraform",
                line_number=node.start_point[0] + 1,
                end_line_number=node.end_point[0] + 1,
                kind="terraform",
                bases=[],
                attributes=_extract_attributes(body, source) if body else [],
                docstring=docstring,
            )
        )


def _extract_module_source(
    body: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    line: int,
) -> None:
    for child in body.children:
        if child.type == "attribute":
            id_node = find_child_by_type(child, "identifier")
            if id_node and node_text(id_node, source) == "source":
                expr = find_child_by_type(child, "expression")
                if expr is None:
                    continue
                lit = find_child_by_type(expr, "literal_value")
                if lit is None:
                    continue
                str_node = find_child_by_type(lit, "string_lit")
                if str_node is None:
                    continue
                module_path = _string_label_text(str_node, source)
                result.imports.append(
                    ParsedImport(
                        module=module_path,
                        line_number=line,
                    )
                )
                return
