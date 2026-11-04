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
    "else_clause",
    "for_statement",
    "for_in_statement",
    "while_statement",
    "do_statement",
    "switch_case",
    "catch_clause",
    "ternary_expression",
    "binary_expression",
})


def _is_logical_op(node: tree_sitter.Node, source: bytes) -> bool:
    for child in node.children:
        txt = node_text(child, source)
        if txt in ("&&", "||"):
            return True
    return False


def _ts_cyclomatic(body_node: tree_sitter.Node, source: bytes) -> int:
    complexity = 1
    stack: list[tree_sitter.Node] = [body_node]
    while stack:
        n = stack.pop()
        if n.type == "binary_expression":
            if _is_logical_op(n, source):
                complexity += 1
        elif n.type in _COMPLEXITY_NODES:
            complexity += 1
        for child in n.children:
            stack.append(child)
    return complexity


def _extract_params(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in params_node.children:
        if child.type in ("identifier",):
            args.append(node_text(child, source))
        elif child.type in (
            "required_parameter",
            "optional_parameter",
        ):
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append(node_text(id_node, source))
        elif child.type == "rest_pattern":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                args.append("..." + node_text(id_node, source))
    return args


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func = call_node.child_by_field_name("function")
    if func is None:
        return ("", "")
    full_name = node_text(func, source)
    if func.type == "identifier":
        return (full_name, full_name)
    if func.type == "member_expression":
        prop = func.child_by_field_name("property")
        if prop:
            return (node_text(prop, source), full_name)
    return (full_name, full_name)


def _extract_jsdoc(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev and prev.type == "comment":
        text = node_text(prev, source)
        if text.startswith("/**"):
            inner = text[3:-2].strip()
            lines = []
            for line in inner.split("\n"):
                line = line.strip()
                if line.startswith("* "):
                    line = line[2:]
                elif line.startswith("*"):
                    line = line[1:]
                lines.append(line.strip())
            return "\n".join(lines).strip()
    return ""


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    prev = node.prev_named_sibling
    while prev and prev.type == "decorator":
        for child in prev.children:
            if child.type not in ("@",):
                decorators.append(node_text(child, source).split("(")[0])
                break
        prev = prev.prev_named_sibling
    decorators.reverse()
    return decorators


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    _extract_variables(root, source, result)
    _walk(root, source, result, class_context="", caller="")


def _extract_variables(root: tree_sitter.Node, source: bytes, result: FileParseResult) -> None:
    for child in root.children:
        node = child
        if node.type == "export_statement":
            decl = find_child_by_type(node, "lexical_declaration")
            if decl is None:
                decl = find_child_by_type(node, "variable_declaration")
            if decl:
                node = decl
            else:
                continue
        if node.type in ("lexical_declaration", "variable_declaration"):
            for sub in node.children:
                if sub.type == "variable_declarator":
                    name_node = sub.child_by_field_name("name")
                    if name_node and name_node.type == "identifier":
                        value = sub.child_by_field_name("value")
                        if value and value.type in ("arrow_function", "function"):
                            continue
                        result.variables.append(node_text(name_node, source))


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        inner = child
        if child.type == "export_statement":
            for sub in child.children:
                if sub.type in (
                    "function_declaration",
                    "class_declaration",
                    "lexical_declaration",
                    "abstract_class_declaration",
                ):
                    inner = sub
                    break

        if inner.type in ("function_declaration", "generator_function_declaration"):
            _handle_function(inner, source, result, class_context)

        elif inner.type in ("class_declaration", "abstract_class_declaration"):
            _handle_class(inner, source, result)

        elif inner.type == "interface_declaration":
            _handle_interface(inner, source, result)

        elif inner.type == "method_definition":
            _handle_method(inner, source, result, class_context)

        elif inner.type in ("lexical_declaration", "variable_declaration"):
            for sub in inner.children:
                if sub.type == "variable_declarator":
                    value = sub.child_by_field_name("value")
                    if value and value.type in ("arrow_function", "function"):
                        _handle_arrow_fn(sub, value, source, result, class_context)
                    elif value:
                        _walk(value, source, result, class_context, caller)

        elif child.type == "import_statement":
            _handle_import(child, source, result)

        elif inner.type == "expression_statement":
            _walk(inner, source, result, class_context, caller)

        elif inner.type == "call_expression":
            simple_name, full_name = _extract_call_name(inner, source)
            if simple_name:
                result.calls.append(
                    ParsedCall(
                        name=simple_name,
                        line_number=inner.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full_name,
                    )
                )
            args = inner.child_by_field_name("arguments")
            if args:
                _walk(args, source, result, class_context, caller)

        elif inner.child_count > 0 and inner.type not in (
            "import_statement",
            "string",
            "template_string",
        ):
            _walk(inner, source, result, class_context, caller)


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
    docstring = _extract_jsdoc(node, source)
    complexity = _ts_cyclomatic(body, source) if body else 1

    is_async = any(c.type == "async" for c in node.children)

    return_type = ""
    rt_node = node.child_by_field_name("return_type")
    if rt_node:
        return_type = node_text(rt_node, source).lstrip(":").strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=is_async,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context, caller=name)


def _handle_arrow_fn(
    declarator: tree_sitter.Node,
    arrow_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    name_node = declarator.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""
    params = arrow_node.child_by_field_name("parameters")
    args = _extract_params(params, source) if params else []
    body = arrow_node.child_by_field_name("body")
    complexity = _ts_cyclomatic(body, source) if body else 1

    is_async = any(c.type == "async" for c in arrow_node.children)

    return_type = ""
    rt_node = arrow_node.child_by_field_name("return_type")
    if rt_node:
        return_type = node_text(rt_node, source).lstrip(":").strip()

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=declarator.start_point[0] + 1,
            end_line_number=declarator.end_point[0] + 1,
            args=args,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=is_async,
            return_type=return_type,
        )
    )
    if body:
        _walk(body, source, result, class_context, caller=name)


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    cls_name = node_text(name_node, source) if name_node else ""

    bases: list[str] = []
    heritage = find_child_by_type(node, "class_heritage")
    if heritage:
        extends = find_child_by_type(heritage, "extends_clause")
        if extends:
            for child in extends.children:
                if child.type in ("identifier", "type_identifier"):
                    bases.append(node_text(child, source))
        implements = find_child_by_type(heritage, "implements_clause")
        if implements:
            for child in implements.children:
                if child.type in ("identifier", "type_identifier"):
                    bases.append(node_text(child, source))

    docstring = _extract_jsdoc(node, source)

    attributes: list[str] = []
    body = find_child_by_type(node, "class_body")
    if body:
        for child in body.children:
            if child.type == "public_field_definition":
                prop = find_child_by_type(child, "property_identifier")
                if prop:
                    attributes.append(node_text(prop, source))

    result.classes.append(
        ParsedClass(
            name=cls_name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )

    if body:
        _walk(body, source, result, class_context=cls_name, caller=cls_name)


def _handle_interface(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) if name_node else ""

    bases: list[str] = []
    extends = find_child_by_type(node, "extends_type_clause")
    if extends:
        for child in extends.children:
            if child.type == "type_identifier":
                bases.append(node_text(child, source))

    docstring = _extract_jsdoc(node, source)

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="interface",
            bases=bases,
            docstring=docstring,
        )
    )


