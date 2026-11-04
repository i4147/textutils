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
    "if_expression",
    "for_expression",
    "while_expression",
    "match_expression",
    "case_clause",
    "catch_clause",
})


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "parameter":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_class_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type == "class_parameter":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev is None:
        return ""
    if prev.type not in ("block_comment", "comment"):
        return ""
    text = node_text(prev, source)
    if not text.startswith("/**"):
        return ""
    inner = text[3:]
    if inner.endswith("*/"):
        inner = inner[:-2]
    lines: list[str] = []
    for line in inner.split("\n"):
        stripped = line.strip().lstrip("* ").strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    for child in node.children:
        if child.type == "annotation":
            for ac in child.children:
                if ac.type in ("type_identifier", "identifier"):
                    decorators.append(node_text(ac, source))
                    break
    return decorators


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
        if child.type == "class_definition":
            _handle_class(child, source, result)

        elif child.type == "trait_definition":
            _handle_trait(child, source, result)

        elif child.type == "object_definition":
            _handle_object(child, source, result)

        elif child.type == "enum_definition":
            _handle_enum(child, source, result)

        elif child.type == "function_definition":
            _handle_function(child, source, result, class_context)

        elif child.type == "function_declaration":
            _handle_function_decl(child, source, result, class_context)

        elif child.type == "import_declaration":
            _handle_import(child, source, result)

        elif child.type == "call_expression":
            _handle_call(child, source, result, class_context, caller)

        elif child.type == "val_definition" or child.type == "var_definition":
            _handle_val(child, source, result, class_context, caller)

        elif child.child_count > 0 and child.type not in (
            "class_definition",
            "trait_definition",
            "object_definition",
            "enum_definition",
            "function_definition",
            "function_declaration",
            "import_declaration",
            "string",
        ):
            _walk(child, source, result, class_context, caller)


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    params_node = find_child_by_type(node, "parameters")
    args = _extract_params(params_node, source) if params_node else []
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)

    body = find_child_by_type(node, "block")
    if body is None:
        body = find_child_by_type(node, "indented_block")
    complexity = cyclomatic_complexity(body, _COMPLEXITY_NODES) if body else 1

    return_type = ""
    rt_node = find_child_by_type(node, "type_identifier")
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


def _handle_function_decl(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    params_node = find_child_by_type(node, "parameters")
    args = _extract_params(params_node, source) if params_node else []
    docstring = _extract_doc_comment(node, source)
    decorators = _extract_decorators(node, source)

    return_type = ""
    rt_node = find_child_by_type(node, "type_identifier")
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
            cyclomatic_complexity=1,
            return_type=return_type,
        )
    )


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    extends = find_child_by_type(node, "extends_clause")
    if extends:
        for ti in find_children_by_type(extends, "type_identifier"):
            bases.append(node_text(ti, source))

    attributes: list[str] = []
    cp_node = find_child_by_type(node, "class_parameters")
    if cp_node:
        attributes.extend(_extract_class_params(cp_node, source))

    body = find_child_by_type(node, "template_body")
    if body:
        for val in find_children_by_type(body, "val_definition"):
            vid = find_child_by_type(val, "identifier")
            if vid:
                attributes.append(node_text(vid, source))
        for var in find_children_by_type(body, "var_definition"):
            vid = find_child_by_type(var, "identifier")
            if vid:
                attributes.append(node_text(vid, source))

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


def _handle_trait(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    extends = find_child_by_type(node, "extends_clause")
    if extends:
        for ti in find_children_by_type(extends, "type_identifier"):
            bases.append(node_text(ti, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="trait",
            bases=bases,
            attributes=[],
            docstring=docstring,
        )
    )

    body = find_child_by_type(node, "template_body")
    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_object(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    bases: list[str] = []
    extends = find_child_by_type(node, "extends_clause")
    if extends:
        for ti in find_children_by_type(extends, "type_identifier"):
            bases.append(node_text(ti, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="object",
            bases=bases,
            attributes=[],
            docstring=docstring,
        )
    )

    body = find_child_by_type(node, "template_body")
    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_enum(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    attributes: list[str] = []
    body = find_child_by_type(node, "enum_body")
    if body:
        for case_defs in find_children_by_type(body, "enum_case_definitions"):
            for case in find_children_by_type(case_defs, "simple_enum_case"):
                case_id = find_child_by_type(case, "identifier")
                if case_id:
                    attributes.append(node_text(case_id, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="enum",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )

    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    parts: list[str] = []
    for child in node.children:
        if child.type == "identifier":
            parts.append(node_text(child, source))

    ns = find_child_by_type(node, "namespace_selectors")
    if ns:
        module = ".".join(parts)
        for child in ns.children:
            if child.type == "identifier":
                imported = node_text(child, source)
                result.imports.append(
                    ParsedImport(
                        module=module,
                        line_number=node.start_point[0] + 1,
                        imported_name=imported,
                    )
                )
            elif child.type == "arrow_renamed_identifier":
                ids = find_children_by_type(child, "identifier")
                if len(ids) >= 2:
                    result.imports.append(
                        ParsedImport(
                            module=module,
                            line_number=node.start_point[0] + 1,
                            imported_name=node_text(ids[0], source),
                            alias=node_text(ids[1], source),
                        )
                    )
        return

    if not parts:
        return

    module = ".".join(parts)
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
    first = node.children[0] if node.children else None
    if first is None:
        return

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
    elif first.type == "field_expression":
        ids = find_children_by_type(first, "identifier")
        if len(ids) >= 2:
            method_name = node_text(ids[-1], source)
            full = node_text(first, source)
            result.calls.append(
                ParsedCall(
                    name=method_name,
                    line_number=node.start_point[0] + 1,
                    caller=caller,
                    full_call_name=full,
                )
            )
    elif first.type == "call_expression":
        _handle_call(first, source, result, class_context, caller)

    args = find_child_by_type(node, "arguments")
    if args:
        _walk(args, source, result, class_context, caller)
    block = find_child_by_type(node, "block")
    if block:
        _walk(block, source, result, class_context, caller)


def _handle_val(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    if not class_context:
        id_node = find_child_by_type(node, "identifier")
        if id_node:
            result.variables.append(node_text(id_node, source))
    _walk(node, source, result, class_context, caller)
