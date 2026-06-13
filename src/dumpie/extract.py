"""Core extraction: discover zips, unpack in modular or flat mode, sweep originals."""

from __future__ import annotations

import enum
import shutil
import zipfile
from pathlib import Path

from .fsutil import ARCHIVE_DIRNAME, NameAllocator, listdir_names, unique_dir
from .ui import console, summary


class Mode(enum.Enum):
    """How a run lays out the files it unpacks."""

    MODULAR = "modular"  # a folder per zip, internal structure kept
    FLAT = "flat"        # every file into the target, internal folders stripped


def collect_zips(target: Path) -> list[Path]:
    """All zips under ``target``, recursive. Skips any prior ``_dumped*`` archives."""
    found = []
    for p in sorted(target.rglob("*")):
        if not (p.is_file() and p.suffix.lower() == ".zip"):
            continue
        rel_parts = p.relative_to(target).parts
        if any(part.startswith(ARCHIVE_DIRNAME) for part in rel_parts[:-1]):
            continue
        found.append(p)
    return found


def _flat_members(zf: zipfile.ZipFile) -> list[tuple[zipfile.ZipInfo, str]]:
    """File members of a zip paired with their basename (internal folders stripped)."""
    out = []
    for member in zf.infolist():
        if member.is_dir():
            continue
        base = member.filename.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        if base:
            out.append((member, base))
    return out


def _sweep(zp: Path, archive_dir: Path, rel: Path) -> None:
    """Move a processed zip into the archive dir, mirroring its relative path."""
    slot = archive_dir / rel
    slot.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(zp), str(slot))


def _extract_modular(zp: Path, target: Path, archive_dir: Path, rel: Path) -> Path:
    """Unpack one zip into a folder of its own name. Returns the dest, relative to target."""
    dest = unique_dir(zp.parent / zp.stem)
    try:
        with zipfile.ZipFile(zp) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(f"corrupt member: {bad}")
            dest.mkdir(parents=True)
            zf.extractall(dest)
    except (zipfile.BadZipFile, OSError):
        if dest.exists() and not any(dest.iterdir()):
            dest.rmdir()
        raise
    _sweep(zp, archive_dir, rel)
    return dest.relative_to(target)


def _extract_flat(zp: Path, target: Path, archive_dir: Path) -> int:
    """Unpack one zip's files straight into ``target``, folders stripped.

    Returns the number of files that had to be auto-numbered to avoid a collision.
    Re-seeds its name allocator from the live directory each call, so files written
    by earlier zips in the same run are accounted for.
    """
    alloc = NameAllocator(listdir_names(target))
    written: list[Path] = []
    renamed = 0
    try:
        with zipfile.ZipFile(zp) as zf:
            bad = zf.testzip()
            if bad is not None:
                raise zipfile.BadZipFile(f"corrupt member: {bad}")
            for member, base in _flat_members(zf):
                chosen, was_renamed = alloc.take(base)
                renamed += was_renamed
                dest = target / chosen
                with zf.open(member) as src, open(dest, "wb") as out:
                    shutil.copyfileobj(src, out)
                written.append(dest)
    except (zipfile.BadZipFile, OSError):
        for f in written:  # a corrupt zip leaves nothing behind
            try:
                f.unlink()
            except OSError:
                pass
        raise
    return renamed


def _preview(target: Path, zips: list[Path], mode: Mode) -> int:
    """Report what a run would do without writing anything. Returns exit code 0."""
    alloc = NameAllocator(listdir_names(target)) if mode is Mode.FLAT else None
    for zp in zips:
        rel = zp.relative_to(target)
        if mode is Mode.MODULAR:
            dest_rel = rel.parent / zp.stem
            console.print(f"  [accent]·[/accent] {rel} [muted]→ {dest_rel}/[/muted]")
            continue
        try:
            with zipfile.ZipFile(zp) as zf:
                files = _flat_members(zf)
        except (zipfile.BadZipFile, OSError) as e:
            console.print(f"  [bad]✗[/bad] {rel} [muted]{e}[/muted]")
            continue
        assert alloc is not None
        renamed = sum(alloc.take(base)[1] for _, base in files)
        extra = f", {renamed} renamed" if renamed else ""
        console.print(f"  [accent]·[/accent] {rel} [muted]→ {len(files)} file(s){extra}[/muted]")
    console.print("\n  [muted]dry run — nothing written.[/muted]\n")
    return 0


def run(target: Path, mode: Mode, *, dry_run: bool = False) -> int:
    """Unpack every zip under ``target``. Returns a process exit code (0 ok, 1 errors)."""
    zips = collect_zips(target)
    if not zips:
        console.print(f"\n  [warn]nothing to do[/warn] — no zip files under [muted]{target}[/muted]\n")
        return 0

    console.print(f"\n  found [b]{len(zips)}[/b] zip{'s' if len(zips) != 1 else ''}\n")

    if dry_run:
        return _preview(target, zips, mode)

    archive_dir = unique_dir(target / ARCHIVE_DIRNAME)
    archive_dir.mkdir(parents=True)

    ok = failed = renamed = 0
    with console.status("[b]unpacking…[/b]", spinner="dots"):
        for zp in zips:
            rel = zp.relative_to(target)
            try:
                if mode is Mode.FLAT:
                    n = _extract_flat(zp, target, archive_dir)
                    _sweep(zp, archive_dir, rel)
                    renamed += n
                    note = f" ({n} renamed)" if n else ""
                    console.print(f"  [ok]✓[/ok] {rel} [muted]→ flattened{note}[/muted]")
                else:
                    dest = _extract_modular(zp, target, archive_dir, rel)
                    console.print(f"  [ok]✓[/ok] {rel} [muted]→ {dest}/[/muted]")
                ok += 1
            except (zipfile.BadZipFile, OSError) as e:
                failed += 1
                console.print(f"  [bad]✗[/bad] {rel} [muted]{e}[/muted]")

    if ok == 0 and archive_dir.exists() and not any(archive_dir.iterdir()):
        archive_dir.rmdir()

    rows = [("unpacked", f"[ok]{ok}[/ok]" + (f"  [bad]{failed} failed[/bad]" if failed else ""))]
    if mode is Mode.FLAT and renamed:
        rows.append(("auto-numbered", f"{renamed} file{'s' if renamed != 1 else ''}"))
    rows.append(("source", str(target)))
    if ok:
        rows.append(("archived zips", str(archive_dir)))
    summary("complete" if not failed else "complete with errors", not failed, rows)
    return 0 if not failed else 1
