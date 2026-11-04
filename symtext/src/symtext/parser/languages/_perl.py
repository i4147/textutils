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
    "conditional_statement",
    "for_statement",
    "foreach_statement",
    "loop_statement",
    "unless_statement",
    "while_statement",
})


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


def _extract_sub_params(block: tree_sitter.Node, source: bytes) -> list[str]:
    for child in block.children:
        if child.type != "expression_statement":
            continue
        assign = find_child_by_type(child, "assignment_expression")
        if assign is None:
            continue
        rhs = assign.children[-1] if assign.children else None
        if rhs is None or rhs.type != "array":
            continue
        varname = find_child_by_type(rhs, "varname")
        if varname is None or node_text(varname, source) != "_":
            continue
        decl = find_child_by_type(assign, "variable_declaration")
        if decl is None:
            continue
        args: list[str] = []
        for sc in find_children_by_type(decl, "scalar"):
            vn = find_child_by_type(sc, "varname")
            if vn:
                args.append(node_text(vn, source))
        return args
    return []


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
        if child.type == "package_statement":
            _handle_package(child, source, result)

        elif child.type == "subroutine_declaration_statement":
            _handle_sub(child, source, result, class_context)

        elif child.type == "use_statement":
            _handle_use(child, source, result)

        elif child.type == "expression_statement":
            _handle_expression_statement(child, source, result, class_context, caller)

        elif child.type in (
            "conditional_statement",
            "for_statement",
            "foreach_statement",
            "loop_statement",
            "while_statement",
            "unless_statement",
        ) or (child.type == "block" and child.parent and child.parent.type != "subroutine_declaration_statement"):
            _walk(child, source, result, class_context, caller)


def _handle_package(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    pkgs = find_children_by_type(node, "package")
    if len(pkgs) < 2:
        return
    name = node_text(pkgs[1], source)
    if not name:
        return
    docstring = _extract_doc_comment(node, source)
    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="package",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )


def _handle_sub(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = find_child_by_type(node, "bareword")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    block = find_child_by_type(node, "block")
    args = _extract_sub_params(block, source) if block else []
    docstring = _extract_doc_comment(node, source)
    complexity = cyclomatic_complexity(block, _COMPLEXITY_NODES) if block else 1

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
    if block:
        _walk(block, source, result, class_context, caller=name)


def _handle_use(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    pkg_node = find_child_by_type(node, "package")
    if pkg_node is None:
        return
    module = node_text(pkg_node, source)

    qw_node = find_child_by_type(node, "quoted_word_list")
    if qw_node:
        content = find_child_by_type(qw_node, "string_content")
        if content:
            words = node_text(content, source).split()
            for word in words:
                result.imports.append(
                    ParsedImport(
                        module=module,
                        line_number=node.start_point[0] + 1,
                        imported_name=word,
                    )
                )
            return

    result.imports.append(
        ParsedImport(
            module=module,
            line_number=node.start_point[0] + 1,
        )
    )


def _handle_expression_statement(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "require_expression":
            _handle_require(child, source, result)
        elif child.type == "function_call_expression":
            _handle_function_call(child, source, result, caller)
        elif child.type == "method_call_expression":
            _handle_method_call(child, source, result, caller)
        elif child.type == "ambiguous_function_call_expression":
            _handle_ambiguous_call(child, source, result, caller)
        elif child.type == "assignment_expression":
            _handle_assignment(child, source, result, class_context, caller)


def _handle_require(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    str_node = find_child_by_type(node, "string_literal") or find_child_by_type(node, "interpolated_string_literal")
    if str_node is None:
        return
    content = find_child_by_type(str_node, "string_content")
    if content is None:
        return
    module = node_text(content, source)
    result.imports.append(
        ParsedImport(
            module=module,
            line_number=node.start_point[0] + 1,
        )
    )


def _handle_function_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    func_node = find_child_by_type(node, "function")
    if func_node is None:
        return
    full_name = node_text(func_node, source)
    name = full_name.rsplit("::", 1)[-1]
    result.calls.append(
        ParsedCall(
            name=name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=full_name,
        )
    )


def _handle_method_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    method_node = find_child_by_type(node, "method")
    if method_node is None:
        return
    method_name = node_text(method_node, source)
    full = node_text(node, source).split("(")[0].strip()
    result.calls.append(
        ParsedCall(
            name=method_name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=full,
        )
    )


def _handle_ambiguous_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    func_node = find_child_by_type(node, "function")
    if func_node is None:
        return
    name = node_text(func_node, source)
    result.calls.append(
        ParsedCall(
            name=name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=name,
        )
    )


def _handle_assignment(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    decl = find_child_by_type(node, "variable_declaration")
    if decl is None:
        return
    if caller:
        return
    scope = find_child_by_type(decl, "my") or find_child_by_type(decl, "our")
    if scope is None:
        return
    for sc in find_children_by_type(decl, "scalar"):
        vn = find_child_by_type(sc, "varname")
        if vn:
            result.variables.append(node_text(vn, source))

    for child in node.children:
        if child.type in ("function_call_expression", "method_call_expression"):
            if child.type == "function_call_expression":
                _handle_function_call(child, source, result, caller)
            else:
                _handle_method_call(child, source, result, caller)
