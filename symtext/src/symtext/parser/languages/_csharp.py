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
    ParsedImport,
)

_COMPLEXITY_NODES: frozenset[str] = frozenset({
    "if_statement",
    "for_statement",
    "for_each_statement",
    "while_statement",
    "do_statement",
    "switch_section",
    "catch_clause",
    "conditional_expression",
    "binary_expression",
})


def _csharp_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
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
        if child.type == "parameter":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("///"):
            inner = text[3:].strip()
            return inner
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
    for child in node.children:
        if child.type == "attribute_list":
            for attr in child.children:
                if attr.type == "attribute":
                    name_node = find_child_by_type(attr, "identifier")
                    if name_node:
                        decorators.append(node_text(name_node, source))
    return decorators


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func_node = call_node.child_by_field_name("function")
    if func_node is None:
        return ("", "")
    if func_node.type == "member_access_expression":
        name_node = func_node.child_by_field_name("name")
        expr_node = func_node.child_by_field_name("expression")
        if name_node is None:
            return ("", "")
        simple = node_text(name_node, source)
        if expr_node:
            full = node_text(expr_node, source) + "." + simple
            return (simple, full)
        return (simple, simple)
    if func_node.type == "identifier":
        name = node_text(func_node, source)
        return (name, name)
    name = node_text(func_node, source)
    return (name, name)


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
            "struct_declaration",
            "record_declaration",
        ):
            _handle_class(child, source, result)

        elif child.type == "using_directive":
            _handle_using(child, source, result)

        elif child.type == "invocation_expression":
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

        elif child.type == "namespace_declaration":
            body = find_child_by_type(child, "declaration_list")
            if body:
                _walk(body, source, result, class_context, caller)

        elif child.child_count > 0 and child.type not in (
            "method_declaration",
            "constructor_declaration",
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "struct_declaration",
            "record_declaration",
            "using_directive",
            "string_literal",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_method(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "identifier")
    name = node_text(name_node, source) if name_node else ""
    params = find_child_by_type(node, "parameter_list")
    args = _extract_params(params, source) if params else []
    body = find_child_by_type(node, "block")
    arrow = find_child_by_type(node, "arrow_expression_clause")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)

    complexity_node = body or arrow
    complexity = _csharp_cyclomatic(complexity_node, source) if complexity_node else 1

    modifiers = find_children_by_type(node, "modifier")
    is_async = any(node_text(m, source) == "async" for m in modifiers)

    return_type = ""
    type_node = find_child_by_type(node, "predefined_type") or find_child_by_type(node, "generic_name")
    if type_node is None:
        type_node = find_child_by_type(node, "type_identifier")
    if type_node is None:
        type_node = find_child_by_type(node, "nullable_type")
    if type_node is None:
        type_node = find_child_by_type(node, "array_type")
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
            is_async=is_async,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context, caller=name)
    elif arrow:
        _walk(arrow, source, result, class_context, caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "struct_declaration": "struct",
        "record_declaration": "class",
    }
    kind = kind_map.get(node.type, "class")

    bases: list[str] = []
    base_list = find_child_by_type(node, "base_list")
    if base_list:
        for child in base_list.children:
            if child.type == "identifier":
                bases.append(node_text(child, source))

    attributes: list[str] = []
    body = find_child_by_type(node, "declaration_list")
    if body:
        for child in body.children:
            if child.type == "field_declaration":
                var_decl = find_child_by_type(child, "variable_declaration")
                if var_decl:
                    for sub in var_decl.children:
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


def _handle_using(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    identifiers = find_children_by_type(node, "identifier")
    qualified = find_child_by_type(node, "qualified_name")
    eq_present = any(c.type == "=" for c in node.children)

    if eq_present and qualified and identifiers:
        alias = node_text(identifiers[0], source)
        module = node_text(qualified, source)
        result.imports.append(
            ParsedImport(
                module=module,
                line_number=node.start_point[0] + 1,
                alias=alias,
            )
        )
        return

    if qualified:
        module = node_text(qualified, source)
    elif identifiers:
        module = node_text(identifiers[0], source)
    else:
        return

    result.imports.append(ParsedImport(module=module, line_number=node.start_point[0] + 1))


def _handle_new_expression(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    type_node = node.child_by_field_name("type")
    if type_node:
        if type_node.type == "generic_name":
            id_node = find_child_by_type(type_node, "identifier")
            name = node_text(id_node, source) if id_node else node_text(type_node, source)
        else:
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
    modifiers = find_children_by_type(node, "modifier")
    is_static = any(node_text(m, source) == "static" for m in modifiers)
    if is_static:
        var_decl = find_child_by_type(node, "variable_declaration")
        if var_decl:
            for child in var_decl.children:
                if child.type == "variable_declarator":
                    id_node = find_child_by_type(child, "identifier")
                    if id_node:
                        result.variables.append(node_text(id_node, source))
