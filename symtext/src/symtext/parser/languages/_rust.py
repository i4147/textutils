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
    "if_expression",
    "else_clause",
    "for_expression",
    "while_expression",
    "loop_expression",
    "match_arm",
    "binary_expression",
})


def _rust_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
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
        if child.type == "parameter":
            pat = child.child_by_field_name("pattern")
            if pat:
                args.append(node_text(pat, source))
        elif child.type == "self_parameter":
            args.append(node_text(child, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev and prev.type == "attribute_item":
        prev = prev.prev_named_sibling
    while prev and prev.type == "line_comment":
        text = node_text(prev, source)
        if text.startswith("///"):
            lines.append(text[3:].strip())
        else:
            break
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_attributes(node: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    prev = node.prev_named_sibling
    while prev and prev.type == "attribute_item":
        attr = find_child_by_type(prev, "attribute")
        if attr:
            id_node = find_child_by_type(attr, "identifier")
            if id_node:
                token_tree = find_child_by_type(attr, "token_tree")
                if token_tree:
                    attrs.append(node_text(id_node, source) + node_text(token_tree, source))
                else:
                    attrs.append(node_text(id_node, source))
        prev = prev.prev_named_sibling
    attrs.reverse()
    return attrs


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func = call_node.child_by_field_name("function")
    if func is None:
        return ("", "")
    full_name = node_text(func, source)
    if func.type == "identifier":
        return (full_name, full_name)
    if func.type == "field_expression":
        field = func.child_by_field_name("field")
        if field:
            return (node_text(field, source), full_name)
    if func.type == "scoped_identifier":
        name = func.child_by_field_name("name")
        if name:
            return (node_text(name, source), full_name)
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
        if child.type in ("static_item", "const_item"):
            name_node = child.child_by_field_name("name")
            if name_node is None:
                name_node = find_child_by_type(child, "identifier")
            if name_node:
                result.variables.append(node_text(name_node, source))


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "function_item":
            _handle_function(child, source, result, class_context)

        elif child.type in ("struct_item", "enum_item"):
            _handle_struct_or_enum(child, source, result)

        elif child.type == "trait_item":
            _handle_trait(child, source, result)

        elif child.type == "impl_item":
            _handle_impl(child, source, result)

        elif child.type == "use_declaration":
            _handle_use(child, source, result)

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

        elif child.type == "macro_invocation":
            macro = child.child_by_field_name("macro")
            if macro:
                name = node_text(macro, source)
                result.calls.append(
                    ParsedCall(
                        name=name + "!",
                        line_number=child.start_point[0] + 1,
                        caller=caller,
                        full_call_name=name + "!",
                    )
                )

        elif child.type == "expression_statement" or (
            child.child_count > 0
            and child.type
            not in (
                "function_item",
                "struct_item",
                "enum_item",
                "trait_item",
                "impl_item",
                "use_declaration",
                "string_literal",
                "raw_string_literal",
            )
        ):
            _walk(child, source, result, class_context, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    params = node.child_by_field_name("parameters")
    args = _extract_params(params, source) if params else []
    body = node.child_by_field_name("body")
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_attributes(node, source)
    complexity = _rust_cyclomatic(body, source) if body else 1

    is_async = any(c.type == "async" for c in node.children)

    return_type = ""
    rt_node = node.child_by_field_name("return_type")
    if rt_node:
        return_type = node_text(rt_node, source).lstrip("- >").strip()

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


def _handle_struct_or_enum(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    docstring = _extract_doc_comment(node, source)
    kind = "struct" if node.type == "struct_item" else "enum"

    attributes: list[str] = []
    if node.type == "struct_item":
        fields = find_child_by_type(node, "field_declaration_list")
        if fields:
            for field in fields.children:
                if field.type == "field_declaration":
                    id_node = find_child_by_type(field, "field_identifier")
                    if id_node:
                        attributes.append(node_text(id_node, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind=kind,
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_trait(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    docstring = _extract_doc_comment(node, source)

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="trait",
            docstring=docstring,
        )
    )


def _handle_impl(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    impl_type = node.child_by_field_name("type")
    class_context = node_text(impl_type, source) if impl_type else ""

    trait_node = node.child_by_field_name("trait")
    if trait_node:
        trait_name = node_text(trait_node, source)
        for cls in result.classes:
            if cls.name == class_context:
                if trait_name not in cls.bases:
                    cls.bases.append(trait_name)
                break

    body = node.child_by_field_name("body")
    if body:
        _walk(body, source, result, class_context=class_context, caller=class_context)


def _handle_use(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    line = node.start_point[0] + 1

    for child in node.children:
        if child.type in ("use", ";"):
            continue
        _walk_use_path(child, source, result, line, prefix="")


def _walk_use_path(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    line: int,
    prefix: str,
) -> None:
    if node.type == "identifier":
        module = prefix.removesuffix("::") if prefix else node_text(node, source)
        name = node_text(node, source) if prefix else ""
        result.imports.append(
            ParsedImport(
                module=module,
                line_number=line,
                imported_name=name,
            )
        )
    elif node.type == "scoped_identifier":
        full = node_text(node, source)
        parts = full.rsplit("::", 1)
        module = parts[0] if len(parts) > 1 else full
        imported = parts[1] if len(parts) > 1 else ""
        result.imports.append(
            ParsedImport(
                module=module,
                line_number=line,
                imported_name=imported,
            )
        )
    elif node.type == "scoped_use_list":
        path_node = find_child_by_type(node, "scoped_identifier")
        if path_node is None:
            path_node = find_child_by_type(node, "identifier")
        if path_node is None:
            path_node = find_child_by_type(node, "crate")
        base = node_text(path_node, source) if path_node else ""

        use_list = find_child_by_type(node, "use_list")
        if use_list:
            for child in use_list.children:
                if child.type == "identifier":
                    result.imports.append(
                        ParsedImport(
                            module=base,
                            line_number=line,
                            imported_name=node_text(child, source),
                        )
                    )
                elif child.type in ("scoped_identifier", "scoped_use_list", "use_as_clause"):
                    _walk_use_path(child, source, result, line, base + "::")
    elif node.type == "use_as_clause":
        path = node.child_by_field_name("path")
        alias = node.child_by_field_name("alias")
        if path:
            module = prefix.removesuffix("::") if prefix else ""
            result.imports.append(
                ParsedImport(
                    module=module if module else node_text(path, source),
                    line_number=line,
                    imported_name=node_text(path, source) if module else "",
                    alias=node_text(alias, source) if alias else "",
                )
            )
