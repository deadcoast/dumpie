# dumpie

Interactive CLI that recursively unpacks every zip under a directory, then sweeps the originals into a single archive folder. Point it at a path full of zips and pick how you want them laid out — **flat** (every file loose) or **modular** (a folder per zip).

---

## Quick run

**macOS / Linux / WSL**
```bash
bash install.sh   # once
dumpie            # any new terminal
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1   # once
dumpie                                                   # any new terminal
```

Then `dumpie` greets you and shows a short menu. Pick a number, give it a path, done.

---

## The menu

```
  ▌ dumpie · zip-dump unpacker
  hand it a folder full of zips. it unpacks them and sweeps the originals aside.

  what now?

   1  flat dumpie     unpack everything into the folder, no subfolders
   2  modular dumpie  a folder per zip — keeps structure
   3  options
   q  quit
```

- **flat dumpie** — unpacks every zip and drops all the files straight into the folder, discarding the folders *inside* each zip. Two files that would land on the same name are auto-numbered (`a.png`, `a_2.png`, …) so nothing is ever overwritten or lost.
- **modular dumpie** — unpacks each zip into a folder of its own name, right where the zip lived (`sub/deep/foo.zip` → `sub/deep/foo/`), keeping each archive's internal structure.
- **options** — the less-common tools, kept off the main surface:
  - **flatten an existing directory** — already ran modular and changed your mind? This collapses an already-unpacked folder down to files only, same auto-numbering, leaving `_dumped/` untouched.
  - **about**

In every mode the originals are swept into a single `_dumped/` folder at the root of the path. Corrupt or unreadable zips are left exactly where they are — `_dumped/` means "verified and processed," so anything that failed stays visible in place for you to deal with.

## Example — modular

```
Before                          After
dump/                           dump/
├── alpha.zip                   ├── alpha/              ← unpacked
├── broken.zip                  ├── gamma/              ← unpacked
├── gamma.zip                   ├── broken.zip          ← left in place (failed)
└── sub/                        ├── sub/
    └── beta.zip                │   └── beta/           ← unpacked
                                └── _dumped/            ← originals, structure mirrored
                                    ├── alpha.zip
                                    ├── gamma.zip
                                    └── sub/
                                        └── beta.zip
```

## Example — flat

```
Before                          After
dump/                           dump/
├── photos.zip                  ├── a.png               ← from photos.zip (img/a.png)
│     └ img/a.png               ├── b.png               ← from photos.zip (img/b.png)
│     └ img/b.png               ├── a_2.png             ← from icons.zip (a.png) — auto-numbered
└── icons.zip                   └── _dumped/
      └ a.png                       ├── photos.zip
                                    └── icons.zip
```

---

## Power-user flags

The menu is the whole experience; you never need flags. But for scripting or CI, every mode is reachable directly:

```bash
dumpie --flat    <path>   # flat unpack
dumpie --modular <path>   # modular unpack
dumpie --flatten <path>   # flatten an already-unpacked folder
dumpie --dry-run --flat <path>   # show the plan, write nothing
dumpie --version
```

Exit code is `0` when everything unpacked cleanly, `1` if any zip failed, `2` for a bad path argument.

---

## Install (full)

The installer is a single self-contained file — the dumpie program is embedded inside it, so it's the only thing you need to download. Running it:

- Creates a **private Python virtual environment** just for dumpie, so it never touches your system Python or any other project's packages.
- Installs dumpie's one dependency ([Rich](https://github.com/Textualize/rich), for the colored output) into that environment.
- Drops the dumpie program and a small launcher.
- Adds the launcher to your `PATH` so `dumpie` works as a plain command.

### Requirements

- **Python 3** must already be installed.
  - macOS: `brew install python3`, or from [python.org](https://python.org).
  - Linux: usually preinstalled; on Debian/Ubuntu you may also need `sudo apt install python3-venv`.
  - Windows: install from [python.org](https://python.org) and **check "Add python.exe to PATH"** during setup.

If Python is missing, the installer stops and tells you exactly what to install.

### macOS / Linux / WSL

```bash
bash install.sh
```

Files land in `~/.local/share/dumpie/` (program + venv) and `~/.local/bin/dumpie` (launcher). If `~/.local/bin` isn't on your `PATH`, the installer appends it to the right shell config and tells you to open a new terminal once.

### Windows

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Files land in `%LOCALAPPDATA%\dumpie\` (program + venv) and `%LOCALAPPDATA%\dumpie\bin\dumpie.cmd` (launcher, works in PowerShell and cmd). The launcher folder is added to your **user** `PATH` (no admin needed).

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
The `PATH` entry is harmless if left; remove the `...\dumpie\bin` entry via *Settings → Environment Variables* if you want it gone.

---

## Notes & limitations

- **Re-running is safe.** dumpie ignores its own `_dumped/` archives, so pointing it at an already-processed folder only picks up zips you've added since (or ones that failed last time).
- **Collisions never overwrite.** Modular destinations that already exist get a numbered variant (`alpha/` → `alpha_2/`); flat/flatten files get a numbered variant (`a.png` → `a_2.png`).
- **Recursion snapshot:** dumpie lists all zips *before* it starts, so a zip that only appears after another is unpacked is not pulled into the same run. Run it again to catch those.
- **Long paths (Windows):** very deeply nested archives can exceed the legacy 260-character path limit on older Windows configurations. Enable long-path support, or extract closer to the drive root.
- **Supported archives:** `.zip` only. No `.7z` / `.rar` / `.tar` (yet).

---

## Development

The program is developed as a small package under `src/dumpie/` (one module per concern: `cli`, `menu`, `extract`, `flatten`, `fsutil`, `ui`). What ships is a single file — `build.py` amalgamates the package into the root `dumpie` script and embeds that same source into both installers, so source, script, and installers never drift.

```bash
python build.py                  # rebuild dumpie + installers from src/
uv run --group dev pytest -q     # run the test suite
```

A test asserts the installers contain the current amalgamated source, so it fails if you edit `src/dumpie/` without re-running `build.py`.
