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
    "expression_switch_statement",
    "switch_case",
    "default_case",
    "type_switch_statement",
    "select_statement",
    "communication_case",
    "binary_expression",
})


def _go_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
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
        if child.type == "parameter_declaration":
            for sub in child.children:
                if sub.type == "identifier":
                    args.append(node_text(sub, source))
        elif child.type == "variadic_parameter_declaration":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append("..." + node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("//"):
            lines.append(text[2:].strip())
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func = call_node.child_by_field_name("function")
    if func is None:
        return ("", "")
    full_name = node_text(func, source)
    if func.type == "identifier":
        return (full_name, full_name)
    if func.type == "selector_expression":
        field = func.child_by_field_name("field")
        if field:
            return (node_text(field, source), full_name)
    return (full_name, full_name)


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    _extract_variables(root, source, result)
    _walk(root, source, result, class_context="", caller="")


def _extract_variables(root: tree_sitter.Node, source: bytes, result: FileParseResult) -> None:
    for child in root.children:
        if child.type == "var_declaration":
            for spec in child.children:
                if spec.type == "var_spec":
                    for sub in spec.children:
                        if sub.type == "identifier":
                            result.variables.append(node_text(sub, source))
                            break
        elif child.type == "short_var_declaration":
            left = child.child_by_field_name("left")
            if left:
                for sub in left.children:
                    if sub.type == "identifier":
                        result.variables.append(node_text(sub, source))


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "function_declaration":
            _handle_function(child, source, result)

        elif child.type == "method_declaration":
            _handle_method(child, source, result)

        elif child.type == "type_declaration":
            _handle_type_decl(child, source, result)

        elif child.type == "import_declaration":
            _handle_import(child, source, result)

        elif child.type == "call_expression":
            simple_name, full_name = _extract_call_name(child, source)
            if simple_name:
                result.calls.append(
                    ParsedCall(
                        name=simple_name,
                        line_number=child.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full_name,
                    )
                )
            args = child.child_by_field_name("arguments")
            if args:
                _walk(args, source, result, class_context, caller)

        elif child.type in (
            "expression_statement",
            "block",
            "statement_list",
        ) or (
            child.child_count > 0
            and child.type
            not in (
                "function_declaration",
                "method_declaration",
                "type_declaration",
                "import_declaration",
                "interpreted_string_literal",
                "raw_string_literal",
            )
        ):
            _walk(child, source, result, class_context, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    params = node.child_by_field_name("parameters")
    args = _extract_params(params, source) if params else []
    body = node.child_by_field_name("body")
    docstring = _extract_doc_comment(node, source)
    complexity = _go_cyclomatic(body, source) if body else 1

    return_type = ""
    rt_node = node.child_by_field_name("result")
    if rt_node:
        return_type = node_text(rt_node, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            docstring=docstring,
            cyclomatic_complexity=complexity,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context="", caller=name)


def _handle_method(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""

    receiver_class = ""
    params_list = find_children_by_type(node, "parameter_list")
    if params_list:
        receiver_params = params_list[0]
        for decl in receiver_params.children:
            if decl.type == "parameter_declaration":
                for sub in decl.children:
                    if sub.type == "pointer_type":
                        inner = find_child_by_type(sub, "type_identifier")
                        if inner:
                            receiver_class = node_text(inner, source)
                    elif sub.type == "type_identifier":
                        receiver_class = node_text(sub, source)

    method_params = params_list[1] if len(params_list) > 1 else None
    args = _extract_params(method_params, source) if method_params else []
    body = node.child_by_field_name("body")
    docstring = _extract_doc_comment(node, source)
    complexity = _go_cyclomatic(body, source) if body else 1

    return_type = ""
    rt_node = node.child_by_field_name("result")
    if rt_node:
        return_type = node_text(rt_node, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            docstring=docstring,
            class_context=receiver_class,
            cyclomatic_complexity=complexity,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context=receiver_class, caller=name)


def _handle_type_decl(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for spec in node.children:
        if spec.type != "type_spec":
            continue
        name_node = find_child_by_type(spec, "type_identifier")
        name = node_text(name_node, source) if name_node else ""
        docstring = _extract_doc_comment(node, source)

        struct = find_child_by_type(spec, "struct_type")
        if struct:
            attrs: list[str] = []
            fields = find_child_by_type(struct, "field_declaration_list")
            if fields:
                for field in fields.children:
                    if field.type == "field_declaration":
                        id_node = find_child_by_type(field, "field_identifier")
                        if id_node:
                            attrs.append(node_text(id_node, source))
            result.classes.append(
                ParsedClass(
                    name=name,
                    line_number=node.start_point[0] + 1,
                    end_line_number=node.end_point[0] + 1,
                    kind="struct",
                    attributes=attrs,
                    docstring=docstring,
                )
            )
            continue

        iface = find_child_by_type(spec, "interface_type")
        if iface:
            result.classes.append(
                ParsedClass(
                    name=name,
                    line_number=node.start_point[0] + 1,
                    end_line_number=node.end_point[0] + 1,
                    kind="interface",
                    docstring=docstring,
                )
            )


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:

    def _process_spec(spec: tree_sitter.Node) -> None:
        str_node = find_child_by_type(spec, "interpreted_string_literal")
        if str_node is None:
            return
        content = find_child_by_type(str_node, "interpreted_string_literal_content")
        module = node_text(content, source) if content else node_text(str_node, source).strip('"')

        alias = ""
        name_node = find_child_by_type(spec, "package_identifier")
        if name_node is None:
            name_node = find_child_by_type(spec, "dot")
        if name_node:
            alias = node_text(name_node, source)

        result.imports.append(ParsedImport(module=module, line_number=spec.start_point[0] + 1, alias=alias))

    spec_list = find_child_by_type(node, "import_spec_list")
    if spec_list:
        for spec in spec_list.children:
            if spec.type == "import_spec":
                _process_spec(spec)
    else:
        single_spec = find_child_by_type(node, "import_spec")
        if single_spec:
            _process_spec(single_spec)
