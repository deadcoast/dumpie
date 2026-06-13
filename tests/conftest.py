"""Shared test fixtures for dumpie."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest


def _make_zip(path: Path, entries: dict[str, bytes]) -> Path:
    """Write a zip at ``path`` whose members are ``{archive_name: bytes}``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in entries.items():
            zf.writestr(name, data)
    return path


@pytest.fixture
def mkzip():
    """Return a helper that builds zips from a name->bytes mapping."""
    return _make_zip
