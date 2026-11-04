from __future__ import annotations

import tree_sitter

from symtext.parser._common import cyclomatic_complexity, node_text
from symtext.parser.parser import (
    FileParseResult,
    ParsedCall,
    ParsedClass,
    ParsedFunction,
    ParsedImport,
)

_COMPLEXITY_NODES: frozenset[str] = frozenset({
    "if_statement",
    "elif_clause",
    "for_statement",
    "while_statement",
    "except_clause",
    "boolean_operator",
    "conditional_expression",
})


def _extract_docstring(body_node: tree_sitter.Node, source: bytes) -> str:
    if body_node.type != "block" or body_node.child_count == 0:
        return ""
    first = body_node.children[0]
    string_node: tree_sitter.Node | None = None
    if first.type == "expression_statement" and first.child_count > 0:
        expr = first.children[0]
        if expr.type == "string":
            string_node = expr
    elif first.type == "string":
        string_node = first

    if string_node is None:
        return ""

    from symtext.parser._common import find_child_by_type

    content_node = find_child_by_type(string_node, "string_content")
    if content_node is not None:
        return node_text(content_node, source).strip()

    raw = node_text(string_node, source)
    for q in ('"""', "'''", '"', "'"):
        if raw.startswith(q) and raw.endswith(q):
            return raw[len(q) : -len(q)].strip()
    return raw


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators = []
    for child in node.children:
        if child.type == "decorator":
            for deco_child in child.children:
                if deco_child.type not in ("@",):
                    decorators.append(node_text(deco_child, source).split("(")[0])
                    break
    return decorators


def _extract_parameters(params_node: tree_sitter.Node, source: bytes) -> list[str]:
    args = []
    for child in params_node.children:
        if child.type == "identifier":
            args.append(node_text(child, source))
        elif child.type in ("typed_parameter", "typed_default_parameter", "default_parameter"):
            for sub in child.children:
                if sub.type == "identifier":
                    args.append(node_text(sub, source))
                    break
        elif child.type == "list_splat_pattern":
            for sub in child.children:
                if sub.type == "identifier":
                    args.append("*" + node_text(sub, source))
                    break
        elif child.type == "dictionary_splat_pattern":
            for sub in child.children:
                if sub.type == "identifier":
                    args.append("**" + node_text(sub, source))
                    break
    return args


def _extract_bases(node: tree_sitter.Node, source: bytes) -> list[str]:
    for child in node.children:
        if child.type == "argument_list":
            bases = []
            for arg in child.children:
                if arg.type in ("identifier", "dotted_name", "attribute"):
                    bases.append(node_text(arg, source))
            return bases
    return []


def _extract_call_name(call_node: tree_sitter.Node, source: bytes) -> tuple[str, str]:
    func = call_node.children[0] if call_node.children else None
    if func is None:
        return ("", "")
    full_name = node_text(func, source)
    if func.type == "identifier":
        return (full_name, full_name)
    if func.type == "attribute":
        for child in reversed(func.children):
            if child.type == "identifier":
                return (node_text(child, source), full_name)
    return (full_name, full_name)


def _extract_assignment_name(node: tree_sitter.Node, source: bytes) -> str | None:
    if node.type != "assignment":
        return None
    for sub in node.children:
        if sub.type == "identifier":
            return node_text(sub, source)
        break
    return None


def _extract_class_attributes(body_node: tree_sitter.Node, source: bytes) -> list[str]:
    attrs: list[str] = []
    for child in body_node.children:
        if child.type == "assignment":
            name = _extract_assignment_name(child, source)
            if name:
                attrs.append(name)
        elif child.type == "expression_statement" and child.child_count > 0:
            expr = child.children[0]
            if expr.type == "assignment":
                name = _extract_assignment_name(expr, source)
                if name:
                    attrs.append(name)
    return attrs


def _extract_variables(root_node: tree_sitter.Node, source: bytes) -> list[str]:
    variables: list[str] = []
    for child in root_node.children:
        if child.type == "assignment":
            name = _extract_assignment_name(child, source)
            if name:
                variables.append(name)
        elif child.type == "expression_statement" and child.child_count > 0:
            expr = child.children[0]
            if expr.type == "assignment":
                name = _extract_assignment_name(expr, source)
                if name:
                    variables.append(name)
    return variables


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    result.variables = _extract_variables(root, source)
    _walk(root, source, result, class_context="", caller="")


