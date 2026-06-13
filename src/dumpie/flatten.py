"""Flatten an already-extracted directory down to files only, archive preserved."""

from __future__ import annotations

import shutil
from pathlib import Path

from .fsutil import ARCHIVE_DIRNAME, NameAllocator, listdir_names
from .ui import console, summary


def _under_archive(rel: Path) -> bool:
    """True if a path (relative to target) lives inside the ``_dumped`` archive."""
    return bool(rel.parts) and rel.parts[0].startswith(ARCHIVE_DIRNAME)


def _nested_files(target: Path) -> list[Path]:
    """Every file under ``target`` that sits in a subfolder, excluding the archive."""
    files = []
    for p in sorted(target.rglob("*")):
        rel = p.relative_to(target)
        if _under_archive(rel):
            continue
        if p.is_file() and rel.parent != Path("."):
            files.append(p)
    return files


def _prune_empty_dirs(target: Path) -> int:
    """Remove now-empty subdirectories (deepest first). Skips the archive. Returns count."""
    removed = 0
    dirs = sorted(
        (p for p in target.rglob("*") if p.is_dir()),
        key=lambda p: len(p.relative_to(target).parts),
        reverse=True,
    )
    for d in dirs:
        if _under_archive(d.relative_to(target)):
            continue
        try:
            if not any(d.iterdir()):
                d.rmdir()
                removed += 1
        except OSError:
            pass
    return removed


def flatten_directory(target: Path, *, dry_run: bool = False) -> int:
    """Collapse every nested file in ``target`` up to the top level.

    Files already at the top stay put. Anything inside the ``_dumped`` archive is
    left untouched. Name collisions are auto-numbered so nothing is lost. After the
    moves, emptied subdirectories are removed. Returns a process exit code.
    """
    files = _nested_files(target)  # snapshot before we mutate the tree
    if not files:
        console.print(f"\n  [warn]nothing to flatten[/warn] — no nested files under [muted]{target}[/muted]\n")
        return 0

    console.print(f"\n  flattening [b]{len(files)}[/b] file{'s' if len(files) != 1 else ''}\n")

    alloc = NameAllocator(listdir_names(target))

    if dry_run:
        renamed = 0
        for f in files:
            chosen, was_renamed = alloc.take(f.name)
            renamed += was_renamed
            note = f" [muted]→ {chosen}[/muted]" if was_renamed else ""
            console.print(f"  [accent]·[/accent] {f.relative_to(target)}{note}")
        console.print("\n  [muted]dry run — nothing moved.[/muted]\n")
        return 0

    moved = renamed = failed = 0
    with console.status("[b]flattening…[/b]", spinner="dots"):
        for f in files:
            chosen, was_renamed = alloc.take(f.name)
            dest = target / chosen
            try:
                shutil.move(str(f), str(dest))
                moved += 1
                renamed += was_renamed
                note = f" [muted]→ {chosen}[/muted]" if was_renamed else ""
                console.print(f"  [ok]✓[/ok] {f.relative_to(target)}{note}")
            except OSError as e:
                failed += 1
                console.print(f"  [bad]✗[/bad] {f.relative_to(target)} [muted]{e}[/muted]")

    removed = _prune_empty_dirs(target)

    rows = [("flattened", f"[ok]{moved}[/ok]" + (f"  [bad]{failed} failed[/bad]" if failed else ""))]
    if renamed:
        rows.append(("auto-numbered", f"{renamed} file{'s' if renamed != 1 else ''}"))
    if removed:
        rows.append(("folders removed", str(removed)))
    rows.append(("target", str(target)))
    summary("flattened" if not failed else "flattened with errors", not failed, rows)
    return 0 if not failed else 1
