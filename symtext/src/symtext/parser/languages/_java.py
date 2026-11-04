from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    find_child_by_type,
    node_text,
)
from symtext.parser.parser import (
    FileParseResult,
    ParsedCall,
    ParsedClass,
    ParsedFunction,
    ParsedImport,
)

_COMPLEXITY_NODES: frozenset[str] = frozenset({
    "if_statement",
    "for_statement",
    "enhanced_for_statement",
    "while_statement",
    "switch_block_statement_group",
    "catch_clause",
    "conditional_expression",
    "binary_expression",
})


def _java_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body_node]
    while stack:
        n = stack.pop()
        if n.type == "binary_expression":
            for child in n.children:
                txt = node_text(child, source)
                if txt in ("&&", "||"):
                    complexity += 1
        elif n.type in _COMPLEXITY_NODES:
            complexity += 1
        for child in n.children:
            stack.append(child)
    return complexity


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type in ("formal_parameter", "spread_parameter"):
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev and prev.type == "block_comment":
        text = node_text(prev, source)
        if text.startswith("/**"):
            inner = text[3:]
            if inner.endswith("*/"):
                inner = inner[:-2]
            lines: list[str] = []
            for line in inner.split("\n"):
                stripped = line.strip().lstrip("* ").strip()
                if stripped:
                    lines.append(stripped)
            return "\n".join(lines)
    return ""


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    modifiers = find_child_by_type(node, "modifiers")
    if modifiers is None:
        return decorators
    for child in modifiers.children:
        if child.type in ("marker_annotation", "annotation"):
            name_node = find_child_by_type(child, "identifier")
            if name_node:
                decorators.append(node_text(name_node, source))
    return decorators


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    name_node = call_node.child_by_field_name("name")
    obj_node = call_node.child_by_field_name("object")
    if name_node is None:
        return ("", "")
    simple = node_text(name_node, source)
    if obj_node:
        full = node_text(obj_node, source) + "." + simple
        return (simple, full)
    return (simple, simple)


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    _walk(root, source, result, class_context="", caller="")


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type in ("method_declaration", "constructor_declaration"):
            _handle_method(child, source, result, class_context)

        elif child.type in (
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
        ):
            _handle_class(child, source, result)

        elif child.type == "import_declaration":
            _handle_import(child, source, result)

        elif child.type == "method_invocation":
            simple, full = _extract_call_name(child, source)
            if simple:
                result.calls.append(
                    ParsedCall(
                        name=simple,
                        line_number=child.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full,
                    )
                )
            args_node = child.child_by_field_name("arguments")
            if args_node:
                _walk(args_node, source, result, class_context, caller)

        elif child.type == "object_creation_expression":
            _handle_new_expression(child, source, result, caller)

        elif child.type == "field_declaration" and class_context:
            _handle_field(child, source, result)

        elif child.child_count > 0 and child.type not in (
            "method_declaration",
            "constructor_declaration",
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "record_declaration",
            "import_declaration",
            "string_literal",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_method(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    params = node.child_by_field_name("parameters")
    args = _extract_params(params, source) if params else []
    body = node.child_by_field_name("body")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)
    complexity = _java_cyclomatic(body, source) if body else 1

    return_type = ""
    type_node = node.child_by_field_name("type")
    if type_node:
        return_type = node_text(type_node, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=decorators,
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context, caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "record_declaration": "class",
    }
    kind = kind_map.get(node.type, "class")

    bases: list[str] = []
    superclass = find_child_by_type(node, "superclass")
    if superclass:
        type_id = find_child_by_type(superclass, "type_identifier")
        if type_id:
            bases.append(node_text(type_id, source))
    super_interfaces = find_child_by_type(node, "super_interfaces")
    if super_interfaces:
        type_list = find_child_by_type(super_interfaces, "type_list")
        if type_list:
            for child in type_list.children:
                if child.type == "type_identifier":
                    bases.append(node_text(child, source))

    attributes: list[str] = []
    body = node.child_by_field_name("body")
    if body:
        for child in body.children:
            if child.type == "field_declaration":
                for sub in child.children:
                    if sub.type == "variable_declarator":
                        id_node = find_child_by_type(sub, "identifier")
                        if id_node:
                            attributes.append(node_text(id_node, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind=kind,
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )

    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    is_wildcard = any(child.type == "asterisk" for child in node.children)

    scoped = find_child_by_type(node, "scoped_identifier")
    if scoped:
        module = node_text(scoped, source)
        if is_wildcard:
            module += ".*"
        result.imports.append(ParsedImport(module=module, line_number=node.start_point[0] + 1))
        return

    id_node = find_child_by_type(node, "identifier")
    if id_node:
        module = node_text(id_node, source)
        result.imports.append(ParsedImport(module=module, line_number=node.start_point[0] + 1))


def _handle_new_expression(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    type_node = node.child_by_field_name("type")
    if type_node:
        name = node_text(type_node, source)
        result.calls.append(
            ParsedCall(
                name=name,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name="new " + name,
            )
        )
    args_node = find_child_by_type(node, "argument_list")
    if args_node:
        _walk(args_node, source, result, class_context="", caller=caller)


def _handle_field(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    modifiers = find_child_by_type(node, "modifiers")
    is_static = False
    if modifiers:
        for child in modifiers.children:
            if node_text(child, source) == "static":
                is_static = True
                break
    if is_static:
        for child in node.children:
            if child.type == "variable_declarator":
                id_node = find_child_by_type(child, "identifier")
                if id_node:
                    result.variables.append(node_text(id_node, source))
