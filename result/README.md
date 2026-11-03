# Linux textutils (partial migration)

A small, typed Python 3.12+ library and Typer CLI, intended for Linux. Install
with `python3.12 -m pip install ./result` from the repository root.

```
textutils distance kitten sitting
textutils leet "Hello world"
textutils search ./documents needle --pattern '*.txt'
```

```python
from pathlib import Path
from textutils import TextFile, levenshtein_distance, search_files

print(levenshtein_distance('kitten', 'sitting'))
print(TextFile(Path('notes.txt')).search('hello'))
for path, matches in search_files(Path('documents'), 'hello'):
    print(path, matches)
```

The search is recursive, reads UTF-8, uses a four-process pool and emits matches
in completion order. It raises on unreadable or invalid UTF-8 files rather than
silently skipping them. Close the search generator if abandoning iteration early.
Protect process-spawning entry points with `if __name__ == '__main__':`.

## Scope and provenance

This is **not a complete migration** of the hundreds of source files in this
repository. It adapts a small, independently usable subset: Levenshtein and LCS
metrics from `pytextdist/edit_distance.py`, the sentence-tokenizer idea from
`textsplit/tools.py`, random casing from `spongetext/spongestring.py`, leetspeak
from `textfun/funciones.py`, and file search from `textfiles/txt_file.py`.
APIs are intentionally simplified and are not drop-in replacements: in
particular, distance functions compare raw Unicode characters rather than
pytextdist's default preprocessing; sentence fragments and whitespace handling
also differ. No other package has been migrated or validated. The checkout does
not provide an obvious license for these source files; review upstream licensing
and attribution before redistribution.

Run tests with `python -m unittest discover -s result/tests -v` after installing
the project and its dependencies in a Python 3.12+ environment.
