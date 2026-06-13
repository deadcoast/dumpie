#!/usr/bin/env bash
# dumpie installer — run once:  bash install_dumpie.sh
# Installs the tool + its own private Python environment.
# After install, type `dumpie` in any terminal.
set -euo pipefail

APP_DIR="$HOME/.local/share/dumpie"
BIN_DIR="$HOME/.local/bin"
VENV="$APP_DIR/venv"

say()  { printf '\033[1m%s\033[0m\n' "$*"; }
fail() { printf '\033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

say "installing dumpie..."

# 1. need python3
command -v python3 >/dev/null 2>&1 || fail "python3 not found — install Python 3 first (https://python.org or 'brew install python3')"

# 2. private venv so nothing touches your system Python
mkdir -p "$APP_DIR" "$BIN_DIR"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV" 2>/dev/null || {
    # Debian/Ubuntu ship venv separately
    fail "python3-venv missing — run: sudo apt install python3-venv  (then re-run this installer)"
  }
fi
"$VENV/bin/pip" install --quiet --upgrade pip rich

# 3. drop the app
cat > "$APP_DIR/dumpie.py" << 'DUMPIE_EOF'
#!/usr/bin/env python3
"""dumpie — unpack every zip under a directory, then quarantine the originals."""

import sys
import zipfile
import shutil
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
from rich import box

ARCHIVE_DIRNAME = "_dumped"

console = Console()


def greet() -> None:
    console.print()
    console.print("[bold]dumpie[/bold] [dim]·[/dim] zip dump unpacker", highlight=False)
    console.print("[dim]feed it a directory. it unpacks every zip beneath it, then sweeps the originals aside.[/dim]")
    console.print()


def get_target() -> Path:
    while True:
        raw = Prompt.ask("[bold cyan]path[/bold cyan]").strip().strip('"').strip("'")
        if not raw:
            continue
        target = Path(raw).expanduser().resolve()
        if not target.exists():
            console.print(f"  [red]✗[/red] no such path: [dim]{target}[/dim]")
            continue
        if not target.is_dir():
            console.print(f"  [red]✗[/red] not a directory: [dim]{target}[/dim]")
            continue
        return target


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


def collect_zips(target: Path) -> list[Path]:
    """All zips under target, recursive. Skips any prior _dumped* archives."""
    found = []
    for p in sorted(target.rglob("*")):
        if not (p.is_file() and p.suffix.lower() == ".zip"):
            continue
        rel_parts = p.relative_to(target).parts
        if any(part.startswith(ARCHIVE_DIRNAME) for part in rel_parts[:-1]):
            continue
        found.append(p)
    return found


def main() -> int:
    greet()
    target = get_target()

    # Snapshot before extracting — zips nested inside archives we unpack
    # mid-run are not part of this pass.
    zips = collect_zips(target)
    if not zips:
        console.print(f"\n  [yellow]nothing to do[/yellow] — no zip files under [dim]{target}[/dim]\n")
        return 0

    console.print(f"\n  found [bold]{len(zips)}[/bold] zip{'s' if len(zips) != 1 else ''}\n")

    archive_dir = unique_dir(target / ARCHIVE_DIRNAME)
    archive_dir.mkdir(parents=True)

    ok = failed = 0

    with console.status("[bold]unpacking...[/bold]", spinner="dots"):
        for zp in zips:
            rel = zp.relative_to(target)
            dest = unique_dir(zp.parent / zp.stem)
            try:
                with zipfile.ZipFile(zp) as zf:
                    bad = zf.testzip()
                    if bad is not None:
                        raise zipfile.BadZipFile(f"corrupt member: {bad}")
                    dest.mkdir(parents=True)
                    zf.extractall(dest)
                # Mirror the relative structure inside the archive dir so
                # same-named zips from different subdirs never collide.
                slot = archive_dir / rel
                slot.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(zp), slot)
                ok += 1
                console.print(f"  [green]✓[/green] {rel} [dim]→ {dest.relative_to(target)}/[/dim]")
            except (zipfile.BadZipFile, OSError) as e:
                if dest.exists() and not any(dest.iterdir()):
                    dest.rmdir()
                failed += 1
                console.print(f"  [red]✗[/red] {rel} [dim]{e}[/dim]")

    if ok == 0 and not any(archive_dir.iterdir()):
        archive_dir.rmdir()

    table = Table(box=box.SIMPLE, show_header=False, pad_edge=False)
    table.add_column(style="dim", justify="right")
    table.add_column()
    table.add_row("unpacked", f"[green]{ok}[/green]" + (f"  [red]{failed} failed[/red]" if failed else ""))
    table.add_row("source", str(target))
    if ok:
        table.add_row("archived zips", str(archive_dir))

    console.print()
    console.print("[bold green]complete[/bold green]" if not failed else "[bold yellow]complete with errors[/bold yellow]")
    console.print(table)
    console.print()
    return 0 if not failed else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n[dim]aborted[/dim]")
        sys.exit(130)
DUMPIE_EOF

# 4. launcher on PATH
cat > "$BIN_DIR/dumpie" << LAUNCHER
#!/bin/sh
exec "$VENV/bin/python" "$APP_DIR/dumpie.py" "\$@"
LAUNCHER
chmod +x "$BIN_DIR/dumpie"

# 5. make sure ~/.local/bin is on PATH for future shells
ensure_path() {
  local rc="$1"
  grep -qs '\.local/bin' "$rc" 2>/dev/null && return 0
  printf '\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
  ADDED_RC="$rc"
}
ADDED_RC=""
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;  # already there
  *)
    case "${SHELL:-}" in
      */zsh)  ensure_path "$HOME/.zshrc" ;;
      */bash) ensure_path "$HOME/.bashrc" ;;
      *)      ensure_path "$HOME/.profile" ;;
    esac
    ;;
esac

say "✓ dumpie installed"
echo "  app:      $APP_DIR"
echo "  command:  $BIN_DIR/dumpie"
if [ -n "$ADDED_RC" ]; then
  echo
  echo "  PATH updated in $ADDED_RC — open a new terminal (or run: source $ADDED_RC)"
  echo "  then just type:  dumpie"
else
  echo
  echo "  ready — type:  dumpie"
fi
