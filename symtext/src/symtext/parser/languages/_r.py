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
    "repeat_statement",
})

_IMPORT_FUNCTIONS: frozenset[str] = frozenset({"library", "require"})


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        stripped = text[2:].strip() if text.startswith("#'") else text.lstrip("#").strip()
        if stripped:
            lines.append(stripped)
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "parameter":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _call_name(node: tree_sitter.Node, source: bytes) -> str:
    first = node.children[0] if node.children else None
    if first is None:
        return ""
    if first.type == "identifier":
        return node_text(first, source)
    if first.type == "namespace_operator":
        return node_text(first, source)
    return ""


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    _walk(root, source, result, caller="")


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "binary_operator":
            _handle_binary_operator(child, source, result, caller)

        elif child.type == "call":
            _handle_call(child, source, result, caller)

        elif child.type in (
            "if_statement",
            "for_statement",
            "while_statement",
            "repeat_statement",
            "braced_expression",
        ):
            _walk(child, source, result, caller)


def _handle_binary_operator(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    children = node.children
    if len(children) < 3:
        return

    lhs = children[0]
    op = children[1]
    rhs = children[2]

    if op.type not in ("<-", "="):
        return

    if lhs.type != "identifier":
        return

    name = node_text(lhs, source)

    if rhs.type == "function_definition":
        _handle_function_def(node, name, rhs, source, result, caller)
    elif rhs.type == "call":
        call_fn = _call_name(rhs, source)
        short_name = call_fn.rsplit("::", 1)[-1] if "::" in call_fn else call_fn
        if short_name in ("R6Class", "setRefClass"):
            _handle_r6_class(node, name, rhs, source, result)
        else:
            if not caller:
                result.variables.append(name)
            _handle_call(rhs, source, result, caller)
    else:
        if not caller:
            result.variables.append(name)


def _handle_function_def(
    assign_node: tree_sitter.Node,
    name: str,
    func_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    params = find_child_by_type(func_node, "parameters")
    args = _extract_params(params, source) if params else []
    docstring = _extract_doc_comment(assign_node, source)
    body = find_child_by_type(func_node, "braced_expression")
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=assign_node.start_point[0] + 1,
            end_line_number=assign_node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context="",
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )
    if body:
        _walk(body, source, result, caller=name)


def _handle_r6_class(
    assign_node: tree_sitter.Node,
    name: str,
    call_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    docstring = _extract_doc_comment(assign_node, source)

    attributes: list[str] = []
    args_node = find_child_by_type(call_node, "arguments")
    if args_node:
        for arg in find_children_by_type(args_node, "argument"):
            id_node = find_child_by_type(arg, "identifier")
            if id_node:
                attr_name = node_text(id_node, source)
                if attr_name in ("public", "private", "active"):
                    list_call = find_child_by_type(arg, "call")
                    if list_call:
                        list_args = find_child_by_type(list_call, "arguments")
                        if list_args:
                            for la in find_children_by_type(list_args, "argument"):
                                la_id = find_child_by_type(la, "identifier")
                                if la_id:
                                    attributes.append(node_text(la_id, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=assign_node.start_point[0] + 1,
            end_line_number=assign_node.end_point[0] + 1,
            kind="class",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    name = _call_name(node, source)
    if not name:
        return

    short_name = name.rsplit("::", 1)[-1] if "::" in name else name

    if short_name in _IMPORT_FUNCTIONS:
        _handle_library_call(node, source, result)
        return

    if short_name == "source":
        _handle_source_call(node, source, result)
        return

    result.calls.append(
        ParsedCall(
            name=short_name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=name,
        )
    )

    args_node = find_child_by_type(node, "arguments")
    if args_node:
        _walk(args_node, source, result, caller)


def _handle_library_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    args_node = find_child_by_type(node, "arguments")
    if args_node is None:
        return
    for arg in find_children_by_type(args_node, "argument"):
        id_node = find_child_by_type(arg, "identifier")
        if id_node:
            result.imports.append(
                ParsedImport(
                    module=node_text(id_node, source),
                    line_number=node.start_point[0] + 1,
                )
            )
            return
        str_node = find_child_by_type(arg, "string")
        if str_node:
            content = find_child_by_type(str_node, "string_content")
            if content:
                result.imports.append(
                    ParsedImport(
                        module=node_text(content, source),
                        line_number=node.start_point[0] + 1,
                    )
                )
                return


def _handle_source_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    args_node = find_child_by_type(node, "arguments")
    if args_node is None:
        return
    for arg in find_children_by_type(args_node, "argument"):
        str_node = find_child_by_type(arg, "string")
        if str_node:
            content = find_child_by_type(str_node, "string_content")
            if content:
                result.imports.append(
                    ParsedImport(
                        module=node_text(content, source),
                        line_number=node.start_point[0] + 1,
                    )
                )
                return
