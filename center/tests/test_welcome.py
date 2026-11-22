# SPDX-License-Identifier: GPL-3.0-or-later
import re
from pathlib import Path

import arctiva_center
from arctiva_center.__main__ import main
from arctiva_center.core import welcome

PKGBUILD = Path(__file__).resolve().parents[2] / "packages" / "arctiva-center" / "PKGBUILD"


def test_show_and_hide(tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    no_live = str(tmp_path / "no-existe")
    assert welcome.should_show(env, no_live)
    welcome.set_show_at_login(False, env)
    assert (tmp_path / "arctiva-center" / "welcome.done").exists()
    assert not welcome.should_show(env, no_live)
    welcome.set_show_at_login(True, env)
    assert welcome.should_show(env, no_live)
    welcome.set_show_at_login(True, env)  # sin el archivo, no falla


def test_always_in_live(tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    assert welcome.should_show(env, str(tmp_path))
    welcome.set_show_at_login(False, env)
    assert welcome.should_show(env, str(tmp_path))  # en la live ofrece instalar siempre


def test_welcome_exits_without_window_when_done(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    welcome.set_show_at_login(False)
    assert main(["--welcome"]) == 0  # sale antes de importar PySide6


def test_version_matches_pkgbuild():
    pkgver = re.search(r"^pkgver=(\S+)$", PKGBUILD.read_text(encoding="utf-8"), re.M).group(1)
    assert arctiva_center.__version__ == pkgver
