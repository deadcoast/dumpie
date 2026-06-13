"""Tests for the amalgamator and installer/source synchronization."""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

import build

ROOT = Path(__file__).resolve().parent.parent


def test_amalgamation_compiles_and_is_complete():
    code = build.amalgamate()
    compile(code, "dumpie", "exec")  # raises on bad source
    assert "def main(" in code
    assert "def landing(" in code
    assert "def flatten_directory(" in code


def test_installers_and_script_match_source():
    # Guards against editing src/dumpie/ without re-running build.py.
    code = build.amalgamate().strip()
    assert code == (ROOT / "dumpie").read_text(encoding="utf-8").strip()
    assert code in (ROOT / "install.sh").read_text(encoding="utf-8")
    assert code in (ROOT / "install.ps1").read_text(encoding="utf-8")


def _run_generated(args, **kwargs):
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, str(ROOT / "dumpie"), *args],
        capture_output=True,
        text=True,
        env=env,
        **kwargs,
    )


def test_generated_script_reports_version():
    result = _run_generated(["--version"])
    assert result.returncode == 0, result.stderr
    assert "dumpie 0.2.0" in result.stdout


def test_generated_script_flattens_end_to_end(tmp_path):
    with zipfile.ZipFile(tmp_path / "a.zip", "w") as zf:
        zf.writestr("deep/x.txt", b"x")
    result = _run_generated(["--flat", str(tmp_path)])
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "x.txt").exists()
    assert (tmp_path / "_dumped" / "a.zip").exists()
