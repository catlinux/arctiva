# SPDX-License-Identifier: GPL-3.0-or-later
"""Catálogo de extras (extras.toml) tal como lo muestra la ventana."""
import tomllib
from dataclasses import dataclass

from . import i18n


@dataclass(frozen=True)
class Extra:
    id: str
    name: str
    description: str
    icon: str
    packages: tuple
    flatpaks: tuple = ()

    def installed(self, installed_packages, installed_flatpaks=frozenset()):
        if not self.packages and not self.flatpaks:
            return False
        return (all(p in installed_packages for p in self.packages)
                and all(f in installed_flatpaks for f in self.flatpaks))


def load(path, languages=("en",)):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    return [Extra(e["id"], _pick(e.get("name", {}), languages, e["id"]),
                  _pick(e.get("description", {}), languages, ""), e.get("icon", "package-x-generic"),
                  tuple(e.get("packages", [])), tuple(e.get("flatpaks", [])))
            for e in data.get("extra", [])]


def _pick(texts, languages, default):
    for name in i18n.catalog_candidates(languages):
        if name in texts:
            return texts[name]
    return texts.get("en", default)
