from __future__ import annotations

from dataclasses import replace

from .structured import NavigationEntry, TextBlock

_UNSET = 10**12


def _effective_start(entry: NavigationEntry) -> int | None:
    if entry.source_char_start is not None:
        return entry.source_char_start
    if (
        entry.fragment is None
        and entry.document_href is not None
        and entry.spine_index is not None
    ):
        return 0
    return None


def _entry_sort_key(entry: NavigationEntry) -> tuple[int, int, int, int]:
    start = _effective_start(entry)
    return (
        entry.spine_index if entry.spine_index is not None else _UNSET,
        start if start is not None else _UNSET,
        entry.level,
        entry.order,
    )


def annotate_blocks_with_navigation(
    blocks: list[TextBlock],
    navigation: list[NavigationEntry],
) -> list[TextBlock]:
    nav_entries = [
        entry
        for entry in navigation
        if entry.source != "fallback"
        and entry.document_href is not None
        and entry.spine_index is not None
        and _effective_start(entry) is not None
    ]
    nav_entries.sort(key=_entry_sort_key)

    annotated: list[TextBlock] = []
    for block in blocks:
        block_spine = block.spine_index
        block_start = block.outer_char_start
        block_end = block.outer_char_end
        if block_spine is None:
            annotated.append(block)
            continue

        active: NavigationEntry | None = None
        for entry in nav_entries:
            entry_spine = entry.spine_index
            entry_start = _effective_start(entry)
            if entry_spine is None or entry_start is None:
                continue

            if entry_spine < block_spine:
                active = entry
                continue

            if entry_spine > block_spine:
                break

            if entry_start <= block_start or block_start <= entry_start < block_end:
                active = entry
                continue

            break

        if active is None:
            annotated.append(block)
        else:
            annotated.append(
                replace(
                    block,
                    chapter_id=active.id,
                    chapter_title=active.title,
                )
            )

    return annotated
