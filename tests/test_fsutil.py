"""Tests for collision-free name allocation and directory uniqueness."""

from __future__ import annotations

from dumpie.fsutil import NameAllocator, _split_name, unique_dir


def test_allocator_passes_through_unique():
    alloc = NameAllocator()
    assert alloc.take("x.txt") == ("x.txt", False)


def test_allocator_numbers_collisions():
    alloc = NameAllocator(["a.png"])
    assert alloc.take("a.png") == ("a_2.png", True)
    assert alloc.take("a.png") == ("a_3.png", True)


def test_allocator_preserves_suffix():
    alloc = NameAllocator(["report.tar.gz"])
    chosen, renamed = alloc.take("report.tar.gz")
    assert renamed is True
    assert chosen == "report.tar_2.gz"


def test_allocator_is_case_insensitive():
    # Windows and default macOS filesystems treat A.PNG and a.png as the same file.
    alloc = NameAllocator(["A.PNG"])
    chosen, renamed = alloc.take("a.png")
    assert renamed is True
    assert chosen == "a_2.png"


def test_split_name_handles_no_suffix():
    assert _split_name("README") == ("README", "")


def test_unique_dir(tmp_path):
    (tmp_path / "d").mkdir()
    assert unique_dir(tmp_path / "d").name == "d_2"
    assert unique_dir(tmp_path / "fresh") == tmp_path / "fresh"
