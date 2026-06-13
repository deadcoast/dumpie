"""Interactive landing page and Options submenu — dumpie's primary surface."""

from __future__ import annotations

from pathlib import Path

from rich.prompt import Prompt

from . import __version__
from .extract import Mode, run
from .flatten import flatten_directory
from .ui import console, greet


def _ask_path() -> Path | None:
    """Prompt for a directory. Blank input returns None (back to the menu)."""
    while True:
        raw = Prompt.ask("  [accent]path[/accent]", default="", show_default=False).strip().strip('"').strip("'")
        if not raw:
            return None
        target = Path(raw).expanduser().resolve()
        if not target.exists():
            console.print(f"  [bad]✗[/bad] no such path: [muted]{target}[/muted]")
            continue
        if not target.is_dir():
            console.print(f"  [bad]✗[/bad] not a directory: [muted]{target}[/muted]")
            continue
        return target


def _print_menu() -> None:
    console.print("  [b]what now?[/b]\n")
    console.print("   [accent]1[/accent]  flat dumpie     [muted]unpack everything into the folder, no subfolders[/muted]")
    console.print("   [accent]2[/accent]  modular dumpie  [muted]a folder per zip — keeps structure[/muted]")
    console.print("   [accent]3[/accent]  options")
    console.print("   [accent]q[/accent]  quit")
    console.print()


def _options() -> None:
    while True:
        console.print("  [b]options[/b]\n")
        console.print("   [accent]1[/accent]  flatten an existing directory  [muted]collapse an already-unpacked folder to files only[/muted]")
        console.print("   [accent]2[/accent]  about")
        console.print("   [accent]b[/accent]  back")
        console.print()
        choice = Prompt.ask("  [accent]›[/accent]", choices=["1", "2", "b"], show_choices=False, default="b")
        console.print()
        if choice == "1":
            target = _ask_path()
            if target is not None:
                flatten_directory(target)
        elif choice == "2":
            console.print(f"  [brand]dumpie[/brand] [muted]v{__version__}[/muted]")
            console.print("  [muted]unpacks every zip under a folder, then sweeps the originals into _dumped/.[/muted]")
            console.print("  [muted]flat = all files loose · modular = a folder per zip.[/muted]\n")
        else:
            return


def landing() -> int:
    """Run dumpie's interactive menu. Returns a process exit code."""
    greet()
    while True:
        _print_menu()
        choice = Prompt.ask("  [accent]›[/accent]", choices=["1", "2", "3", "q"], show_choices=False, default="1")
        console.print()
        if choice == "1":
            target = _ask_path()
            if target is not None:
                run(target, Mode.FLAT)
        elif choice == "2":
            target = _ask_path()
            if target is not None:
                run(target, Mode.MODULAR)
        elif choice == "3":
            _options()
        else:
            console.print("  [muted]later.[/muted]\n")
            return 0