def _handle_method(
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
    docstring = _extract_jsdoc(node, source)
    decorators = _extract_decorators(node, source)
    complexity = _ts_cyclomatic(body, source) if body else 1

    is_async = any(c.type == "async" for c in node.children)

    return_type = ""
    rt_node = node.child_by_field_name("return_type")
    if rt_node:
        return_type = node_text(rt_node, source).lstrip(":").strip()

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


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    line = node.start_point[0] + 1

    source_node = node.child_by_field_name("source")
    if source_node is None:
        for child in node.children:
            if child.type == "string":
                source_node = child
                break
    module = ""
    if source_node:
        frag = find_child_by_type(source_node, "string_fragment")
        if frag:
            module = node_text(frag, source)
        else:
            raw = node_text(source_node, source)
            module = raw.strip("'\"")

    clause = find_child_by_type(node, "import_clause")
    if clause is None:
        result.imports.append(ParsedImport(module=module, line_number=line))
        return

    for child in clause.children:
        if child.type == "identifier":
            result.imports.append(
                ParsedImport(
                    module=module,
                    line_number=line,
                    imported_name=node_text(child, source),
                )
            )
        elif child.type == "named_imports":
            for spec in child.children:
                if spec.type == "import_specifier":
                    name_node = spec.child_by_field_name("name")
                    alias_node = spec.child_by_field_name("alias")
                    nm = node_text(name_node, source) if name_node else ""
                    al = node_text(alias_node, source) if alias_node else ""
                    result.imports.append(
                        ParsedImport(
                            module=module,
                            line_number=line,
                            imported_name=nm,
                            alias=al,
                        )
                    )
        elif child.type == "namespace_import":
            id_node = find_child_by_type(child, "identifier")
            if id_node:
                result.imports.append(
                    ParsedImport(
                        module=module,
                        line_number=line,
                        imported_name="*",
                        alias=node_text(id_node, source),
                    )
                )
