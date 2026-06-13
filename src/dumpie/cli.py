"""Command-line entry: open the menu by default, or run one mode directly from flags."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import __version__
from .extract import Mode, run
from .flatten import flatten_directory
from .menu import landing
from .ui import console


def _resolve_dir(raw: str) -> Path | None:
    """Resolve and validate a directory argument, reporting why if it is rejected."""
    target = Path(raw).expanduser().resolve()
    if not target.exists():
        console.print(f"  [bad]✗[/bad] no such path: [muted]{target}[/muted]")
        return None
    if not target.is_dir():
        console.print(f"  [bad]✗[/bad] not a directory: [muted]{target}[/muted]")
        return None
    return target


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dumpie",
        description="Unpack every zip under a folder. Run with no arguments for the menu.",
    )
    parser.add_argument("--version", action="version", version=f"dumpie {__version__}")
    parser.add_argument("--dry-run", action="store_true", help="show what would happen, write nothing")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--flat", metavar="PATH", help="unpack all files into the folder, no subfolders")
    group.add_argument("--modular", metavar="PATH", help="a folder per zip (keeps structure)")
    group.add_argument("--flatten", metavar="PATH", help="flatten an already-unpacked folder to files only")
    return parser


def main(argv: list[str] | None = None) -> int:
    """dumpie entry point. With no mode flag, opens the interactive menu."""
    args = _build_parser().parse_args(argv)

    if args.flat is not None:
        target = _resolve_dir(args.flat)
        return run(target, Mode.FLAT, dry_run=args.dry_run) if target else 2
    if args.modular is not None:
        target = _resolve_dir(args.modular)
        return run(target, Mode.MODULAR, dry_run=args.dry_run) if target else 2
    if args.flatten is not None:
        target = _resolve_dir(args.flatten)
        return flatten_directory(target, dry_run=args.dry_run) if target else 2

    return landing()
