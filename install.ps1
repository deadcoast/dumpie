# dumpie installer for Windows — run once in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\install_dumpie.ps1
# After install, type `dumpie` in any new terminal (PowerShell or cmd).
$ErrorActionPreference = "Stop"

function Say($msg)  { Write-Host $msg -ForegroundColor White }
function Fail($msg) { Write-Host "x $msg" -ForegroundColor Red; exit 1 }

Say "installing dumpie..."

# 1. find Python (py launcher first, then python on PATH)
$python = $null
foreach ($cand in @("py", "python", "python3")) {
    $cmd = Get-Command $cand -ErrorAction SilentlyContinue
    if ($cmd) {
        # reject the Microsoft Store stub that just opens the store
        $ver = & $cand --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $ver -match "Python 3") { $python = $cand; break }
    }
}
if (-not $python) {
    Fail "Python 3 not found. Install it from https://python.org (check 'Add python.exe to PATH'), then re-run this."
}

# 2. private venv — nothing touches your system Python
$appDir = Join-Path $env:LOCALAPPDATA "dumpie"
$binDir = Join-Path $appDir "bin"
$venv   = Join-Path $appDir "venv"
$venvPy = Join-Path $venv "Scripts\python.exe"

New-Item -ItemType Directory -Force -Path $appDir, $binDir | Out-Null
if (-not (Test-Path $venvPy)) {
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail "couldn't create venv" }
}
& $venvPy -m pip install --quiet --upgrade pip rich
if ($LASTEXITCODE -ne 0) { Fail "pip install failed" }

# 3. drop the app
$appPy = Join-Path $appDir "dumpie.py"
$source = @'
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
'@
Set-Content -Path $appPy -Value $source -Encoding UTF8

# 4. launcher shim on PATH (works from cmd AND PowerShell)
$shim = Join-Path $binDir "dumpie.cmd"
$shimBody = "@echo off`r`n`"$venvPy`" `"$appPy`" %*"
Set-Content -Path $shim -Value $shimBody -Encoding ASCII

# 5. add the shim dir to the user PATH if it's not there
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if (-not ($userPath -split ";" | Where-Object { $_ -eq $binDir })) {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", "User")
    $pathAdded = $true
}
# also current session, so it works immediately in this window
if (-not (($env:Path -split ";") -contains $binDir)) { $env:Path += ";$binDir" }

Say ""
Say "+ dumpie installed"
Say "  app:      $appDir"
Say "  command:  $shim"
Say ""
if ($pathAdded) {
    Say "  PATH updated - works in THIS window now; other open terminals need a restart."
}
Say "  type:  dumpie"
