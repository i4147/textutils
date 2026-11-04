from __future__ import annotations

import tree_sitter

from symtext.parser._common import (
    find_child_by_type,
    find_children_by_type,
    node_text,
)
from symtext.parser.parser import (
    FileParseResult,
    ParsedClass,
    ParsedFunction,
    ParsedImport,
)


def _extract_haddock(node: tree_sitter.Node, source: bytes) -> str:
    prev = node.prev_named_sibling
    if prev is not None and prev.type == "haddock":
        text = node_text(prev, source)
        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.lstrip("-").lstrip().lstrip("|").strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines) if lines else ""
    return ""


def _module_text(mod_node: tree_sitter.Node, source: bytes) -> str:
    parts: list[str] = []
    for child in mod_node.children:
        if child.type == "module_id":
            parts.append(node_text(child, source))
    return ".".join(parts)


def _count_guards(node: tree_sitter.Node) -> int:
    count = 0
    for child in node.children:
        if child.type == "match":
            for mc in child.children:
                if mc.type == "|":
                    count += 1
                    break
    return count


def walk(
    root: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    imports_node = find_child_by_type(root, "imports")
    trailing_haddock: tree_sitter.Node | None = None
    if imports_node:
        for child in imports_node.children:
            if child.type == "import":
                _handle_import(child, source, result)
            elif child.type == "haddock":
                trailing_haddock = child

    decls = find_child_by_type(root, "declarations")
    if decls is None:
        return

    signatures: dict[str, tree_sitter.Node] = {}
    for child in decls.children:
        if child.type == "signature":
            var = find_child_by_type(child, "variable")
            if var:
                signatures[node_text(var, source)] = child

    for child in decls.children:
        if child.type == "function":
            _handle_function(child, source, result, signatures)
        elif child.type == "data_type":
            _handle_data_type(child, source, result, trailing_haddock)
        elif child.type in ("class", "newtype"):
            _handle_class(child, source, result)
        elif child.type == "bind":
            _handle_bind(child, source, result, signatures)


def _handle_import(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    mod_nodes = find_children_by_type(node, "module")
    if not mod_nodes:
        return

    module_name = _module_text(mod_nodes[0], source)
    is_qualified = find_child_by_type(node, "qualified") is not None

    alias = ""
    if len(mod_nodes) >= 2:
        alias = _module_text(mod_nodes[1], source)

    import_list = find_child_by_type(node, "import_list")
    if import_list:
        for imp in import_list.children:
            if imp.type == "import_name":
                name_node = find_child_by_type(imp, "name") or find_child_by_type(imp, "variable")
                if name_node:
                    imported = node_text(name_node, source)
                    result.imports.append(
                        ParsedImport(
                            module=module_name,
                            line_number=node.start_point[0] + 1,
                            alias=alias,
                            imported_name=imported,
                        )
                    )
        return

    result.imports.append(
        ParsedImport(
            module=module_name,
            line_number=node.start_point[0] + 1,
            alias="Map" if is_qualified and alias else alias,
        )
    )


def _handle_function(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    signatures: dict[str, tree_sitter.Node],
) -> None:
    var = find_child_by_type(node, "variable")
    if var is None:
        return
    name = node_text(var, source)

    args: list[str] = []
    patterns = find_child_by_type(node, "patterns")
    if patterns:
        for p in patterns.children:
            if p.type == "variable":
                args.append(node_text(p, source))

    docstring = ""
    sig = signatures.get(name)
    if sig:
        docstring = _extract_haddock(sig, source)
    if not docstring:
        docstring = _extract_haddock(node, source)

    guard_count = _count_guards(node)
    complexity = 1 + guard_count

    result.functions.append(
        ParsedFunction(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            args=args,
            decorators=[],
            docstring=docstring,
            class_context="",
            cyclomatic_complexity=complexity,
            is_async=False,
            return_type="",
        )
    )


def _handle_data_type(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    trailing_haddock: tree_sitter.Node | None = None,
) -> None:
    name_node = find_child_by_type(node, "name")
    if name_node is None:
        return
    name = node_text(name_node, source)
    docstring = _extract_haddock(node, source)
    if not docstring and trailing_haddock is not None:
        text = node_text(trailing_haddock, source)
        lines: list[str] = []
        for line in text.splitlines():
            stripped = line.lstrip("-").lstrip().lstrip("|").strip()
            if stripped:
                lines.append(stripped)
        docstring = "\n".join(lines) if lines else ""

    attributes: list[str] = []
    constructors = find_child_by_type(node, "data_constructors")
    if constructors:
        for ctor in constructors.children:
            if ctor.type == "data_constructor":
                record = find_child_by_type(ctor, "record")
                if record:
                    fields = find_child_by_type(record, "fields")
                    if fields:
                        for f in find_children_by_type(fields, "field"):
                            fname = find_child_by_type(f, "field_name")
                            if fname:
                                fvar = find_child_by_type(fname, "variable")
                                if fvar:
                                    attributes.append(node_text(fvar, source))

    bases: list[str] = []
    deriving = find_child_by_type(node, "deriving")
    if deriving:
        for child in deriving.children:
            if child.type == "name":
                bases.append(node_text(child, source))
            elif child.type == "tuple":
                for tc in child.children:
                    if tc.type == "name":
                        bases.append(node_text(tc, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="data",
            bases=bases,
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_class(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
) -> None:
    name_node = find_child_by_type(node, "name")
    if name_node is None:
        return
    name = node_text(name_node, source)
    docstring = _extract_haddock(node, source)

    attributes: list[str] = []
    class_decls = find_child_by_type(node, "class_declarations")
    if class_decls:
        for child in class_decls.children:
            if child.type == "signature":
                sig_var = find_child_by_type(child, "variable")
                if sig_var:
                    attributes.append(node_text(sig_var, source))

    result.classes.append(
        ParsedClass(
            name=name,
            line_number=node.start_point[0] + 1,
            end_line_number=node.end_point[0] + 1,
            kind="class",
            bases=[],
            attributes=attributes,
            docstring=docstring,
        )
    )


def _handle_bind(
    node: tree_sitter.Node,
    source: bytes,
    result: FileParseResult,
    signatures: dict[str, tree_sitter.Node],
) -> None:
    var = find_child_by_type(node, "variable")
    if var is None:
        return
    name = node_text(var, source)
    if name in signatures:
        result.variables.append(name)
    else:
        result.variables.append(name)
