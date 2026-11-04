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
    "foreach_statement",
    "while_statement",
    "do_statement",
    "case_statement",
    "catch_clause",
    "conditional_expression",
    "binary_expression",
})


def _php_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body_node]
    while stack:
        n = stack.pop()
        if n.type == "binary_expression":
            for child in n.children:
                txt = node_text(child, source)
                if txt in ("&&", "||", "and", "or"):
                    complexity += 1
        elif n.type in _COMPLEXITY_NODES:
            complexity += 1
        for child in n.children:
            stack.append(child)
    return complexity


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type in ("simple_parameter", "variadic_parameter"):
            var_node = find_child_by_type(child, "variable_name")
            if var_node:
                name_node = find_child_by_type(var_node, "name")
                if name_node:
                    args.append(node_text(name_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev and prev.type == "comment":
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
    for child in node.children:
        if child.type == "attribute_list":
            for group in child.children:
                if group.type == "attribute_group":
                    for attr in group.children:
                        if attr.type == "attribute":
                            name_node = find_child_by_type(attr, "name")
                            if name_node:
                                decorators.append(node_text(name_node, source))
    return decorators


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func_node = find_child_by_type(call_node, "name")
    if func_node:
        name = node_text(func_node, source)
        return (name, name)
    qn = find_child_by_type(call_node, "qualified_name")
    if qn:
        name = node_text(qn, source)
        return (name, name)
    return ("", "")


def _extract_member_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    name_node = find_child_by_type(call_node, "name")
    if name_node is None:
        return ("", "")
    simple = node_text(name_node, source)
    obj_node = find_child_by_type(call_node, "variable_name")
    if obj_node:
        obj_name_node = find_child_by_type(obj_node, "name")
        if obj_name_node:
            obj_text = node_text(obj_name_node, source)
            return (simple, obj_text + "->" + simple)
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
        if child.type == "method_declaration":
            _handle_method(child, source, result, class_context)

        elif child.type == "function_definition":
            _handle_function(child, source, result, caller)

        elif child.type in (
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "trait_declaration",
        ):
            _handle_class(child, source, result)

        elif child.type == "namespace_use_declaration":
            _handle_use(child, source, result)

        elif child.type == "namespace_definition":
            pass

        elif child.type == "function_call_expression":
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
            args_node = find_child_by_type(child, "arguments")
            if args_node:
                _walk(args_node, source, result, class_context, caller)

        elif child.type == "member_call_expression":
            simple, full = _extract_member_call_name(child, source)
            if simple:
                result.calls.append(
                    ParsedCall(
                        name=simple,
                        line_number=child.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full,
                    )
                )
            args_node = find_child_by_type(child, "arguments")
            if args_node:
                _walk(args_node, source, result, class_context, caller)

        elif child.type == "scoped_call_expression":
            name_node = find_child_by_type(child, "name")
            if name_node:
                simple = node_text(name_node, source)
                result.calls.append(
                    ParsedCall(
                        name=simple,
                        line_number=child.start_point[0] + 1,
                        caller=caller,
                        full_call_name=simple,
                    )
                )
            args_node = find_child_by_type(child, "arguments")
            if args_node:
                _walk(args_node, source, result, class_context, caller)

        elif child.type == "object_creation_expression":
            _handle_new_expression(child, source, result, caller)

        elif child.type == "property_declaration" and class_context:
            _handle_property(child, source, result)

        elif child.child_count > 0 and child.type not in (
            "method_declaration",
            "function_definition",
            "class_declaration",
            "interface_declaration",
            "enum_declaration",
            "trait_declaration",
            "namespace_use_declaration",
            "string",
            "encapsed_string",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_method(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "name")
    name = node_text(name_node, source) if name_node else ""
    params = find_child_by_type(node, "formal_parameters")
    args = _extract_params(params, source) if params else []
    body = find_child_by_type(node, "compound_statement")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)
    complexity = _php_cyclomatic(body, source) if body else 1

    return_type = ""
    rt_node = find_child_by_type(node, "named_type")
    if rt_node is None:
        rt_node = find_child_by_type(node, "primitive_type")
    if rt_node is None:
        rt_node = find_child_by_type(node, "optional_type")
    if rt_node:
        return_type = node_text(rt_node, source).strip()

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


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    name_node = find_child_by_type(node, "name")
    name = node_text(name_node, source) if name_node else ""
    params = find_child_by_type(node, "formal_parameters")
    args = _extract_params(params, source) if params else []
    body = find_child_by_type(node, "compound_statement")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)
    complexity = _php_cyclomatic(body, source) if body else 1

    return_type = ""
    rt_node = find_child_by_type(node, "named_type")
    if rt_node is None:
        rt_node = find_child_by_type(node, "primitive_type")
    if rt_node is None:
        rt_node = find_child_by_type(node, "optional_type")
    if rt_node:
        return_type = node_text(rt_node, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=decorators,
            docstring=docstring,
            class_context="",
            cyclomatic_complexity=complexity,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context="", caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "name")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    kind_map = {
        "class_declaration": "class",
        "interface_declaration": "interface",
        "enum_declaration": "enum",
        "trait_declaration": "trait",
    }
    kind = kind_map.get(node.type, "class")

    bases: list[str] = []
    base_clause = find_child_by_type(node, "base_clause")
    if base_clause:
        for child in base_clause.children:
            if child.type in ("name", "qualified_name"):
                bases.append(node_text(child, source))

    iface_clause = find_child_by_type(node, "class_interface_clause")
    if iface_clause:
        for child in iface_clause.children:
            if child.type in ("name", "qualified_name"):
                bases.append(node_text(child, source))

    attributes: list[str] = []
    body = find_child_by_type(node, "declaration_list")
    if body is None:
        body = find_child_by_type(node, "enum_declaration_list")
    if body:
        for child in body.children:
            if child.type == "property_declaration":
                for sub in child.children:
                    if sub.type == "property_element":
                        var_node = find_child_by_type(sub, "variable_name")
                        if var_node:
                            n = find_child_by_type(var_node, "name")
                            if n:
                                attributes.append(node_text(n, source))

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


def _handle_use(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for child in node.children:
        if child.type == "namespace_use_clause":
            qn = find_child_by_type(child, "qualified_name")
            if qn is None:
                continue
            module = node_text(qn, source)
            alias_node = None
            saw_as = False
            for sub in child.children:
                if sub.type == "as":
                    saw_as = True
                elif saw_as and sub.type == "name":
                    alias_node = sub
                    break
            alias = node_text(alias_node, source) if alias_node else ""
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=node.start_point[0] + 1,
                    alias=alias,
                )
            )


def _handle_new_expression(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    name_node = find_child_by_type(node, "name")
    if name_node is None:
        name_node = find_child_by_type(node, "qualified_name")
    if name_node:
        name = node_text(name_node, source)
        result.calls.append(
            ParsedCall(
                name=name,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name="new " + name,
            )
        )
    args_node = find_child_by_type(node, "arguments")
    if args_node:
        _walk(args_node, source, result, class_context="", caller=caller)


def _handle_property(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    has_static = find_child_by_type(node, "static_modifier") is not None
    if has_static:
        for child in node.children:
            if child.type == "property_element":
                var_node = find_child_by_type(child, "variable_name")
                if var_node:
                    n = find_child_by_type(var_node, "name")
                    if n:
                        result.variables.append(node_text(n, source))
