from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    cyclomatic_complexity,
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
    "if",
    "unless",
    "while",
    "until",
    "for",
    "when",
    "rescue",
    "elsif",
})

_REQUIRE_NAMES: frozenset[str] = frozenset({"require", "require_relative"})
_ATTR_NAMES: frozenset[str] = frozenset({"attr_accessor", "attr_reader", "attr_writer"})


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "identifier":
            args.append(node_text(child, source))
        elif child.type in (
            "optional_parameter",
            "splat_parameter",
            "hash_splat_parameter",
            "keyword_parameter",
            "block_parameter",
        ):
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        stripped = text.lstrip("#").strip()
        if stripped:
            lines.append(stripped)
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _is_call_with_name(node: tree_sitter.Node, source: bytes, names: frozenset[str]) -> str | None:
    if node.type != "call":
        return None
    first = node.children[0] if node.children else None
    if first and first.type == "identifier":
        name = node_text(first, source)
        if name in names:
            return name
    return None


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
        if child.type in ("method", "singleton_method"):
            _handle_method(child, source, result, class_context)

        elif child.type == "class":
            _handle_class(child, source, result)

        elif child.type == "module":
            _handle_module(child, source, result)

        elif child.type == "call":
            req_name = _is_call_with_name(child, source, _REQUIRE_NAMES)
            if req_name:
                _handle_require(child, source, result)
            elif _is_call_with_name(child, source, _ATTR_NAMES):
                pass
            elif _is_call_with_name(child, source, frozenset({"include"})):
                _handle_include_import(child, source, result)
            else:
                _handle_call(child, source, result, class_context, caller)

        elif child.type == "assignment":
            _handle_assignment(child, source, result)
            _walk(child, source, result, class_context, caller)
            continue

        elif child.child_count > 0 and child.type not in (
            "method",
            "singleton_method",
            "class",
            "module",
            "string",
            "string_content",
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
    if not name:
        return

    params_node = find_child_by_type(node, "method_parameters")
    args = _extract_params(params_node, source) if params_node else []
    body = find_child_by_type(node, "body_statement")
    docstring = _extract_doc_comment(node, source)
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    result.functions.append(
        ParsedFunction(
            name=name,
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
        _walk(body, source, result, class_context, caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "constant")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    superclass = find_child_by_type(node, "superclass")
    if superclass:
        sc_const = find_child_by_type(superclass, "constant")
        if sc_const is None:
            sc_const = find_child_by_type(superclass, "scope_resolution")
        if sc_const:
            bases.append(node_text(sc_const, source))

    attributes: list[str] = []
    body = find_child_by_type(node, "body_statement")
    if body:
        for child in body.children:
            if child.type == "call":
                _extract_class_body_call(child, source, bases, attributes)

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

    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_module(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "constant")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)
    body = find_child_by_type(node, "body_statement")

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="module",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _extract_class_body_call(
    node: tree_sitter.Node,
    source: bytes,
    bases: list[str],
    attributes: list[str],
) -> None:
    first = node.children[0] if node.children else None
    if first is None or first.type != "identifier":
        return
    call_name = node_text(first, source)

    arg_list = find_child_by_type(node, "argument_list")
    if arg_list is None:
        return

    if call_name == "include":
        for arg in arg_list.children:
            if arg.type in ("constant", "scope_resolution"):
                bases.append(node_text(arg, source))

    elif call_name in _ATTR_NAMES:
        for arg in arg_list.children:
            if arg.type == "simple_symbol":
                text = node_text(arg, source)
                attributes.append(text.lstrip(":"))


def _handle_require(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    arg_list = find_child_by_type(node, "argument_list")
    if arg_list is None:
        return
    for arg in arg_list.children:
        if arg.type == "string":
            content = find_child_by_type(arg, "string_content")
            if content:
                module = node_text(content, source)
                result.imports.append(
                    ParsedImport(
                        module=module,
                        line_number=node.start_point[0] + 1,
                    )
                )


def _handle_include_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    arg_list = find_child_by_type(node, "argument_list")
    if arg_list is None:
        return
    for arg in arg_list.children:
        if arg.type in ("constant", "scope_resolution"):
            module = node_text(arg, source)
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=node.start_point[0] + 1,
                )
            )


def _handle_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    children = node.children
    if not children:
        return

    has_dot = any(c.type == "." for c in children)

    if has_dot:
        method_name = ""
        seen_dot = False
        for child in children:
            if child.type == ".":
                seen_dot = True
            elif seen_dot and child.type == "identifier":
                method_name = node_text(child, source)
                break
        if method_name:
            full = node_text(node, source).split("(")[0].split("\n")[0].strip()
            result.calls.append(
                ParsedCall(
                    name=method_name,
                    line_number=node.start_point[0] + 1,
                    caller=caller,
                    full_call_name=full,
                )
            )
    else:
        first = children[0]
        if first.type == "identifier":
            name = node_text(first, source)
            result.calls.append(
                ParsedCall(
                    name=name,
                    line_number=node.start_point[0] + 1,
                    caller=caller,
                    full_call_name=name,
                )
            )

    for child in children:
        if child.type == "call":
            req_name = _is_call_with_name(child, source, _REQUIRE_NAMES)
            if req_name:
                _handle_require(child, source, result)
            elif not _is_call_with_name(child, source, _ATTR_NAMES):
                _handle_call(child, source, result, class_context, caller)
        elif child.type == "argument_list":
            _walk(child, source, result, class_context, caller)


def _handle_assignment(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    first = node.children[0] if node.children else None
    if first and first.type == "constant":
        result.variables.append(node_text(first, source))
