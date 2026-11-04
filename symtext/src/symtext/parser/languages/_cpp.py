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
    "if_statement",
    "for_statement",
    "while_statement",
    "do_statement",
    "case_statement",
    "catch_clause",
    "conditional_expression",
    "binary_expression",
})


def _cpp_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
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


def _extract_declarator_name(node: tree_sitter.Node, source: bytes) -> str:
    if node.type in ("identifier", "field_identifier", "destructor_name"):
        return node_text(node, source)
    if node.type == "qualified_identifier":
        name_node = node.child_by_field_name("name")
        if name_node:
            return node_text(name_node, source)
        return node_text(node, source)
    if node.type == "operator_name":
        return node_text(node, source)
    if node.type in (
        "function_declarator",
        "pointer_declarator",
        "reference_declarator",
        "parenthesized_declarator",
    ):
        declarator = node.child_by_field_name("declarator")
        if declarator:
            return _extract_declarator_name(declarator, source)
        for child in node.children:
            if child.type in ("identifier", "field_identifier", "qualified_identifier"):
                return _extract_declarator_name(child, source)
    return ""


def _extract_params(declarator: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    func_decl: tree_sitter.Node | None = declarator
    while func_decl and func_decl.type != "function_declarator":
        func_decl = find_child_by_type(func_decl, "function_declarator")
        if func_decl is None:
            for child_type in ("pointer_declarator", "reference_declarator"):
                inner = find_child_by_type(declarator, child_type)
                if inner:
                    func_decl = find_child_by_type(inner, "function_declarator")
                    if func_decl:
                        break
            break

    if func_decl is None:
        return args

    params = func_decl.child_by_field_name("parameters")
    if params is None:
        return args

    for child in params.children:
        if child.type == "parameter_declaration":
            decl = child.child_by_field_name("declarator")
            if decl:
                name = _extract_declarator_name(decl, source)
                if name:
                    args.append(name)
            else:
                id_node = find_child_by_type(child, "identifier")
                if id_node:
                    args.append(node_text(id_node, source))
        elif child.type == "variadic_parameter":
            args.append("...")
        elif child.type == "optional_parameter_declaration":
            decl = child.child_by_field_name("declarator")
            if decl:
                name = _extract_declarator_name(decl, source)
                if name:
                    args.append(name)
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("/**"):
            inner = text[3:]
            if inner.endswith("*/"):
                inner = inner[:-2]
            block_lines: list[str] = []
            for line in inner.split("\n"):
                stripped = line.strip().lstrip("* ").strip()
                if stripped:
                    block_lines.append(stripped)
            return "\n".join(block_lines)
        if text.startswith("///"):
            triple_lines: list[str] = []
            while prev and prev.type == "comment":
                t = node_text(prev, source)
                if t.startswith("///"):
                    triple_lines.append(t[3:].strip())
                else:
                    break
                prev = prev.prev_named_sibling
            triple_lines.reverse()
            return "\n".join(triple_lines)
    return ""


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
    if func.type == "qualified_identifier":
        name = func.child_by_field_name("name")
        if name:
            return (node_text(name, source), full_name)
    if func.type == "template_function":
        name_node = func.child_by_field_name("name")
        if name_node:
            return (node_text(name_node, source), full_name)
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
        if child.type == "declaration":
            is_func = False
            for sub in child.children:
                if sub.type == "function_declarator":
                    is_func = True
                    break
                if sub.type == "init_declarator":
                    inner = sub.child_by_field_name("declarator")
                    if inner and inner.type == "function_declarator":
                        is_func = True
                        break
            if is_func:
                continue
            for sub in child.children:
                if sub.type in ("identifier", "pointer_declarator"):
                    name = _extract_declarator_name(sub, source)
                    if name:
                        result.variables.append(name)
                elif sub.type == "init_declarator":
                    decl = sub.child_by_field_name("declarator")
                    if decl:
                        name = _extract_declarator_name(decl, source)
                        if name:
                            result.variables.append(name)


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "function_definition":
            _handle_function(child, source, result, class_context)

        elif child.type in (
            "struct_specifier",
            "class_specifier",
            "enum_specifier",
            "union_specifier",
        ):
            _handle_class(child, source, result)

        elif child.type == "namespace_definition":
            _handle_namespace(child, source, result)

        elif child.type == "template_declaration":
            for sub in child.children:
                if sub.type in (
                    "function_definition",
                    "class_specifier",
                    "struct_specifier",
                    "declaration",
                ):
                    if sub.type == "function_definition":
                        _handle_function(sub, source, result, class_context)
                    elif sub.type in ("class_specifier", "struct_specifier"):
                        _handle_class(sub, source, result)

        elif child.type == "preproc_include":
            _handle_include(child, source, result)

        elif child.type == "using_declaration":
            _handle_using(child, source, result)

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

        elif child.type == "expression_statement" or (
            child.child_count > 0
            and child.type
            not in (
                "function_definition",
                "struct_specifier",
                "class_specifier",
                "enum_specifier",
                "union_specifier",
                "namespace_definition",
                "template_declaration",
                "preproc_include",
                "using_declaration",
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
    declarator = node.child_by_field_name("declarator")
    if declarator is None:
        return
    name = _extract_declarator_name(declarator, source)
    args = _extract_params(declarator, source)
    body = node.child_by_field_name("body")
    docstring = _extract_doc_comment(node, source)
    complexity = _cpp_cyclomatic(body, source) if body else 1

    func_class_context = class_context
    if declarator.type == "function_declarator":
        inner_decl = declarator.child_by_field_name("declarator")
        if inner_decl and inner_decl.type == "qualified_identifier":
            scope = inner_decl.child_by_field_name("scope")
            if scope:
                func_class_context = node_text(scope, source).rstrip(":")

    return_type = ""
    type_node = node.child_by_field_name("type")
    if type_node:
        return_type = node_text(type_node, source).strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            docstring=docstring,
            class_context=func_class_context,
            cyclomatic_complexity=complexity,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, func_class_context, caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    kind_map = {
        "class_specifier": "class",
        "struct_specifier": "struct",
        "enum_specifier": "enum",
        "union_specifier": "struct",
    }
    kind = kind_map.get(node.type, "class")

    bases: list[str] = []
    base_clause = find_child_by_type(node, "base_class_clause")
    if base_clause:
        for child in base_clause.children:
            if child.type in ("type_identifier", "qualified_identifier"):
                bases.append(node_text(child, source))

    attributes: list[str] = []
    body = node.child_by_field_name("body")
    if body:
        for child in body.children:
            if child.type == "field_declaration":
                decl = child.child_by_field_name("declarator")
                if decl:
                    fname = _extract_declarator_name(decl, source)
                    if fname:
                        attributes.append(fname)
                else:
                    id_node = find_child_by_type(child, "field_identifier")
                    if id_node:
                        attributes.append(node_text(id_node, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind=kind,
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )

    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_namespace(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    body = node.child_by_field_name("body")
    if body:
        _walk(body, source, result, class_context="", caller="")


def _handle_include(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    path_node = node.child_by_field_name("path")
    if path_node:
        module = node_text(path_node, source).strip('"<>')
    else:
        for child in node.children:
            if child.type in ("string_literal", "system_lib_string"):
                module = node_text(child, source).strip('"<>')
                break
        else:
            return
    result.imports.append(ParsedImport(module=module, line_number=node.start_point[0] + 1))


def _handle_using(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for child in node.children:
        if child.type == "qualified_identifier":
            full = node_text(child, source)
            parts = full.rsplit("::", 1)
            module = parts[0] if len(parts) > 1 else full
            imported = parts[1] if len(parts) > 1 else ""
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=node.start_point[0] + 1,
                    imported_name=imported,
                )
            )
            return
        if child.type == "identifier":
            result.imports.append(
                ParsedImport(
                    module=node_text(child, source),
                    line_number=node.start_point[0] + 1,
                )
            )
            return
