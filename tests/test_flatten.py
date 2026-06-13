"""Tests for flattening an already-extracted directory."""

from __future__ import annotations

from dumpie.flatten import flatten_directory


def test_flatten_moves_nested_files_up(tmp_path):
    (tmp_path / "alpha").mkdir()
    (tmp_path / "alpha" / "a.txt").write_text("A")
    (tmp_path / "beta").mkdir()
    (tmp_path / "beta" / "b.txt").write_text("B")
    rc = flatten_directory(tmp_path)
    assert rc == 0
    assert (tmp_path / "a.txt").read_text() == "A"
    assert (tmp_path / "b.txt").read_text() == "B"
    assert not (tmp_path / "alpha").exists()  # emptied dirs pruned
    assert not (tmp_path / "beta").exists()


def test_flatten_preserves_dumped_archive(tmp_path):
    (tmp_path / "_dumped").mkdir()
    (tmp_path / "_dumped" / "orig.zip").write_bytes(b"z")
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "f.txt").write_text("f")
    flatten_directory(tmp_path)
    assert (tmp_path / "_dumped" / "orig.zip").exists()
    assert (tmp_path / "f.txt").exists()


def test_flatten_numbers_collisions(tmp_path):
    for d, payload in (("d1", "1"), ("d2", "2")):
        (tmp_path / d).mkdir()
        (tmp_path / d / "a.txt").write_text(payload)
    flatten_directory(tmp_path)
    names = sorted(p.name for p in tmp_path.iterdir() if p.is_file())
    assert names == ["a.txt", "a_2.txt"]
    assert {(tmp_path / n).read_text() for n in names} == {"1", "2"}


def test_flatten_keeps_toplevel_files(tmp_path):
    (tmp_path / "top.txt").write_text("t")
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "n.txt").write_text("n")
    flatten_directory(tmp_path)
    assert (tmp_path / "top.txt").read_text() == "t"
    assert (tmp_path / "n.txt").read_text() == "n"


def test_flatten_dry_run_moves_nothing(tmp_path):
    (tmp_path / "d").mkdir()
    (tmp_path / "d" / "n.txt").write_text("n")
    rc = flatten_directory(tmp_path, dry_run=True)
    assert rc == 0
    assert (tmp_path / "d" / "n.txt").exists()
    assert not (tmp_path / "n.txt").exists()


def test_flatten_nothing_nested(tmp_path):
    (tmp_path / "top.txt").write_text("t")
    assert flatten_directory(tmp_path) == 0