def _walk(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    for child in node.children:
        if child.type == "function_definition":
            name_node = child.child_by_field_name("name")
            name = node_text(name_node, source) if name_node else ""
            params_node = child.child_by_field_name("parameters")
            args = _extract_parameters(params_node, source) if params_node else []
            body_node = child.child_by_field_name("body")
            docstring = _extract_docstring(body_node, source) if body_node else ""
            decorators = _extract_decorators(child, source)
            complexity = cyclomatic_complexity(body_node, _COMPLEXITY_NODES) if body_node else 1
            line_number = child.start_point[0] + 1

            is_async = any(c.type == "async" for c in child.children)

            return_type = ""
            rt_node = child.child_by_field_name("return_type")
            if rt_node:
                return_type = node_text(rt_node, source).lstrip("- >").strip()

            result.functions.append(
                ParsedFunction(
                    name=name,
                    line_number=line_number,
                    end_line_number=child.end_point[0] + 1,
                    args=args,
                    decorators=decorators,
                    docstring=docstring,
                    class_context=class_context,
                    cyclomatic_complexity=complexity,
                    is_async=is_async,
                    return_type=return_type,
                )
            )
            if body_node:
                _walk(body_node, source, result, class_context, caller=name)

        elif child.type == "class_definition":
            name_node = child.child_by_field_name("name")
            cls_name = node_text(name_node, source) if name_node else ""
            bases = _extract_bases(child, source)
            body_node = child.child_by_field_name("body")
            docstring = _extract_docstring(body_node, source) if body_node else ""
            line_number = child.start_point[0] + 1
            attributes = _extract_class_attributes(body_node, source) if body_node else []

            result.classes.append(
                ParsedClass(
                    name=cls_name,
                    line_number=line_number,
                    end_line_number=child.end_point[0] + 1,
                    bases=bases,
                    attributes=attributes,
                    docstring=docstring,
                )
            )
            if body_node:
                _walk(body_node, source, result, class_context=cls_name, caller=cls_name)

        elif child.type == "decorated_definition":
            _walk(child, source, result, class_context, caller)

        elif child.type == "import_statement":
            for imp_child in child.children:
                if imp_child.type == "dotted_name":
                    module = node_text(imp_child, source)
                    result.imports.append(
                        ParsedImport(
                            module=module,
                            line_number=child.start_point[0] + 1,
                        )
                    )
                elif imp_child.type == "aliased_import":
                    name_part = imp_child.child_by_field_name("name")
                    alias_part = imp_child.child_by_field_name("alias")
                    module = node_text(name_part, source) if name_part else ""
                    alias = node_text(alias_part, source) if alias_part else ""
                    result.imports.append(
                        ParsedImport(
                            module=module,
                            line_number=child.start_point[0] + 1,
                            alias=alias,
                        )
                    )

        elif child.type == "import_from_statement":
            module = ""
            imported_names: list[tuple[str, str]] = []
            for imp_child in child.children:
                is_module_src = (imp_child.type == "dotted_name" and not module) or imp_child.type == "relative_import"
                if is_module_src:
                    module = node_text(imp_child, source)
                elif imp_child.type == "dotted_name" and module:
                    imported_names.append((node_text(imp_child, source), ""))
                elif imp_child.type == "aliased_import":
                    name_part = imp_child.child_by_field_name("name")
                    alias_part = imp_child.child_by_field_name("alias")
                    nm = node_text(name_part, source) if name_part else ""
                    al = node_text(alias_part, source) if alias_part else ""
                    imported_names.append((nm, al))
            if imported_names:
                for imported_name, alias in imported_names:
                    result.imports.append(
                        ParsedImport(
                            module=module,
                            line_number=child.start_point[0] + 1,
                            imported_name=imported_name,
                            alias=alias,
                        )
                    )
            else:
                result.imports.append(
                    ParsedImport(
                        module=module,
                        line_number=child.start_point[0] + 1,
                    )
                )

        elif child.type == "call" or (
            child.type == "expression_statement" and child.child_count > 0 and child.children[0].type == "call"
        ):
            call_node = child if child.type == "call" else child.children[0]
            simple_name, full_name = _extract_call_name(call_node, source)
            if simple_name:
                result.calls.append(
                    ParsedCall(
                        name=simple_name,
                        line_number=call_node.start_point[0] + 1,
                        caller=caller,
                        full_call_name=full_name,
                    )
                )
            for arg in call_node.children[1:]:
                if arg.child_count > 0:
                    _walk(arg, source, result, class_context, caller)

        else:
            if child.child_count > 0 and child.type not in (
                "function_definition",
                "class_definition",
                "import_statement",
                "import_from_statement",
            ):
                _walk(child, source, result, class_context, caller)
