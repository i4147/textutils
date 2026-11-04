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
    "IfStatement",
    "IfExpr",
    "ForStatement",
    "ForExpr",
    "WhileStatement",
    "WhileExpr",
    "SwitchExpr",
    "catch",
    "orelse",
})


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev is not None and prev.type == "doc_comment":
        text = node_text(prev, source)
        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.lstrip("/").strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines) if lines else ""
    return ""


def _is_import(node: tree_sitter.Node) -> bool:
    expr = find_child_by_type(node, "ErrorUnionExpr")
    if expr is None:
        return False
    suffix = find_child_by_type(expr, "SuffixExpr")
    if suffix is None:
        return False
    builtin = find_child_by_type(suffix, "BUILTINIDENTIFIER")
    return builtin is not None and any(c.type == "@" for c in builtin.children)


def _import_string(node: tree_sitter.Node, source: bytes) -> str:
    expr = find_child_by_type(node, "ErrorUnionExpr")
    if expr is None:
        return ""
    suffix = find_child_by_type(expr, "SuffixExpr")
    if suffix is None:
        return ""
    fn_args = find_child_by_type(suffix, "FnCallArguments")
    if fn_args is None:
        return ""
    inner_expr = find_child_by_type(fn_args, "ErrorUnionExpr")
    if inner_expr is None:
        return ""
    inner_suffix = find_child_by_type(inner_expr, "SuffixExpr")
    if inner_suffix is None:
        return ""
    str_node = find_child_by_type(inner_suffix, "STRINGLITERALSINGLE")
    if str_node is None:
        return ""
    return node_text(str_node, source).strip('"')


def _extract_params(param_list: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in param_list.children:
        if child.type == "ParamDecl":
            id_node = find_child_by_type(child, "IDENTIFIER")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_container_fields(container: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    for child in container.children:
        if child.type == "ContainerField":
            id_node = find_child_by_type(child, "IDENTIFIER")
            if id_node:
                attrs.append(node_text(id_node, source))
            else:
                expr = find_child_by_type(child, "ErrorUnionExpr")
                if expr:
                    suffix = find_child_by_type(expr, "SuffixExpr")
                    if suffix:
                        eid = find_child_by_type(suffix, "IDENTIFIER")
                        if eid:
                            attrs.append(node_text(eid, source))
    return attrs


def _container_kind(container: tree_sitter.Node) -> str:
    decl_type = find_child_by_type(container, "ContainerDeclType")
    if decl_type is None:
        return "struct"
    for child in decl_type.children:
        if child.type in ("struct", "enum", "union"):
            return child.type
    return "struct"


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
        if child.type == "Decl":
            _handle_decl(child, source, result, class_context, caller)
        elif child.type == "pub":
            pass
        elif child.type == "doc_comment":
            pass
        elif child.child_count > 0 and child.type not in (
            "STRINGLITERALSINGLE",
            "STRINGLITERAL",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_decl(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    var_decl = find_child_by_type(node, "VarDecl")
    if var_decl:
        _handle_var_decl(var_decl, node, source, result, class_context)
        return

    fn_proto = find_child_by_type(node, "FnProto")
    if fn_proto:
        _handle_fn(fn_proto, node, source, result, class_context)
        return


def _handle_var_decl(
    var_decl: tree_sitter.Node,
    decl_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    id_node = find_child_by_type(var_decl, "IDENTIFIER")
    if id_node is None:
        return
    name = node_text(id_node, source)

    if _is_import(var_decl):
        module = _import_string(var_decl, source)
        if module:
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=var_decl.start_point[0] + 1,
                )
            )
        return

    expr = find_child_by_type(var_decl, "ErrorUnionExpr")
    if expr:
        suffix = find_child_by_type(expr, "SuffixExpr")
        if suffix:
            container = find_child_by_type(suffix, "ContainerDecl")
            if container:
                _handle_container(name, container, decl_node, source, result, class_context)
                return

    result.variables.append(name)


def _handle_container(
    name: str,
    container: tree_sitter.Node,
    decl_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    kind = _container_kind(container)
    parent = decl_node.parent if decl_node.parent else decl_node
    docstring = _extract_doc_comment(parent, source)
    if not docstring:
        docstring = _extract_doc_comment(decl_node, source)

    attributes = _extract_container_fields(container, source)

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=decl_node.start_point[0] + 1,
            end_line_number=decl_node.end_point[0] + 1,
            kind=kind,
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )

    _walk(container, source, result, class_context=name, caller=name)


def _handle_fn(
    fn_proto: tree_sitter.Node,
    decl_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    id_node = find_child_by_type(fn_proto, "IDENTIFIER")
    if id_node is None:
        return
    name = node_text(id_node, source)

    param_list = find_child_by_type(fn_proto, "ParamDeclList")
    args = _extract_params(param_list, source) if param_list else []

    parent = decl_node.parent if decl_node.parent else decl_node
    docstring = _extract_doc_comment(parent, source)
    if not docstring:
        docstring = _extract_doc_comment(decl_node, source)

    block = find_child_by_type(decl_node, "Block")
    complexity = cyclomatic_complexity(block, _COMPLEXITY_NODES) if block else 1

    return_type = ""
    rt_node = find_child_by_type(fn_proto, "SuffixExpr")
    if rt_node:
        rt_id = find_child_by_type(rt_node, "IDENTIFIER")
        if rt_id:
            return_type = node_text(rt_id, source).strip()
        else:
            builtin = find_child_by_type(rt_node, "BUILTINIDENTIFIER")
            if builtin:
                return_type = node_text(builtin, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=fn_proto.start_point[0] + 1,
            end_line_number=decl_node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type=return_type,
        )
    )

    if block:
        _walk_calls(block, source, result, class_context, caller=name)


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
        if n.type == "SuffixExpr":
            _maybe_record_call(n, source, result, caller)
        for child in n.children:
            stack.append(child)


def _maybe_record_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
) -> None:
    if find_child_by_type(node, "BUILTINIDENTIFIER"):
        return

    has_direct_call = find_child_by_type(node, "FnCallArguments") is not None
    has_field_call = False
    for child in node.children:
        if child.type == "FieldOrFnCall" and find_child_by_type(child, "FnCallArguments"):
            has_field_call = True
            break

    if not has_direct_call and not has_field_call:
        return

    parts: list[str] = []
    for child in node.children:
        if child.type == "IDENTIFIER":
            parts.append(node_text(child, source))
        elif child.type == "FieldOrFnCall":
            id_child = find_child_by_type(child, "IDENTIFIER")
            if id_child:
                parts.append(node_text(id_child, source))
            if find_child_by_type(child, "FnCallArguments"):
                break
        elif child.type == "FnCallArguments":
            break

    if not parts:
        return

    full_name = ".".join(parts)
    short_name = parts[-1]

    result.calls.append(
        ParsedCall(
            name=short_name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=full_name,
        )
    )
