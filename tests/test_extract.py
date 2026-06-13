"""Tests for zip discovery and modular/flat extraction."""

from __future__ import annotations

import zipfile

from dumpie.extract import Mode, collect_zips, run


def test_modular_run_keeps_structure(tmp_path, mkzip):
    mkzip(tmp_path / "alpha.zip", {"a.txt": b"A", "sub/b.txt": b"B"})
    rc = run(tmp_path, Mode.MODULAR)
    assert rc == 0
    assert (tmp_path / "alpha" / "a.txt").read_bytes() == b"A"
    assert (tmp_path / "alpha" / "sub" / "b.txt").read_bytes() == b"B"
    assert (tmp_path / "_dumped" / "alpha.zip").exists()
    assert not (tmp_path / "alpha.zip").exists()


def test_flat_run_strips_internal_folders(tmp_path, mkzip):
    mkzip(tmp_path / "alpha.zip", {"images/a.png": b"1", "notes.txt": b"n"})
    rc = run(tmp_path, Mode.FLAT)
    assert rc == 0
    assert (tmp_path / "a.png").read_bytes() == b"1"
    assert (tmp_path / "notes.txt").exists()
    assert not (tmp_path / "images").exists()
    assert (tmp_path / "_dumped" / "alpha.zip").exists()


def test_flat_numbers_collisions_across_zips(tmp_path, mkzip):
    mkzip(tmp_path / "one.zip", {"dir1/a.png": b"1"})
    mkzip(tmp_path / "two.zip", {"dir2/a.png": b"2"})
    rc = run(tmp_path, Mode.FLAT)
    assert rc == 0
    files = sorted(p.name for p in tmp_path.iterdir() if p.is_file())
    assert files == ["a.png", "a_2.png"]
    payloads = {(tmp_path / n).read_bytes() for n in ("a.png", "a_2.png")}
    assert payloads == {b"1", b"2"}  # nothing overwritten


def test_corrupt_zip_left_in_place(tmp_path):
    (tmp_path / "broken.zip").write_bytes(b"not a zip at all")
    with zipfile.ZipFile(tmp_path / "ok.zip", "w") as zf:
        zf.writestr("x.txt", b"x")
    rc = run(tmp_path, Mode.FLAT)
    assert rc == 1  # one failure -> nonzero exit
    assert (tmp_path / "broken.zip").exists()  # untouched
    assert (tmp_path / "_dumped" / "ok.zip").exists()
    assert (tmp_path / "x.txt").exists()


def test_collect_zips_skips_dumped(tmp_path, mkzip):
    mkzip(tmp_path / "_dumped" / "old.zip", {"a": b"a"})
    mkzip(tmp_path / "real.zip", {"b": b"b"})
    assert [p.name for p in collect_zips(tmp_path)] == ["real.zip"]


def test_nothing_to_do_is_clean_exit(tmp_path):
    assert run(tmp_path, Mode.FLAT) == 0
    assert not (tmp_path / "_dumped").exists()


def test_dry_run_writes_nothing(tmp_path, mkzip):
    mkzip(tmp_path / "a.zip", {"x.txt": b"x"})
    rc = run(tmp_path, Mode.FLAT, dry_run=True)
    assert rc == 0
    assert (tmp_path / "a.zip").exists()
    assert not (tmp_path / "x.txt").exists()
    assert not (tmp_path / "_dumped").exists()
