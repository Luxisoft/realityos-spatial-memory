from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _manual_import_module():
    path = Path(__file__).parents[1] / "scripts" / "import_manual_photos.py"
    spec = importlib.util.spec_from_file_location("realityos_manual_import", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manual_import_accepts_only_regular_staged_images(tmp_path: Path):
    module = _manual_import_module()
    root = tmp_path / "incoming"
    root.mkdir()
    image = root / "taladro.jpg"
    image.write_bytes(b"not-decoded-here")

    assert module.staged_images([str(image)], root) == [image.resolve()]

    outside = tmp_path / "private.jpg"
    outside.write_bytes(b"private")
    with pytest.raises(module.ImportError, match="staging directory"):
        module.staged_images([str(outside)], root)
