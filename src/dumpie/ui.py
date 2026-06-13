"""Console, theme, greeting, and shared result rendering for dumpie's interface."""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

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
