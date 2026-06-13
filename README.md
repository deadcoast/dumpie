# dumpie

Interactive CLI that recursively unpacks every zip under a directory, then sweeps the originals into a single archive folder. Point it at a path full of zips, and it does the rest.

---

## Quick run

**macOS / Linux / WSL**
```bash
bash install_dumpie.sh   # once
dumpie                   # any new terminal
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy Bypass -File .\install_dumpie.ps1   # once
dumpie                                                          # any new terminal
```

Then `dumpie` greets you, asks for a path, and unpacks everything. That's the whole flow.

---

## What it does

Given a directory, dumpie:

1. Finds **every** `.zip` beneath the path, recursively — not just the top level.
2. Extracts each one into a folder of the same name, right next to where the zip lived (`sub/deep/foo.zip` → `sub/deep/foo/`).
3. Moves every successfully-unpacked zip into a single `_dumped/` folder at the root of the path, mirroring the original subfolder structure so same-named zips never collide.
4. Confirms completion, printing both the path you gave it and the path to the archived zips.

Corrupt or unreadable zips are left exactly where they are — `_dumped/` means "verified and processed," so anything that failed stays visible in place for you to deal with.

## Example

```
$ dumpie

dumpie · zip dump unpacker
feed it a directory. it unpacks every zip beneath it, then sweeps the originals aside.

path: ~/Downloads/dump

  found 4 zips

  ✓ alpha.zip       → alpha/
  ✓ sub/beta.zip    → sub/beta/
  ✗ broken.zip      File is not a zip file
  ✓ gamma.zip       → gamma/

complete with errors
      unpacked   3  1 failed
        source   /Users/you/Downloads/dump
 archived zips   /Users/you/Downloads/dump/_dumped
```

Before:
```
dump/
├── alpha.zip
├── broken.zip
├── gamma.zip
└── sub/
    └── beta.zip
```

After:
```
dump/
├── alpha/              ← unpacked
├── gamma/              ← unpacked
├── broken.zip          ← left in place (failed)
├── sub/
│   └── beta/           ← unpacked
└── _dumped/            ← originals swept here, structure mirrored
    ├── alpha.zip
    ├── gamma.zip
    └── sub/
        └── beta.zip
```

---

## Install (full)

The installer is a single self-contained file — the dumpie program is embedded inside it, so it's the only thing you need to download. Running it does four things:

- Creates a **private Python virtual environment** just for dumpie, so it never touches your system Python or any other project's packages.
- Installs dumpie's one dependency ([Rich](https://github.com/Textualize/rich), for the colored output) into that environment.
- Drops the dumpie program and a small launcher.
- Adds the launcher to your `PATH` so `dumpie` works as a plain command — no typing `python`, no long command strings.

### Requirements

- **Python 3** must already be installed.
  - macOS: `brew install python3`, or from [python.org](https://python.org).
  - Linux: usually preinstalled; on Debian/Ubuntu you may also need `sudo apt install python3-venv`.
  - Windows: install from [python.org](https://python.org) and **check "Add python.exe to PATH"** during setup.

If Python is missing, the installer stops and tells you exactly what to install.

### macOS / Linux / WSL

```bash
bash install_dumpie.sh
```

Files land in:
- `~/.local/share/dumpie/` — the program and its venv
- `~/.local/bin/dumpie` — the launcher

If `~/.local/bin` isn't already on your `PATH`, the installer appends it to the right shell config (`.zshrc`, `.bashrc`, or `.profile`) and tells you to open a new terminal once.

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install_dumpie.ps1
```

Files land in:
- `%LOCALAPPDATA%\dumpie\` — the program and its venv
- `%LOCALAPPDATA%\dumpie\bin\dumpie.cmd` — the launcher (works in both PowerShell and cmd)

The launcher folder is added to your **user** `PATH` (no admin needed). It works immediately in the window you ran the installer from; other already-open terminals need to be restarted.

---

## Usage

1. Type `dumpie`.
2. At the `path:` prompt, type or paste a directory path and press Enter. Quoted and drag-and-dropped paths are handled automatically.
3. dumpie unpacks everything and prints a summary.

If you point it at a directory with no zips, it says so and exits without creating anything.

### Re-running on the same folder

Safe. dumpie ignores its own `_dumped/` archives on subsequent runs, so pointing it at an already-processed folder only picks up zips you've added since (or ones that failed last time).

### Collisions

If a destination folder already exists, dumpie extracts to a numbered variant (`alpha/` → `alpha_2/`) rather than overwriting. The same applies to the `_dumped/` folder itself.

---

## Updating

Re-run the installer. It overwrites the program in place and refreshes dependencies.

## Uninstall

**macOS / Linux / WSL**
```bash
rm -rf ~/.local/share/dumpie ~/.local/bin/dumpie
```

**Windows**
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\dumpie"
```
The `PATH` entry is harmless if left, but you can remove the `...\dumpie\bin` entry from your user PATH via *Settings → Environment Variables* if you want it gone.

---

## Notes & limitations

- **Exit codes:** `0` if everything unpacked cleanly, `1` if any zip failed (useful for scripting).
- **Recursion snapshot:** dumpie lists all zips *before* it starts extracting, so a zip that only appears after another is unpacked is not pulled into the same run. Run it again to catch those.
- **Long paths (Windows):** very deeply nested archives can exceed the legacy 260-character path limit on older Windows configurations. If you hit this, enable long-path support in Windows, or extract closer to the drive root.
- **Supported archives:** `.zip` only. No `.7z` / `.rar` / `.tar` (yet).
