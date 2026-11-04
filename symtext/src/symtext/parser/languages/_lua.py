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
    ParsedFunction,
    ParsedImport,
)

_COMPLEXITY_NODES: frozenset[str] = frozenset({
    "if_statement",
    "for_statement",
    "while_statement",
    "repeat_statement",
})


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "identifier":
            args.append(node_text(child, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "comment":
        text = node_text(prev, source)
        content = prev.children[0] if prev.children else None
        if content and content.type == "comment_content":
            ct = node_text(content, source)
            if ct.startswith("-"):
                lines.append(ct[1:].strip())
                prev = prev.prev_named_sibling
                continue
        if text.startswith("---"):
            lines.append(text[3:].strip())
            prev = prev.prev_named_sibling
            continue
        break
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


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
            _handle_function(child, source, result, caller)

        elif child.type == "variable_declaration":
            _handle_variable_declaration(child, source, result, caller)

        elif child.type == "function_call":
            _handle_call(child, source, result, class_context, caller)

        elif child.child_count > 0 and child.type not in (
            "function_declaration",
            "string",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    name = ""
    func_class_context = ""

    dot_expr = find_child_by_type(node, "dot_index_expression")
    if dot_expr:
        ids = find_children_by_type(dot_expr, "identifier")
        if len(ids) >= 2:
            func_class_context = node_text(ids[0], source)
            name = node_text(ids[1], source)
        elif ids:
            name = node_text(ids[0], source)
    else:
        method_expr = find_child_by_type(node, "method_index_expression")
        if method_expr:
            ids = find_children_by_type(method_expr, "identifier")
            if len(ids) >= 2:
                func_class_context = node_text(ids[0], source)
                name = node_text(ids[1], source)
            elif ids:
                name = node_text(ids[0], source)
        else:
            id_node = find_child_by_type(node, "identifier")
            if id_node:
                name = node_text(id_node, source)

    if not name:
        return

    params_node = find_child_by_type(node, "parameters")
    args = _extract_params(params_node, source) if params_node else []
    docstring = _extract_doc_comment(node, source)
    body = find_child_by_type(node, "block")
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=func_class_context,
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )
    if body:
        _walk(body, source, result, func_class_context, caller=name)


def _handle_variable_declaration(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    assign = find_child_by_type(node, "assignment_statement")
    if assign is None:
        vlist = find_child_by_type(node, "variable_list")
        if vlist:
            for vid in find_children_by_type(vlist, "identifier"):
                result.variables.append(node_text(vid, source))
        return

    expr_list = find_child_by_type(assign, "expression_list")
    if expr_list is None:
        return

    func_call = find_child_by_type(expr_list, "function_call")
    if func_call:
        callee_id = find_child_by_type(func_call, "identifier")
        if callee_id and node_text(callee_id, source) == "require":
            _handle_require(node, func_call, source, result)
            return

    func_def = find_child_by_type(expr_list, "function_definition")
    if func_def:
        vlist = find_child_by_type(node, "variable_list")
        if not vlist:
            vlist = find_child_by_type(assign, "variable_list")
        if vlist:
            id_node = find_child_by_type(vlist, "identifier")
            if id_node:
                name = node_text(id_node, source)
                params_node = find_child_by_type(func_def, "parameters")
                args = _extract_params(params_node, source) if params_node else []
                body = find_child_by_type(func_def, "block")
                complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

                result.functions.append(
                    ParsedFunction(
                        name=name,
                        line_number=node.start_point[0] + 1,
                        end_line_number=node.end_point[0] + 1,
                        args=args,
                        decorators=[],
                        docstring=_extract_doc_comment(node, source),
                        class_context="",
                        cyclomatic_complexity=complexity,
                        is_async=False,
                        return_type="",
                    )
                )
                if body:
                    _walk(body, source, result, "", caller=name)
        return

    vlist = find_child_by_type(node, "variable_list")
    if not vlist:
        vlist = find_child_by_type(assign, "variable_list")
    if vlist:
        for vid in find_children_by_type(vlist, "identifier"):
            result.variables.append(node_text(vid, source))

    _walk(expr_list, source, result, "", caller)


def _handle_require(
    var_node: tree_sitter.Node,
    call_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    args_node = find_child_by_type(call_node, "arguments")
    if args_node is None:
        return
    for child in args_node.children:
        if child.type == "string":
            sc = find_child_by_type(child, "string_content")
            module = node_text(sc, source) if sc else node_text(child, source).strip("'\"")
            alias = ""
            assign = find_child_by_type(var_node, "assignment_statement")
            vlist = find_child_by_type(assign, "variable_list") if assign else None
            if vlist is None:
                vlist = find_child_by_type(var_node, "variable_list")
            if vlist:
                id_node = find_child_by_type(vlist, "identifier")
                if id_node:
                    alias = node_text(id_node, source)
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=var_node.start_point[0] + 1,
                    alias=alias,
                )
            )
            return


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

    if first.type == "identifier":
        name = node_text(first, source)
        if name == "require":
            return
        result.calls.append(
            ParsedCall(
                name=name,
                line_number=node.start_point[0] + 1,
                caller=caller,
                full_call_name=name,
            )
        )
    elif first.type == "method_index_expression":
        ids = find_children_by_type(first, "identifier")
        if len(ids) >= 2:
            obj_name = node_text(ids[0], source)
            method_name = node_text(ids[1], source)
            result.calls.append(
                ParsedCall(
                    name=method_name,
                    line_number=node.start_point[0] + 1,
                    caller=caller,
                    full_call_name=f"{obj_name}:{method_name}",
                )
            )
    elif first.type == "dot_index_expression":
        # table.func()
        ids = find_children_by_type(first, "identifier")
        if len(ids) >= 2:
            obj_name = node_text(ids[0], source)
            method_name = node_text(ids[1], source)
            result.calls.append(
                ParsedCall(
                    name=method_name,
                    line_number=node.start_point[0] + 1,
                    caller=caller,
                    full_call_name=f"{obj_name}.{method_name}",
                )
            )

    args = find_child_by_type(node, "arguments")
    if args:
        _walk(args, source, result, class_context, caller)
