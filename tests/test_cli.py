"""Tests for argument parsing and dispatch."""

from __future__ import annotations

import pytest

from dumpie import cli
from dumpie.extract import Mode


def test_version_flag(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "dumpie" in capsys.readouterr().out


def test_flat_flag_dispatches(tmp_path, monkeypatch):
    seen = {}

    def fake_run(target, mode, *, dry_run=False):
        seen.update(target=target, mode=mode, dry_run=dry_run)
        return 0

    monkeypatch.setattr(cli, "run", fake_run)
    rc = cli.main(["--flat", str(tmp_path), "--dry-run"])
    assert rc == 0
    assert seen["mode"] is Mode.FLAT
    assert seen["dry_run"] is True
    assert seen["target"] == tmp_path.resolve()


def test_flatten_flag_dispatches(tmp_path, monkeypatch):
    seen = {}

    def fake_flatten(target, *, dry_run=False):
        seen["target"] = target
        return 0

    monkeypatch.setattr(cli, "flatten_directory", fake_flatten)
    rc = cli.main(["--flatten", str(tmp_path)])
    assert rc == 0
    assert seen["target"] == tmp_path.resolve()


def test_invalid_path_returns_2():
    assert cli.main(["--flat", "this/path/does/not/exist/xyz123"]) == 2


def test_no_args_opens_menu(monkeypatch):
    monkeypatch.setattr(cli, "landing", lambda: 7)
    assert cli.main([]) == 7
