from __future__ import annotations

from symtext.parser.languages._bash import walk as _walk_bash
from symtext.parser.languages._cpp import walk as _walk_cpp
from symtext.parser.languages._csharp import walk as _walk_csharp
from symtext.parser.languages._dart import walk as _walk_dart
from symtext.parser.languages._elixir import walk as _walk_elixir
from symtext.parser.languages._go import walk as _walk_go
from symtext.parser.languages._haskell import walk as _walk_haskell
from symtext.parser.languages._hcl import walk as _walk_hcl
from symtext.parser.languages._java import walk as _walk_java
from symtext.parser.languages._kotlin import walk as _walk_kotlin
from symtext.parser.languages._lua import walk as _walk_lua
from symtext.parser.languages._objc import walk as _walk_objc
from symtext.parser.languages._perl import walk as _walk_perl
from symtext.parser.languages._php import walk as _walk_php
from symtext.parser.languages._protobuf import walk as _walk_protobuf
from symtext.parser.languages._python import walk as _walk_python
from symtext.parser.languages._r import walk as _walk_r
from symtext.parser.languages._ruby import walk as _walk_ruby
from symtext.parser.languages._rust import walk as _walk_rust
from symtext.parser.languages._scala import walk as _walk_scala
from symtext.parser.languages._sql import walk as _walk_sql
from symtext.parser.languages._swift import walk as _walk_swift
from symtext.parser.languages._typescript import walk as _walk_typescript
from symtext.parser.languages._zig import walk as _walk_zig
from symtext.parser.parser import WalkerFn

WALKERS: dict[str, WalkerFn] = {
    "python": _walk_python,
    "typescript": _walk_typescript,
    "javascript": _walk_typescript,
    "go": _walk_go,
    "rust": _walk_rust,
    "c": _walk_cpp,
    "cpp": _walk_cpp,
    "java": _walk_java,
    "kotlin": _walk_kotlin,
    "csharp": _walk_csharp,
    "php": _walk_php,
    "ruby": _walk_ruby,
    "swift": _walk_swift,
    "dart": _walk_dart,
    "elixir": _walk_elixir,
    "scala": _walk_scala,
    "lua": _walk_lua,
    "hcl": _walk_hcl,
    "bash": _walk_bash,
    "perl": _walk_perl,
    "protobuf": _walk_protobuf,
    "sql": _walk_sql,
    "r": _walk_r,
    "haskell": _walk_haskell,
    "zig": _walk_zig,
    "objc": _walk_objc,
}
