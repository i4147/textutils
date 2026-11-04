from __future__ import annotations

from typing import Any

_DEFAULT_LIMIT = 200

_MAX_LIMIT = 10_000
_MAX_DEPTH = 64


TOOLS: list[dict[str, Any]] = [
    {
        "name": "summarize",
        "description": (
            "Start here. Get per-file summaries for a directory: each file's language, "
            "function count, class names (with bases), the top functions ranked by "
            "how many callers they have, and total inbound/outbound call edges per file "
            "(total_callers, total_callees) for spotting hub modules. "
            "One call gives you enough to decide where to dig deeper with symbols(). "
            "Call with no arguments to summarize the whole project."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Directory to summarize. Defaults to project root. Accepts relative paths (resolved from cwd)."
                    ),
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "search_symbols",
        "description": (
            "Find functions, classes, files, or modules by name or docstring content. "
            "Unlike grep, this searches both symbol names AND docstrings — so you can "
            "find symbols by intent (e.g. 'handles authentication') not just text. "
            "Use this to discover exact names before calling get_callers or get_callees. "
            "Returns: [{name, path, line_number, docstring, _label}]. "
            "An empty list means no matches — try a shorter or broader substring."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Name, substring, or docstring keyword to search for "
                        "(e.g. 'parse', 'UserModel', 'handles authentication')"
                    ),
                },
                "label": {
                    "type": "string",
                    "enum": ["Function", "Class", "File", "Module"],
                    "description": ("Filter to a specific symbol type. Omit to search all types."),
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum number of results to return.",
                },
                "exclude_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Directory prefixes to exclude from results "
                        "(e.g. ['tests/', 'vendor/']). Paths are matched as substrings."
                    ),
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
                "is_async": {
                    "type": "boolean",
                    "description": "Filter to async functions only (true) or sync only (false).",
                },
                "return_type": {
                    "type": "string",
                    "description": (
                        "Filter by return type substring (e.g. 'error', 'str', 'None'). "
                        "Only matches functions with annotated return types."
                    ),
                },
                "has_arg": {
                    "type": "string",
                    "description": (
                        "Filter to functions that have a parameter matching this substring "
                        "(e.g. 'path', 'config', 'db')."
                    ),
                },
            },
            "required": ["query"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "get_callers",
        "description": (
            "Find all functions that call a specific function. "
            "Unlike grep, this follows resolved call edges through the code graph — "
            "no false positives from comments, strings, or similarly-named functions. "
            "At depth=1, includes source context around each call site. "
            "Accepts substrings — auto-resolves when unambiguous. "
            "Returns: [{caller, caller_path, caller_line, call_site_line, context}]. "
            "An empty list means no callers exist in the indexed codebase."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Function name or substring (e.g. 'parse_file'). "
                        "Auto-resolves if unambiguous; returns disambiguation list otherwise."
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "File path to disambiguate when multiple functions share the same name. "
                        "Accepts relative paths (resolved from cwd)."
                    ),
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": ("Traversal depth: 1 = direct callers only, 2 = callers of callers, 0 = unlimited."),
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
            },
            "required": ["name"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "get_callees",
        "description": (
            "Find all functions that a specific function calls. "
            "Unlike grep, this traces actual call relationships through the code graph, "
            "not just text matches. At depth=1, includes source context around each call site. "
            "Accepts substrings — auto-resolves when unambiguous. "
            "Returns: [{callee, callee_path, callee_line, call_site_line, context}]. "
            "An empty list means the function makes no calls to other indexed functions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Function name or substring (e.g. 'build_graph'). "
                        "Auto-resolves if unambiguous; returns disambiguation list otherwise."
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "File path to disambiguate when multiple functions share the same name. "
                        "Accepts relative paths (resolved from cwd)."
                    ),
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": ("Traversal depth: 1 = direct callees only, 2 = callees of callees, 0 = unlimited."),
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
            },
            "required": ["name"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "get_importers",
        "description": (
            "Find all files that import a given module. "
            "Unlike grep, this gives clean, structured import data with no false positives "
            "from comments, strings, or partial matches. "
            "Accepts substrings — auto-resolves when unambiguous (e.g. 'config' works if "
            "only one module matches). "
            "Returns: [{file_path, imported_name, alias, line_number}]. "
            "An empty list means no files import this module."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "module": {
                    "type": "string",
                    "description": ("Module name or substring (e.g. 'os', 'config', 'graphdb')."),
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
            },
            "required": ["module"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "get_dependencies",
        "description": (
            "Find all modules that a specific file imports — the outbound dependency list. "
            "This is the inverse of get_importers: get_importers shows who imports a module, "
            "get_dependencies shows what a file depends on. "
            "Use this to assess change safety or understand a file before modifying it. "
            "Returns: [{module, imported_name, alias, line_number}]. "
            "An empty list means the file has no imports."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": ("File path to inspect. Accepts relative paths (resolved from cwd)."),
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
            },
            "required": ["path"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "path_between",
        "description": (
            "Find the shortest call chain between two functions. "
            "Unlike get_callers with high depth (which fans out in all directions), "
            "this returns a single directed path from source to target. "
            "Use this to trace data flow or understand how a change in one layer "
            "reaches another. "
            "Returns: [{step, name, path, line_number}] ordered from source to target. "
            "An empty list means no call path exists within max_depth."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": ("Source function name or substring. Auto-resolves if unambiguous."),
                },
                "target": {
                    "type": "string",
                    "description": ("Target function name or substring. Auto-resolves if unambiguous."),
                },
                "source_path": {
                    "type": "string",
                    "description": "File path to disambiguate the source function.",
                },
                "target_path": {
                    "type": "string",
                    "description": "File path to disambiguate the target function.",
                },
                "max_depth": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of hops to search. Default 10.",
                },
            },
            "required": ["source", "target"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "get_hierarchy",
        "description": (
            "Explore class inheritance — find parent classes, child classes, or both. "
            "Unlike grep, this traverses the full inheritance graph, resolving base class "
            "names to actual definitions across files. "
            "Accepts substrings — auto-resolves when unambiguous. "
            "Returns: [{name, path, relation}] where relation is 'ancestor' or 'descendant'. "
            "An empty list means the class has no inheritance relationships."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Class name or substring (e.g. 'BaseModel'). "
                        "Auto-resolves if unambiguous; returns disambiguation list otherwise."
                    ),
                },
                "direction": {
                    "type": "string",
                    "enum": ["up", "down", "both"],
                    "default": "both",
                    "description": "'up' = ancestors, 'down' = subclasses, 'both' = full tree.",
                },
            },
            "required": ["name"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "symbols",
        "description": (
            "List every function and class defined in a file or directory — full detail "
            "including names, line numbers, args, docstrings, and decorators. "
            "Use this after summarize() to inspect a specific file. "
            "Returns: [{name, path, line, kind, args, docstring, decorators, "
            "is_async, return_type, bases}]. Docstrings are truncated to the first line. "
            "An empty list means no symbols were found at the given path."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "File or directory path. Relative paths are resolved from cwd. "
                        "For directories, returns symbols from all files underneath."
                    ),
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
            },
            "required": ["path"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "unused_symbols",
        "description": (
            "Find functions with zero callers — likely dead code or unreached entrypoints. "
            "Unlike grep + manual review, this checks resolved CALLS edges, so functions "
            "called dynamically or via reflection may show as unused (false positives). "
            "By default, filters out likely entrypoints: dunder methods (__init__, __str__, etc.) "
            "and decorated functions (@app.route, @click.command, @pytest.fixture, etc.) "
            "which are typically invoked by frameworks. "
            "Returns: [{name, path, line, class_context, decorators}]. "
            "An empty list means everything in scope has at least one caller."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "Optional directory prefix to scope the search (e.g. 'src/'). Defaults to the whole project."
                    ),
                },
                "exclude_entrypoints": {
                    "type": "boolean",
                    "default": True,
                    "description": (
                        "Skip likely entrypoints (dunder methods, decorated functions). "
                        "Set false to see every uncalled function including framework hooks."
                    ),
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "changed_symbols",
        "description": (
            "Git-aware blast radius: what symbols changed between a git ref and the "
            "currently-indexed state, and who calls them. Replaces the manual workflow "
            "of `git diff --name-only` + parse changed functions + get_callers on each. "
            "Compares per-symbol content hashes (populated during indexing) against the "
            "same symbols parsed from `git show <ref>:<file>`, so renames, additions, "
            "and deletions are detected alongside modifications. "
            "Returns: [{name, path, line, kind, class_context, change_type, callers}] "
            "where change_type is 'added' | 'modified' | 'deleted'. "
            "Assumes the index is current — re-run `symtext index` if files changed "
            "outside the watcher."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {
                    "type": "string",
                    "default": "HEAD",
                    "description": (
                        "Git ref to diff against (e.g. 'HEAD', 'HEAD~1', 'main', a SHA). "
                        "Default 'HEAD' shows uncommitted changes in the working tree."
                    ),
                },
                "include_callers": {
                    "type": "boolean",
                    "default": True,
                    "description": (
                        "Attach direct callers to each modified or deleted function. "
                        "Set false for a faster, smaller response."
                    ),
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in results. Default false.",
                },
                "limit": {
                    "type": "integer",
                    "default": _DEFAULT_LIMIT,
                    "description": "Maximum number of results to return.",
                },
            },
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "shape",
        "description": (
            "Get the dimensions of the indexed codebase: node counts by type, "
            "relationship counts (calls, imports, inheritance), language breakdown, "
            "and per-directory symbol counts. Use this to understand what's indexed "
            "before calling summarize() or symbols(). "
            "Returns: {nodes, edges, languages, total_nodes, total_edges, directories}."
        ),
        "inputSchema": {"type": "object", "properties": {}},
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
    {
        "name": "describe_symbol",
        "description": (
            "Get everything known about a function or class in one call: "
            "full properties (args, docstring, complexity), callers, callees, "
            "inheritance, files that import this symbol's module, and source code. "
            "Unlike grep + read, this returns source, graph relationships, and metadata "
            "in a single round-trip. Accepts substrings — auto-resolves when unambiguous."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": ("Function or class name (exact or substring). Tries Function first, then Class."),
                },
                "path": {
                    "type": "string",
                    "description": "File path to disambiguate when multiple symbols share a name.",
                },
                "depth": {
                    "type": "integer",
                    "default": 1,
                    "description": (
                        "Caller/callee traversal depth. 1 = direct only (with source context), "
                        "2+ = transitive chain (no context). Use depth=2 or higher to see the "
                        "full blast radius of changing a function."
                    ),
                },
                "include_tests": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include test files in callers/callees. Default false.",
                },
            },
            "required": ["name"],
        },
        "annotations": {"readOnlyHint": True, "openWorldHint": False},
    },
]
