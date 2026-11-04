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
    "if_statement",
    "for_statement",
    "while_statement",
    "do_statement",
    "switch_statement_case",
    "catch_clause",
})


def _extract_params(param_list: tree_sitter.Node, source: bytes) -> list[str]:
    args: list[str] = []
    for child in param_list.children:
        if child.type == "formal_parameter":
            cp = find_child_by_type(child, "constructor_param")
            if cp:
                id_node = find_child_by_type(cp, "identifier")
                if id_node:
                    args.append(node_text(id_node, source))
            else:
                ids = find_children_by_type(child, "identifier")
                if ids:
                    args.append(node_text(ids[-1], source))
        elif child.type == "optional_formal_parameters":
            for fp in find_children_by_type(child, "formal_parameter"):
                cp = find_child_by_type(fp, "constructor_param")
                if cp:
                    id_node = find_child_by_type(cp, "identifier")
                    if id_node:
                        args.append(node_text(id_node, source))
                else:
                    ids = find_children_by_type(fp, "identifier")
                    if ids:
                        args.append(node_text(ids[-1], source))
    return args


def _extract_doc_comment(node: tree_sitter.Node, source: bytes) -> str:
    lines: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "annotation":
        prev = prev.prev_named_sibling
    while prev is not None and prev.type == "documentation_comment":
        text = node_text(prev, source)
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("///"):
                lines.append(stripped[3:].strip())
        prev = prev.prev_named_sibling
    if not lines:
        return ""
    lines.reverse()
    return "\n".join(lines)


def _extract_decorators(node: tree_sitter.Node, source: bytes) -> list[str]:
    decorators: list[str] = []
    prev = node.prev_named_sibling
    while prev is not None and prev.type == "annotation":
        id_node = find_child_by_type(prev, "identifier")
        if id_node:
            decorators.append(node_text(id_node, source))
        prev = prev.prev_named_sibling
    decorators.reverse()
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
    children = node.children
    i = 0
    while i < len(children):
        child = children[i]

        if child.type == "class_definition":
            _handle_class(child, source, result)

        elif child.type == "enum_declaration":
            _handle_enum(child, source, result)

        elif child.type == "mixin_declaration":
            _handle_mixin(child, source, result)

        elif child.type == "extension_declaration":
            _handle_extension(child, source, result)

        elif child.type == "import_or_export":
            _handle_import(child, source, result)

        elif child.type == "function_signature":
            next_sib = children[i + 1] if i + 1 < len(children) else None
            body = next_sib if next_sib and next_sib.type == "function_body" else None
            _handle_function(
                child,
                body,
                source,
                result,
                class_context="",
                caller="",
            )
            if body:
                i += 1

        elif child.type == "method_signature":
            next_sib = children[i + 1] if i + 1 < len(children) else None
            body = next_sib if next_sib and next_sib.type == "function_body" else None
            _handle_method(
                child,
                body,
                source,
                result,
                class_context,
                caller,
            )
            if body:
                i += 1

        elif child.type == "declaration" and class_context:
            if find_child_by_type(child, "constructor_signature"):
                _handle_constructor(child, source, result, class_context)

        elif child.type == "const_builtin" or child.type == "final_builtin":
            if not class_context:
                next_sib = children[i + 1] if i + 1 < len(children) else None
                sfdl = next_sib if next_sib and next_sib.type == "static_final_declaration_list" else None
                if sfdl:
                    _handle_top_level_var(sfdl, source, result)

        elif child.type == "expression_statement":
            _handle_expression_calls(child, source, result, class_context, caller)

        elif child.type == "local_variable_declaration":
            _handle_expression_calls(child, source, result, class_context, caller)

        elif child.type == "return_statement":
            _handle_expression_calls(child, source, result, class_context, caller)

        elif child.child_count > 0 and child.type not in (
            "class_definition",
            "enum_declaration",
            "mixin_declaration",
            "extension_declaration",
            "import_or_export",
            "string_literal",
            "function_signature",
            "method_signature",
        ):
            _walk(child, source, result, class_context, caller)

        i += 1


