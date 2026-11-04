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
    "stab_clause",
})

_DEF_KEYWORDS: frozenset[str] = frozenset({
    "defmodule",
    "def",
    "defp",
    "defprotocol",
    "defimpl",
    "defstruct",
    "defmacro",
    "defmacrop",
    "defguard",
    "defdelegate",
    "alias",
    "import",
    "require",
    "use",
    "if",
    "unless",
    "case",
    "cond",
    "for",
    "with",
})

_COMPLEXITY_KEYWORDS: frozenset[str] = frozenset({"if", "unless", "case", "cond", "for", "with"})


def _call_identifier(node: tree_sitter.Node, source: bytes) -> str | None:
    if node.type != "call":
        return None
    first = node.children[0] if node.children else None
    if first and first.type == "identifier":
        return node_text(first, source)
    return None


def _extract_string_content(node: tree_sitter.Node, source: bytes) -> str:
    qc = find_child_by_type(node, "quoted_content")
    if qc:
        return node_text(qc, source).strip()
    return ""


def _extract_doc(attr_node: tree_sitter.Node, source: bytes) -> str:
    call_node = find_child_by_type(attr_node, "call")
    if call_node is None:
        return ""
    id_node = find_child_by_type(call_node, "identifier")
    if id_node is None:
        return ""
    name = node_text(id_node, source)
    if name not in ("doc", "moduledoc"):
        return ""
    args = find_child_by_type(call_node, "arguments")
    if args is None:
        return ""
    string_node = find_child_by_type(args, "string")
    if string_node:
        return _extract_string_content(string_node, source)
    return ""


def _extract_params(inner_call: tree_sitter.Node, source: bytes) -> list[str]:
    args_node = find_child_by_type(inner_call, "arguments")
    if args_node is None:
        return []
    params: list[str] = []
    for child in args_node.children:
        if child.type == "identifier":
            params.append(node_text(child, source))
        elif child.type == "binary_operator":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                params.append(node_text(id_node, source))
    return params


def _extract_fn_name_and_params(def_node: tree_sitter.Node, source: bytes) -> tuple[str, list[str]]:
    args = find_child_by_type(def_node, "arguments")
    if args is None:
        return "", []

    for child in args.children:
        if child.type == "call":
            id_node = find_child_by_type(child, "identifier")
            name = node_text(id_node, source) if id_node else ""
            return name, _extract_params(child, source)
        if child.type == "binary_operator":
            inner_call = find_child_by_type(child, "call")
            if inner_call:
                id_node = find_child_by_type(inner_call, "identifier")
                name = node_text(id_node, source) if id_node else ""
                return name, _extract_params(inner_call, source)
    return "", []


def _pending_doc(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev is not None and prev.type == "unary_operator":
        return _extract_doc(prev, source)
    return ""


def _elixir_complexity(body: tree_sitter.Node, source: bytes) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body]
    while stack:
        n = stack.pop()
        if n.type in _COMPLEXITY_NODES:
            complexity += 1
        elif n.type == "call":
            cid = _call_identifier(n, source)
            if cid in _COMPLEXITY_KEYWORDS:
                complexity += 1
        elif n.type == "binary_operator":
            for c in n.children:
                if c.type == "when":
                    complexity += 1
                    break
        for child in n.children:
            stack.append(child)
    return complexity


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
        if child.type == "call":
            _dispatch_call(child, source, result, class_context, caller)

        elif child.type == "unary_operator":
            _handle_attribute(child, source, result, class_context)

        elif child.type == "binary_operator":
            _handle_binary_op(child, source, result, class_context, caller)

        elif child.child_count > 0 and child.type not in ("string",):
            _walk(child, source, result, class_context, caller)


def _dispatch_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    cid = _call_identifier(node, source)

    if cid == "defmodule":
        _handle_defmodule(node, source, result, "module")
    elif cid == "defprotocol":
        _handle_defmodule(node, source, result, "protocol")
    elif cid == "defimpl":
        _handle_defimpl(node, source, result)
    elif cid in ("def", "defp"):
        _handle_def(node, source, result, class_context, caller)
    elif cid == "defstruct":
        _handle_defstruct(node, source, result, class_context)
    elif cid in ("import", "alias", "require", "use"):
        _handle_import_like(node, source, result, cid)
    elif cid in _COMPLEXITY_KEYWORDS:
        do_block = find_child_by_type(node, "do_block")
        if do_block:
            _walk(do_block, source, result, class_context, caller)
        args = find_child_by_type(node, "arguments")
        if args:
            _walk(args, source, result, class_context, caller)
    elif cid is not None:
        _record_call(node, source, result, caller, cid, cid)
        _walk_call_args(node, source, result, class_context, caller)
    else:
        _handle_dot_call(node, source, result, class_context, caller)


