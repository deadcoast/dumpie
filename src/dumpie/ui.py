"""Console, theme, greeting, and shared result rendering for dumpie's interface."""

from __future__ import annotations

import sys

from rich import box
from rich.console import Console
from rich.table import Table
from rich.theme import Theme


def _enable_windows_utf8() -> None:
    """Align Windows' console code page and Python's streams to UTF-8.

    Without this, dumpie's UTF-8 output (▌ · › — ✓) is decoded through the
    legacy Windows-1252 code page and shows up as mojibake (``â–Œ``, ``Â·``).
    Switching the console to code page 65001 and reconfiguring stdio to UTF-8
    makes what we emit and what the console reads agree. No-op off Windows, and
    best-effort everywhere (a redirected pipe or unusual host just falls back).
    """
    if sys.platform == "win32":
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except (AttributeError, OSError, ValueError):
            pass


_enable_windows_utf8()

THEME = Theme(
    {
        "accent": "bold cyan",
        "ok": "green",
        "bad": "red",
        "warn": "yellow",
        "muted": "dim",
        "brand": "bold cyan",
    }
)

console = Console(theme=THEME, highlight=False)


def greet() -> None:
    """Print dumpie's stylized landing header."""
    console.print()
    console.print("  [brand]▌ dumpie[/brand] [muted]· zip-dump unpacker[/muted]")
    console.print("  [muted]hand it a folder full of zips. it unpacks them and sweeps the originals aside.[/muted]")
    console.print()


def summary(title: str, ok: bool, rows: list[tuple[str, str]]) -> None:
    """Render a result banner and a right-aligned key/value table."""
    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column(style="muted", justify="right")
    table.add_column()
    for key, value in rows:
        table.add_row(key, value)
    console.print()
    console.print(f"[{'ok' if ok else 'warn'}][b]{title}[/b][/]")
    console.print(table)
    console.print()
