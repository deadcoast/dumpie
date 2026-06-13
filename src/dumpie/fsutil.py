"""Filesystem helpers shared across dumpie: archive naming and collision-free names."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Iterable

ARCHIVE_DIRNAME = "_dumped"


def unique_dir(base: Path) -> Path:
    """Return a non-colliding directory path (name, name_2, name_3...)."""
    if not base.exists():
        return base
    n = 2
    while True:
        candidate = base.with_name(f"{base.name}_{n}")
        if not candidate.exists():
            return candidate
        n += 1


def _split_name(name: str) -> tuple[str, str]:
    """Split a filename into (stem, suffix); suffix includes its dot, '' if none."""
    suffix = PurePosixPath(name).suffix
    stem = name[: len(name) - len(suffix)] if suffix else name
    return stem, suffix


class NameAllocator:
    """Hands out collision-free names within a single directory.

    Seeded with the names already present, it numbers any later collision
    (``a.png`` -> ``a_2.png``) so a flatten never overwrites or drops a file.
    Comparison is case-insensitive, so names that differ only by case — which
    collide on Windows and default macOS filesystems — are still separated.
    """

    def __init__(self, existing: Iterable[str] = ()) -> None:
        self._taken = {n.lower() for n in existing}

    def take(self, name: str) -> tuple[str, bool]:
        """Reserve a usable name for ``name``. Returns (chosen_name, was_renamed)."""
        if name.lower() not in self._taken:
            self._taken.add(name.lower())
            return name, False
        stem, suffix = _split_name(name)
        n = 2
        while f"{stem}_{n}{suffix}".lower() in self._taken:
            n += 1
        chosen = f"{stem}_{n}{suffix}"
        self._taken.add(chosen.lower())
        return chosen, True


def listdir_names(target: Path) -> list[str]:
    """Top-level entry names in ``target``; an empty list if it cannot be read."""
    try:
        return os.listdir(target)
    except OSError:
        return []