def _handle_defmodule(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    kind: str,
) -> None:
    args = find_child_by_type(node, "arguments")
    if args is None:
        return
    alias_node = find_child_by_type(args, "alias")
    name = node_text(alias_node, source) if alias_node else ""
    if not name:
        return

    docstring = ""
    do_block = find_child_by_type(node, "do_block")
    if do_block:
        for child in do_block.children:
            if child.type == "unary_operator":
                doc = _extract_doc(child, source)
                if doc:
                    docstring = doc
                    break

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind=kind,
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    if do_block:
        _walk(do_block, source, result, class_context=name, caller=name)


def _handle_defimpl(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    args = find_child_by_type(node, "arguments")
    if args is None:
        return
    alias_node = find_child_by_type(args, "alias")
    name = node_text(alias_node, source) if alias_node else ""
    if not name:
        return

    bases: list[str] = []
    kw = find_child_by_type(args, "keywords")
    if kw:
        for pair in find_children_by_type(kw, "pair"):
            kw_node = find_child_by_type(pair, "keyword")
            if kw_node and node_text(kw_node, source).startswith("for"):
                val = find_child_by_type(pair, "alias")
                if val:
                    bases.append(node_text(val, source))

    impl_name = f"{name}"
    result.classes.append(
        ParsedClass(
            name=impl_name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="impl",
            bases=bases,
            attributes=[],
            docstring="",
        )
    )

    do_block = find_child_by_type(node, "do_block")
    if do_block:
        _walk(do_block, source, result, class_context=impl_name, caller=impl_name)


def _handle_def(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    name, params = _extract_fn_name_and_params(node, source)
    if not name:
        return

    docstring = _pending_doc(node, source)
    do_block = find_child_by_type(node, "do_block")
    complexity = _elixir_complexity(do_block, source) if do_block else 1

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=params,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )

    if do_block:
        _walk(do_block, source, result, class_context, caller=name)


def _handle_defstruct(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    args = find_child_by_type(node, "arguments")
    if args is None:
        return
    list_node = find_child_by_type(args, "list")
    if list_node is None:
        return
    for child in list_node.children:
        if child.type == "atom":
            text = node_text(child, source).lstrip(":")
            if text:
                for cls in reversed(result.classes):
                    if cls.name == class_context:
                        cls.attributes.append(text)
                        break


def _handle_import_like(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    kind: str,
) -> None:
    args = find_child_by_type(node, "arguments")
    if args is None:
        return
    alias_node = find_child_by_type(args, "alias")
    if alias_node is None:
        return
    module = node_text(alias_node, source)

    result.imports.append(
        ParsedImport(
            module=module,
            line_number=node.start_point[0] + 1,
            alias=kind,
        )
    )


def _handle_attribute(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    call_node = find_child_by_type(node, "call")
    if call_node is None:
        return
    id_node = find_child_by_type(call_node, "identifier")
    if id_node is None:
        return
    attr_name = node_text(id_node, source)

    if attr_name in ("doc", "moduledoc"):
        return

    if attr_name in ("behaviour", "behavior", "spec", "type", "typep", "opaque", "callback"):
        result.variables.append(f"@{attr_name}")
        return

    result.variables.append(f"@{attr_name}")


def _handle_binary_op(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    has_pipe = any(c.type == "|>" for c in node.children)
    if has_pipe:
        _handle_pipe(node, source, result, class_context, caller)
    else:
        _walk(node, source, result, class_context, caller)


def _handle_pipe(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "|>":
            continue
        if child.type == "call":
            _dispatch_call(child, source, result, class_context, caller)
        elif child.type == "binary_operator":
            _handle_binary_op(child, source, result, class_context, caller)
        elif child.child_count > 0:
            _walk(child, source, result, class_context, caller)


def _handle_dot_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    dot_node = find_child_by_type(node, "dot")
    if dot_node is None:
        return
    id_node = find_child_by_type(dot_node, "identifier")
    if id_node is None:
        return
    method_name = node_text(id_node, source)
    full_name = node_text(dot_node, source)

    _record_call(node, source, result, caller, method_name, full_name)
    _walk_call_args(node, source, result, class_context, caller)


def _record_call(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    caller: str,
    name: str,
    full_call_name: str,
) -> None:
    result.calls.append(
        ParsedCall(
            name=name,
            line_number=node.start_point[0] + 1,
            caller=caller,
            full_call_name=full_call_name,
        )
    )


def _walk_call_args(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    args = find_child_by_type(node, "arguments")
    if args:
        _walk(args, source, result, class_context, caller)
    do_block = find_child_by_type(node, "do_block")
    if do_block:
        _walk(do_block, source, result, class_context, caller)
