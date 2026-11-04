from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    cyclomatic_complexity,
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
    "guard_statement",
    "switch_entry",
    "catch_keyword",
    "while_statement",
    "repeat_while_statement",
})


def _extract_params(node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in node.children:
        if child.type == "parameter":
            ids = find_children_by_type(child, "simple_identifier")
            if len(ids) >= 2:
                args.append(node_text(ids[1], source))
            elif len(ids) == 1:
                args.append(node_text(ids[0], source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("///"):
            lines.append(text[3:].strip())
            prev = prev.prev_named_sibling
        else:
            break
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    modifiers = find_child_by_type(node, "modifiers")
    if modifiers is None:
        return decorators
    for child in modifiers.children:
        if child.type == "attribute":
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

        elif child.type == "init_declaration":
            _handle_init(child, source, result, class_context)

        elif child.type == "class_declaration":
            _handle_class(child, source, result, class_context)

        elif child.type == "protocol_declaration":
            _handle_protocol(child, source, result)

        elif child.type == "import_declaration":
            _handle_import(child, source, result)

        elif child.type == "call_expression":
            _handle_call(child, source, result, class_context, caller)

        elif child.type == "property_declaration":
            _handle_property(child, source, result, class_context)
            _walk(child, source, result, class_context, caller)
            continue

        elif child.type == "protocol_function_declaration":
            _handle_protocol_function(child, source, result, class_context)

        elif child.child_count > 0 and child.type not in (
            "function_declaration",
            "init_declaration",
            "class_declaration",
            "protocol_declaration",
            "import_declaration",
            "line_string_literal",
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

    args = _extract_params(node, source)
    body = find_child_by_type(node, "function_body")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    is_async = any(node_text(c, source) == "async" for c in node.children)

    return_type = ""
    for child in node.children:
        if child.type == "type_annotation":
            ti = find_child_by_type(child, "user_type")
            if ti:
                return_type = node_text(ti, source).strip()
            else:
                tt = find_child_by_type(child, "tuple_type")
                if tt:
                    return_type = node_text(tt, source).strip()

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


def _handle_init(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    args = _extract_params(node, source)
    body = find_child_by_type(node, "function_body")
    docstring = _extract_doc_comment(node, source)
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    result.functions.append(
        ParsedFunction(
            name="init",
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )
    if body:
        _walk(body, source, result, class_context, caller="init")


def _handle_protocol_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "simple_identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    args = _extract_params(node, source)

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring="",
            class_context=class_context,
            cyclomatic_complexity=1,
            is_async=False,
            return_type="",
        )
    )


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    parent_class_context: str,
) -> None:
    kind = "class"
    for child in node.children:
        if child.type == "class":
            kind = "class"
            break
        if child.type == "struct":
            kind = "struct"
            break
        if child.type == "enum":
            kind = "enum"
            break
        if child.type == "extension":
            kind = "extension"
            break

    if kind == "extension":
        ut = find_child_by_type(node, "user_type")
        name_node = find_child_by_type(ut, "type_identifier") if ut else None
    else:
        name_node = find_child_by_type(node, "type_identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    for inh in find_children_by_type(node, "inheritance_specifier"):
        ut = find_child_by_type(inh, "user_type")
        if ut:
            ti = find_child_by_type(ut, "type_identifier")
            if ti:
                bases.append(node_text(ti, source))

    attributes: list[str] = []
    body = find_child_by_type(node, "class_body") or find_child_by_type(node, "enum_class_body")
    if body:
        for prop in find_children_by_type(body, "property_declaration"):
            if find_child_by_type(prop, "computed_property") is not None:
                continue
            pat = find_child_by_type(prop, "pattern")
            if pat:
                id_node = find_child_by_type(pat, "simple_identifier")
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


def _handle_protocol(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "type_identifier")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="protocol",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    body = find_child_by_type(node, "protocol_body")
    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    if id_node is None:
        return
    module = node_text(id_node, source)
    result.imports.append(
        ParsedImport(
            module=module,
            line_number=node.start_point[0] + 1,
            alias="",
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
    if class_context:
        return
    vbp = find_child_by_type(node, "value_binding_pattern")
    if vbp is None:
        return
    is_let = any(c.type == "let" for c in vbp.children)
    if not is_let:
        return
    pat = find_child_by_type(node, "pattern")
    if pat:
        id_node = find_child_by_type(pat, "simple_identifier")
        if id_node:
            result.variables.append(node_text(id_node, source))