def _handle_function(
    sig_node: tree_sitter.Node,
    body_node: tree_sitter.Node | None,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    id_node = find_child_by_type(sig_node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    param_list = find_child_by_type(sig_node, "formal_parameter_list")
    args = _extract_params(param_list, source) if param_list else []
    docstring = _extract_doc_comment(sig_node, source)
    complexity = cyclomatic_complexity(body_node, _COMPLEXITY_NODES) if body_node else 1

    is_async = False
    if body_node:
        is_async = any(node_text(c, source) == "async" for c in body_node.children)

    return_type = ""
    type_node = find_child_by_type(sig_node, "type_identifier")
    if type_node:
        return_type = node_text(type_node, source).strip()
    elif find_child_by_type(sig_node, "void_type"):
        return_type = "void"

    end_node = body_node if body_node else sig_node
    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=sig_node.start_point[0] + 1,
            end_line_number=end_node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=complexity,
            is_async=is_async,
            return_type=return_type,
        )
    )
    if body_node:
        _walk(body_node, source, result, class_context, caller=name)


def _handle_method(
    method_sig: tree_sitter.Node,
    body_node: tree_sitter.Node | None,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    func_sig = find_child_by_type(method_sig, "function_signature")
    getter_sig = find_child_by_type(method_sig, "getter_signature")

    if func_sig:
        id_node = find_child_by_type(func_sig, "identifier")
        name = node_text(id_node, source) if id_node else ""
        if not name:
            return
        param_list = find_child_by_type(func_sig, "formal_parameter_list")
        args = _extract_params(param_list, source) if param_list else []
    elif getter_sig:
        id_node = find_child_by_type(getter_sig, "identifier")
        name = node_text(id_node, source) if id_node else ""
        if not name:
            return
        args = []
    else:
        return

    docstring = _extract_doc_comment(method_sig, source)
    decorators = _extract_decorators(method_sig, source)
    complexity = cyclomatic_complexity(body_node, _COMPLEXITY_NODES) if body_node else 1

    is_async = False
    if body_node:
        is_async = any(node_text(c, source) == "async" for c in body_node.children)

    return_type = ""
    if func_sig:
        type_node = find_child_by_type(func_sig, "type_identifier")
        if type_node:
            return_type = node_text(type_node, source).strip()
        elif find_child_by_type(func_sig, "void_type"):
            return_type = "void"

    end_node = body_node if body_node else method_sig
    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=method_sig.start_point[0] + 1,
            end_line_number=end_node.end_point[0] + 1,
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


def _handle_constructor(
    decl_node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
) -> None:
    ctor_sig = find_child_by_type(decl_node, "constructor_signature")
    if ctor_sig is None:
        return

    ids = find_children_by_type(ctor_sig, "identifier")
    if not ids:
        return
    if len(ids) >= 2:
        name = f"{node_text(ids[0], source)}.{node_text(ids[1], source)}"
    else:
        name = node_text(ids[0], source)

    param_list = find_child_by_type(ctor_sig, "formal_parameter_list")
    args = _extract_params(param_list, source) if param_list else []
    docstring = _extract_doc_comment(decl_node, source)

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=decl_node.start_point[0] + 1,
            end_line_number=decl_node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context=class_context,
            cyclomatic_complexity=1,
            is_async=False,
            return_type="",
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
    superclass = find_child_by_type(node, "superclass")
    if superclass:
        for ti in find_children_by_type(superclass, "type_identifier"):
            bases.append(node_text(ti, source))
    interfaces = find_child_by_type(node, "interfaces")
    if interfaces:
        for ti in find_children_by_type(interfaces, "type_identifier"):
            bases.append(node_text(ti, source))
    mixins = find_child_by_type(node, "mixins")
    if mixins:
        for ti in find_children_by_type(mixins, "type_identifier"):
            bases.append(node_text(ti, source))

    attributes: list[str] = []
    body = find_child_by_type(node, "class_body")
    if body:
        for decl in find_children_by_type(body, "declaration"):
            if find_child_by_type(decl, "constructor_signature"):
                continue
            iil = find_child_by_type(decl, "initialized_identifier_list")
            if iil:
                for ii in find_children_by_type(iil, "initialized_identifier"):
                    ii_id = find_child_by_type(ii, "identifier")
                    if ii_id:
                        attributes.append(node_text(ii_id, source))

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
        for ec in find_children_by_type(body, "enum_constant"):
            ec_id = find_child_by_type(ec, "identifier")
            if ec_id:
                attributes.append(node_text(ec_id, source))

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


def _handle_mixin(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    id_node = find_child_by_type(node, "identifier")
    name = node_text(id_node, source) if id_node else ""
    if not name:
        return

    docstring = _extract_doc_comment(node, source)

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="mixin",
            bases=[],
            attributes=[],
            docstring=docstring,
        )
    )

    body = find_child_by_type(node, "class_body")
    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_extension(
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
    on_type = find_child_by_type(node, "type_identifier")
    if on_type:
        bases.append(node_text(on_type, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="extension",
            bases=bases,
            attributes=[],
            docstring=docstring,
        )
    )

    body = find_child_by_type(node, "extension_body")
    if body:
        _walk(body, source, result, class_context=name, caller=name)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    lib_import = find_child_by_type(node, "library_import")
    if lib_import is None:
        return
    spec = find_child_by_type(lib_import, "import_specification")
    if spec is None:
        return

    conf_uri = find_child_by_type(spec, "configurable_uri")
    if conf_uri is None:
        return
    uri_node = find_child_by_type(conf_uri, "uri")
    if uri_node is None:
        return
    sl = find_child_by_type(uri_node, "string_literal")
    if sl is None:
        return

    module = node_text(sl, source).strip("'\"")

    alias = ""
    alias_id = find_child_by_type(spec, "identifier")
    if alias_id:
        alias = node_text(alias_id, source)

    result.imports.append(
        ParsedImport(
            module=module,
            line_number=node.start_point[0] + 1,
            alias=alias,
        )
    )


def _handle_expression_calls(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    class_context: str,
    caller: str,
) -> None:
    children = node.children
    for j, child in enumerate(children):
        if child.type != "identifier":
            if child.child_count > 0 and child.type not in ("string_literal",):
                _handle_expression_calls(child, source, result, class_context, caller)
            continue

        selectors = []
        k = j + 1
        while k < len(children) and children[k].type == "selector":
            selectors.append(children[k])
            k += 1

        if not selectors:
            continue

        first_sel = selectors[0]
        arg_part = find_child_by_type(first_sel, "argument_part")

        if arg_part:
            name = node_text(child, source)
            result.calls.append(
                ParsedCall(
                    name=name,
                    line_number=child.start_point[0] + 1,
                    caller=caller,
                    full_call_name=name,
                )
            )
        else:
            uas = find_child_by_type(first_sel, "unconditional_assignable_selector")
            if uas:
                member_id = find_child_by_type(uas, "identifier")
                if member_id and len(selectors) >= 2:
                    second_sel = selectors[1]
                    arg_part2 = find_child_by_type(second_sel, "argument_part")
                    if arg_part2:
                        member_name = node_text(member_id, source)
                        obj_name = node_text(child, source)
                        result.calls.append(
                            ParsedCall(
                                name=member_name,
                                line_number=child.start_point[0] + 1,
                                caller=caller,
                                full_call_name=f"{obj_name}.{member_name}",
                            )
                        )


def _handle_top_level_var(
    sfdl: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    for sfd in find_children_by_type(sfdl, "static_final_declaration"):
        id_node = find_child_by_type(sfd, "identifier")
        if id_node:
            result.variables.append(node_text(id_node, source))
