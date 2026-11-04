from __future__ import annotations

import hashlib
from collections.abc import Callable, Container, Iterator
from dataclasses import dataclass, field
from pathlib import Path

import tree_sitter
from tree_sitter_language_pack import get_parser as _get_ts_parser

from symtext.config import Settings

WalkerFn = Callable[[tree_sitter.Node, bytes, "FileParseResult"], None]


@dataclass
class ParsedFunction:
    name: str
    line_number: int
    end_line_number: int = 0
    args: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    docstring: str = ""
    class_context: str = ""
    cyclomatic_complexity: int = 1
    is_async: bool = False
    return_type: str = ""
    content_hash: str = ""


@dataclass
class ParsedClass:
    name: str
    line_number: int
    end_line_number: int = 0
    kind: str = "class"
    bases: list[str] = field(default_factory=list)
    attributes: list[str] = field(default_factory=list)
    docstring: str = ""
    content_hash: str = ""


@dataclass
class ParsedImport:
    module: str
    line_number: int
    alias: str = ""
    imported_name: str = ""


@dataclass
class ParsedCall:
    name: str
    line_number: int
    caller: str = ""
    full_call_name: str = ""


@dataclass
class FileParseResult:
    path: Path
    language: str
    functions: list[ParsedFunction] = field(default_factory=list)
    classes: list[ParsedClass] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    calls: list[ParsedCall] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    content_hash: str = ""
    size_bytes: int = 0


def _get_walkers() -> dict[str, WalkerFn]:
    from symtext.parser.languages import WALKERS

    return WALKERS


def _supported_languages() -> frozenset[str]:
    return frozenset(_get_walkers().keys())


class _LazyLanguages:
    _inner: frozenset[str] | None = None

    def _load(self) -> frozenset[str]:
        if self._inner is None:
            self._inner = _supported_languages()
        return self._inner

    def __contains__(self, item: object) -> bool:
        return item in self._load()

    def __iter__(self) -> Iterator[str]:
        return iter(self._load())

    def __len__(self) -> int:
        return len(self._load())

    def __repr__(self) -> str:
        return repr(self._load())


SUPPORTED_LANGUAGES: Container[str] = _LazyLanguages()

_PARSERS: dict[str, tree_sitter.Parser] = {}

_LANGUAGE_PACK_NAMES: dict[str, str] = {
    "javascript": "javascript",
    "typescript": "typescript",
    "python": "python",
    "go": "go",
    "rust": "rust",
    "c": "c",
    "cpp": "cpp",
    "java": "java",
    "csharp": "csharp",
    "kotlin": "kotlin",
    "php": "php",
    "ruby": "ruby",
    "swift": "swift",
    "dart": "dart",
    "elixir": "elixir",
    "scala": "scala",
    "lua": "lua",
    "hcl": "hcl",
    "bash": "bash",
    "perl": "perl",
    "protobuf": "proto",
    "sql": "sql",
    "r": "r",
    "haskell": "haskell",
    "zig": "zig",
    "objc": "objc",
}


def _get_parser(language: str) -> tree_sitter.Parser | None:
    if language in _PARSERS:
        return _PARSERS[language]
    pack_name = _LANGUAGE_PACK_NAMES.get(language, language)
    try:
        parser = _get_ts_parser(pack_name)
    except (KeyError, ValueError):
        return None
    _PARSERS[language] = parser
    return parser


def parse_file(path: Path, settings: Settings | None = None) -> FileParseResult | None:
    language = detect_language(path)
    if language is None:
        return None

    if settings:
        try:
            size_kb = path.stat().st_size / 1024
            if size_kb > settings.max_file_size_kb:
                return None
        except OSError:
            return None

    try:
        source = path.read_bytes()
    except OSError:
        return None

    return parse_bytes(path, source)


def parse_bytes(path: Path, source: bytes) -> FileParseResult | None:
    language = detect_language(path)
    if language is None:
        return None

    walker = _get_walkers().get(language)
    if walker is None:
        return None

    parser = _get_parser(language)
    if parser is None:
        return None

    content_hash = hashlib.sha256(source).hexdigest()
    tree = parser.parse(source)

    result = FileParseResult(
        path=path,
        language=language,
        content_hash=content_hash,
        size_bytes=len(source),
    )
    walker(tree.root_node, source, result)
    _compute_symbol_hashes(source, result)
    return result


def _compute_symbol_hashes(source: bytes, result: FileParseResult) -> None:
    lines = source.split(b"\n")
    for fn in result.functions:
        start = max(0, fn.line_number - 1)
        end = min(len(lines), fn.end_line_number or fn.line_number)
        if end <= start:
            end = start + 1
        fn.content_hash = hashlib.sha256(b"\n".join(lines[start:end])).hexdigest()
    for cls in result.classes:
        start = max(0, cls.line_number - 1)
        end = min(len(lines), cls.end_line_number or cls.line_number)
        if end <= start:
            end = start + 1
        cls.content_hash = hashlib.sha256(b"\n".join(lines[start:end])).hexdigest()


def detect_language(path: Path) -> str | None:
    ext_map: dict[str, str] = {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".mts": "typescript",
        ".cts": "typescript",
        ".java": "java",
        ".c": "c",
        ".h": "c",
        ".cpp": "cpp",
        ".hpp": "cpp",
        ".cc": "cpp",
        ".cxx": "cpp",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".dart": "dart",
        ".ex": "elixir",
        ".exs": "elixir",
        ".scala": "scala",
        ".lua": "lua",
        ".tf": "hcl",
        ".tfvars": "hcl",
        ".sh": "bash",
        ".bash": "bash",
        ".pl": "perl",
        ".pm": "perl",
        ".proto": "protobuf",
        ".sql": "sql",
        ".r": "r",
        ".R": "r",
        ".hs": "haskell",
        ".zig": "zig",
        ".m": "objc",
        ".mm": "objc",
    }
    return ext_map.get(path.suffix)
