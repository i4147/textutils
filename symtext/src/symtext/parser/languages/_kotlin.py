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
    "if_expression",
    "for_statement",
    "while_statement",
    "do_while_statement",
    "when_entry",
    "catch_block",
    "conjunction_expression",
    "disjunction_expression",
})


def _kotlin_cyclomatic(body_node: tree_sitter.Node) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body_node]
    while stack:
        n = stack.pop()
        if n.type in _COMPLEXITY_NODES:
            complexity += 1
        for child in n.children:
            stack.append(child)
    return complexity


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "parameter":
            id_node = find_child_by_type(child, "simple_identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    comment_node = _find_preceding_comment(node)
    if comment_node is None:
        return ""
    text = node_text(comment_node, source)
    if not text.startswith("/**"):
        return ""
    inner = text[3:]
    if inner.endswith("*/"):
        inner = inner[:-2]
    lines: list[str] = []
    for line in inner.split("\n"):
        stripped = line.strip().lstrip("* ").strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _find_preceding_comment(node: tree_sitter.Node) -> tree_sitter.Node | None:
    decl_line = node.start_point[0]
    prev = node.prev_named_sibling
    if prev is None:
        return None
    if prev.type == "multiline_comment":
        return prev
    if prev.named_children:
        last = prev.named_children[-1]
        if last.type == "multiline_comment" and last.end_point[0] >= decl_line - 2:
            return last
        if last.named_children:
            deepest = last.named_children[-1]
            if deepest.type == "multiline_comment" and deepest.end_point[0] >= decl_line - 2:
                return deepest
    return None


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    modifiers = find_child_by_type(node, "modifiers")
    if modifiers is None:
        return decorators
    for child in modifiers.children:
        if child.type == "annotation":
            ci = find_child_by_type(child, "constructor_invocation")
            if ci:
                ut = find_child_by_type(ci, "user_type")
                if ut:
                    ti = find_child_by_type(ut, "type_identifier")
                    if ti:
                        decorators.append(node_text(ti, source))
                continue
            ut = find_child_by_type(child, "user_type")
            if ut:
                ti = find_child_by_type(ut, "type_identifier")
                if ti:
                    decorators.append(node_text(ti, source))
    return decorators


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
        if child.type == "function_declaration":
            _handle_function(child, source, result, class_context)

        elif child.type in ("class_declaration", "object_declaration"):
            _handle_class(child, source, result)

        elif child.type == "import_list":
            _handle_import_list(child, source, result)

        elif child.type == "call_expression":
            _handle_call(child, source, result, class_context, caller)

        elif child.type == "property_declaration":
            _handle_property(child, source, result, class_context)
            _walk(child, source, result, class_context, caller)
            continue

        elif child.child_count > 0 and child.type not in (
            "function_declaration",
            "class_declaration",
            "object_declaration",
            "import_list",
            "string_literal",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "simple_identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    params_node = find_child_by_type(node, "function_value_parameters")
    args = _extract_params(params_node, source) if params_node else []
    body = find_child_by_type(node, "function_body")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)
    complexity = _kotlin_cyclomatic(body) if body else 1

    modifiers_node = find_child_by_type(node, "modifiers")
    is_async = False
    if modifiers_node:
        is_async = any(node_text(c, source) == "suspend" for c in modifiers_node.children)

    return_type = ""
    rt_node = find_child_by_type(node, "user_type")
    if rt_node:
        ti = find_child_by_type(rt_node, "type_identifier")
        if ti:
            return_type = node_text(ti, source).strip()

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


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "type_identifier")
    if name_node is None:
        name_node = find_child_by_type(node, "simple_identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    if node.type == "object_declaration":
        kind = "class"
    else:
        kind = "class"
        for child in node.children:
            txt = node_text(child, source)
            if txt == "interface":
                kind = "interface"
                break
            if txt == "enum":
                kind = "enum"
                break

    bases: list[str] = []
    for ds in find_children_by_type(node, "delegation_specifier"):
        ci = find_child_by_type(ds, "constructor_invocation")
        if ci:
            ut = find_child_by_type(ci, "user_type")
            if ut:
                ti = find_child_by_type(ut, "type_identifier")
                if ti:
                    bases.append(node_text(ti, source))
            continue
        ut = find_child_by_type(ds, "user_type")
        if ut:
            ti = find_child_by_type(ut, "type_identifier")
            if ti:
                bases.append(node_text(ti, source))

    attributes: list[str] = []

    pctor = find_child_by_type(node, "primary_constructor")
    if pctor:
        for cp in find_children_by_type(pctor, "class_parameter"):
            id_node = find_child_by_type(cp, "simple_identifier")
            if id_node:
                attributes.append(node_text(id_node, source))

    body = find_child_by_type(node, "class_body")
    if body:
        for prop in find_children_by_type(body, "property_declaration"):
            vd = find_child_by_type(prop, "variable_declaration")
            if vd:
                id_node = find_child_by_type(vd, "simple_identifier")
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


def _handle_import_list(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for header in find_children_by_type(node, "import_header"):
        id_node = find_child_by_type(header, "identifier")
        if id_node is None:
            continue
        module = node_text(id_node, source)
        alias = ""
        alias_node = find_child_by_type(header, "import_alias")
        if alias_node:
            ti = find_child_by_type(alias_node, "type_identifier")
            if ti:
                alias = node_text(ti, source)
        result.imports.append(
            ParsedImport(
                module=module,
                line_number=header.start_point[0] + 1,
                alias=alias,
            )
        )


def _handle_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    first = node.children[0] if node.children else None
    if first is None:
        return

    if first.type == "simple_identifier":
        name = node_text(first, source)
        result.calls.append(
            ParsedCall(
                name=name,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name=name,
            )
        )
    elif first.type == "navigation_expression":
        nav_suffix = find_child_by_type(first, "navigation_suffix")
        if nav_suffix:
            id_node = find_child_by_type(nav_suffix, "simple_identifier")
            if id_node:
                method_name = node_text(id_node, source)
                full = node_text(first, source)
                result.calls.append(
                    ParsedCall(
                        name=method_name,
                        line_number=node.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full,
                    )
                )

    for child in node.children:
        if child.type in ("call_suffix", "value_arguments"):
            _walk(child, source, result, class_context, caller)


def _handle_property(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    modifiers = find_child_by_type(node, "modifiers")
    is_const = False
    if modifiers:
        for child in modifiers.children:
            if node_text(child, source) == "const":
                is_const = True
                break
    if is_const:
        vd = find_child_by_type(node, "variable_declaration")
        if vd:
            id_node = find_child_by_type(vd, "simple_identifier")
            if id_node:
                result.variables.append(node_text(id_node, source))
