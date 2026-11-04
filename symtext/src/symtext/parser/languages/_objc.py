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
    "while_statement",
    "do_statement",
    "case_statement",
    "conditional_expression",
})


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("//"):
            stripped = text[2:].strip()
        elif text.startswith("/*"):
            stripped = text.strip("/*").strip()
        else:
            stripped = text.strip()
        if stripped:
            lines.append(stripped)
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _method_name(node: tree_sitter.Node, source: bytes) -> str:
    ids = find_children_by_type(node, "identifier")
    if ids:
        return node_text(ids[0], source)
    return ""


def _method_params(node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in node.children:
        if child.type == "method_parameter":
            ids = find_children_by_type(child, "identifier")
            if ids:
                args.append(node_text(ids[-1], source))
    return args


def _is_instance_method(node: tree_sitter.Node) -> bool:
    for child in node.children:
        if child.type == "-":
            return True
        if child.type == "+":
            return False
    return True


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for child in root.children:
        if child.type == "preproc_include":
            _handle_import(child, source, result)
        elif child.type == "class_interface":
            _handle_class_interface(child, source, result)
        elif child.type == "class_implementation":
            _handle_class_implementation(child, source, result)
        elif child.type == "protocol_declaration":
            _handle_protocol(child, source, result)
        elif child.type == "declaration":
            _handle_declaration(child, source, result)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    sys_lib = find_child_by_type(node, "system_lib_string")
    if sys_lib:
        module = node_text(sys_lib, source).strip("<>")
        result.imports.append(
            ParsedImport(
                module=module,
                line_number=node.start_point[0] + 1,
            )
        )
        return

    str_node = find_child_by_type(node, "string_literal")
    if str_node:
        content = find_child_by_type(str_node, "string_content")
        if content:
            result.imports.append(
                ParsedImport(
                    module=node_text(content, source),
                    line_number=node.start_point[0] + 1,
                )
            )


def _handle_class_interface(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    ids = find_children_by_type(node, "identifier")
    if not ids:
        return
    name = node_text(ids[0], source)
    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    if len(ids) >= 2:
        bases.append(node_text(ids[1], source))

    param_args = find_child_by_type(node, "parameterized_arguments")
    if param_args:
        for tn in find_children_by_type(param_args, "type_name"):
            tid = find_child_by_type(tn, "type_identifier")
            if tid:
                bases.append(node_text(tid, source))

    attributes: list[str] = []
    for child in node.children:
        if child.type == "property_declaration":
            struct_decl = find_child_by_type(child, "struct_declaration")
            if struct_decl:
                sd = find_child_by_type(struct_decl, "struct_declarator")
                if sd:
                    prop_id = find_child_by_type(sd, "identifier")
                    if prop_id is None:
                        ptr = find_child_by_type(sd, "pointer_declarator")
                        if ptr:
                            prop_id = find_child_by_type(ptr, "identifier")
                    if prop_id:
                        attributes.append(node_text(prop_id, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="class",
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_class_implementation(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    class_name = node_text(id_node, source) if id_node else ""

    for child in node.children:
        if child.type == "implementation_definition":
            method_def = find_child_by_type(child, "method_definition")
            if method_def:
                _handle_method(method_def, source, result, class_name)


def _handle_method(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name = _method_name(node, source)
    if not name:
        return

    args = _method_params(node, source)
    body = find_child_by_type(node, "compound_statement")
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    is_instance = _is_instance_method(node)
    decorators = [] if is_instance else ["classmethod"]

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=decorators,
            docstring="",
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )

    if body:
        _walk_calls(body, source, result, class_context, caller=name)


def _handle_protocol(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    ids = find_children_by_type(node, "identifier")
    if not ids:
        return
    name = node_text(ids[0], source)
    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    ref_list = find_child_by_type(node, "protocol_reference_list")
    if ref_list:
        for rid in find_children_by_type(ref_list, "identifier"):
            bases.append(node_text(rid, source))

    attributes: list[str] = []
    for child in node.children:
        if child.type == "method_declaration":
            mids = find_children_by_type(child, "identifier")
            if mids:
                attributes.append(node_text(mids[0], source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="protocol",
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_declaration(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    init_decl = find_child_by_type(node, "init_declarator")
    if init_decl:
        id_node = find_child_by_type(init_decl, "identifier")
        if id_node:
            result.variables.append(node_text(id_node, source))


def _walk_calls(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    stack: list[tree_sitter.Node] = [node]
    while stack:
        n = stack.pop()
        if n.type == "call_expression":
            _handle_c_call(n, source, result, caller)
        elif n.type == "message_expression":
            _handle_msg_call(n, source, result, caller)
        for child in n.children:
            stack.append(child)


def _handle_c_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    if id_node is None:
        return
    name = node_text(id_node, source)
    result.calls.append(
        ParsedCall(
            name=name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=name,
        )
    )


def _handle_msg_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    ids = find_children_by_type(node, "identifier")
    if len(ids) >= 2:
        receiver = node_text(ids[0], source)
        method = node_text(ids[1], source)
        result.calls.append(
            ParsedCall(
                name=method,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name=f"[{receiver} {method}]",
            )
        )
    elif len(ids) == 1:
        name = node_text(ids[0], source)
        result.calls.append(
            ParsedCall(
                name=name,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name=name,
            )
        )
