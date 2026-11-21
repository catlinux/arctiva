# SPDX-License-Identifier: GPL-3.0-or-later
"""El catálogo de extras y su sincronía con los perfiles del instalador."""
import re
import tomllib
from pathlib import Path

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
    extras = {e["id"]: e["packages"] for e in tomllib.loads(EXTRAS.read_text(encoding="utf-8"))["extra"]}
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
        assert e["packages"] and all(re.fullmatch(r"[a-z0-9@_+][a-z0-9@._+-]*", p)
                                     for p in e["packages"] + e.get("remove_also", []))
        assert set(e["name"]) == {"en", "es", "ca"} and set(e["description"]) == {"en", "es", "ca"}


def test_load_and_installed():
    extras = catalog.load(EXTRAS, ["ca_ES", "ca"])
    lts = next(e for e in extras if e.id == "kernel-lts")
    assert lts.name == "Nucli LTS"
    assert lts.installed({"linux", "linux-lts"}) and not lts.installed({"linux"})
    assert next(e for e in catalog.load(EXTRAS, ["de"]) if e.id == "oficina").name == "Office"
