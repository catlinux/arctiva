# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center.core import snapshots


def test_count_only_numeric_dirs(tmp_path):
    for name in ("1", "2", "13"):
        (tmp_path / name).mkdir()
    (tmp_path / "otra").mkdir()
    (tmp_path / "7").write_text("no es una carpeta")
    assert snapshots.count(str(tmp_path)) == 3


def test_count_missing_dir(tmp_path):
    assert snapshots.count(str(tmp_path / "no-existe")) == -1


def test_free_bytes(tmp_path):
    assert snapshots.free_bytes(str(tmp_path)) > 0
    assert snapshots.free_bytes(str(tmp_path / "no-existe")) == -1
