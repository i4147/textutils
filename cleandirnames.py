#!/usr/bin/env python3
"""
Strip trailing version specifiers from top-level entry names (in place)
and lowercase them.

Usage:
    python strip_versions.py [DIRECTORY]   # default: current directory

Version pattern: "-<digit><alnum . _>*" at the very end of the name.
    foo-1.2.3             -> foo
    texted-0b1            -> texted
    textract3-1.6.4.post1 -> textract3
    text-util-0.1.1       -> text-util        (only last -<ver> removed)
    Text.1-0.2.5          -> text.1
    help.txt              -> help.txt          (no version pattern)
"""

import os
import re
import sys
from pathlib import Path

VERSION_RE = re.compile(r"-\d[0-9a-zA-Z._]*$")
TMP_SUFFIX = ".__tmp_rename__"


def strip_version(name: str) -> str:
    return VERSION_RE.sub("", name).lower()


def _same_file(a: Path, b: Path) -> bool:
    try:
        return os.path.samefile(str(a), str(b))
    except OSError:
        return False


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not root.is_dir():
        sys.exit(f"not a directory: {root}")

    entries = sorted(root.iterdir())
    reserved = {e.name for e in entries}  # names currently on disk
    seen: set[str] = set()  # names we plan to create
    plan: list[tuple[Path, str, bool]] = []  # (src, new_name, case_only)

    # --- build the rename plan first (safer than renaming while iterating) ---
    for entry in entries:
        old = entry.name
        new = strip_version(old)
        if new == old:
            continue

        case_only = (old.lower() == new) and (old != new)
        target = entry.with_name(new)

        if new in seen:
            print(f"SKIP (duplicate): {old} -> {new}", file=sys.stderr)
            continue
        if new in reserved and not (case_only and _same_file(entry, target)):
            print(f"SKIP (exists):    {old} -> {new}", file=sys.stderr)
            continue

        seen.add(new)
        plan.append((entry, new, case_only))

    # --- apply renames ---
    for src, new, case_only in plan:
        dst = src.with_name(new)
        print(f"{src.name}  ->  {new}")
        if case_only:
            # case-insensitive filesystems need a two-step rename
            tmp = src.with_name(src.name + TMP_SUFFIX)
            src.rename(tmp)
            tmp.rename(dst)
        else:
            src.rename(dst)

    print(f"\nDone. {len(plan)} renamed.")


if __name__ == "__main__":
    main()
