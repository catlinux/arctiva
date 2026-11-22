# SPDX-License-Identifier: GPL-3.0-or-later
"""El catálogo de extras y su sincronía con los perfiles del instalador."""
import os
import re
import tomllib
from pathlib import Path

import pytest

from arctiva_center.core import catalog, paths

REPO = Path(__file__).resolve().parents[2]
PROFILES = REPO / "installer" / "calamares" / "modules" / "packagechooser-perfiles.conf"
EXTRAS = paths.resolve().data / "extras.toml"


def installer_profiles():
    """id → paquetes de packagechooser-perfiles.conf (YAML sencillo, sin PyYAML)."""
    profiles, current, in_packages = {}, None, False
    for line in PROFILES.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\s*- id: (\S+)", line):
            current, in_packages = m.group(1), False
            profiles[current] = []
        elif re.match(r"\s*packages:", line):
            in_packages = True
        elif in_packages and (m := re.match(r"\s*- (\S+)$", line)):
            profiles[current].append(m.group(1))
        elif in_packages and line.strip() and not line.strip().startswith("-"):
            in_packages = False
    return profiles


def test_profiles_and_extras_in_sync():
    extras = {e["id"]: e.get("packages", []) for e in tomllib.loads(EXTRAS.read_text(encoding="utf-8"))["extra"]}
    profiles = installer_profiles()
    assert profiles["juegos"] and profiles["oficina"]
    assert extras["juegos"] == profiles["juegos"]
    assert extras["oficina"] == profiles["oficina"]


def test_catalog_valid_for_helper():
    data = tomllib.loads(EXTRAS.read_text(encoding="utf-8"))
    ids = [e["id"] for e in data["extra"]]
    assert len(ids) == len(set(ids))
    for e in data["extra"]:
        assert re.fullmatch(r"[a-z0-9-]{1,40}", e["id"])
        # Un extra es de pacman o de Flatpak, nunca de los dos (el ayudante solo acepta los de pacman).
        assert bool(e.get("packages")) != bool(e.get("flatpaks"))
        assert all(re.fullmatch(r"[a-z0-9@_+][a-z0-9@._+-]*", p)
                   for p in e.get("packages", []) + e.get("remove_also", []))
        assert all(re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", f) for f in e.get("flatpaks", []))
        assert set(e["name"]) == {"en", "es", "ca"} and set(e["description"]) == {"en", "es", "ca"}


def test_load_and_installed():
    extras = catalog.load(EXTRAS, ["ca_ES", "ca"])
    lts = next(e for e in extras if e.id == "kernel-lts")
    assert lts.name == "Nucli LTS"
    assert lts.installed({"linux", "linux-lts"}) and not lts.installed({"linux"})
    assert next(e for e in catalog.load(EXTRAS, ["de"]) if e.id == "oficina").name == "Office"


def test_flatpak_extras():
    extras = {e.id: e for e in catalog.load(EXTRAS, ["es"])}
    windows = extras["windows"]
    assert windows.name == "Programas de Windows" and windows.packages == () and windows.flatpaks
    assert not windows.installed(set()) and not windows.installed({"steam"})
    assert windows.installed(set(), {"com.usebottles.bottles"})
    assert {"heroic", "protonplus"} <= set(extras)
    # Los de pacman no cambian: instalados si están todos sus paquetes.
    assert extras["kernel-lts"].installed({"linux-lts"})


@pytest.mark.skipif(os.name != "posix", reason="el ayudante solo corre en POSIX")
def test_helper_refuses_flatpak_extras():
    """El ayudante solo acepta extras con paquetes de pacman: los de Flatpak no pasan por él."""
    import subprocess
    import sys
    helper = Path(__file__).resolve().parents[1] / "helper" / "arctiva-helper"
    code = (
        "import importlib.machinery, importlib.util, sys\n"
        "loader = importlib.machinery.SourceFileLoader('h', sys.argv[1])\n"
        "spec = importlib.util.spec_from_loader('h', loader)\n"
        "h = importlib.util.module_from_spec(spec); loader.exec_module(h)\n"
        "h.CATALOG = sys.argv[2]\n"
        "try:\n    h.load_extra('windows')\nexcept h.Refused:\n    print('refused')\n")
    out = subprocess.run([sys.executable, "-c", code, str(helper), str(EXTRAS)], capture_output=True, text=True)
    assert out.stdout.strip() == "refused", out.stderr
