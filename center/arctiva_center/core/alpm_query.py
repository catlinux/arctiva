# SPDX-License-Identifier: GPL-3.0-or-later
"""Consultas a pacman con pyalpm en solo lectura (decisión 4 de la fase 6).

Usa la base de sincronización temporal de `checkupdates` (CHECKUPDATES_DB), la misma del módulo de
Actualizaciones, y nunca la real: consultar la tienda no puede provocar actualizaciones parciales."""
import os
from dataclasses import dataclass
from pathlib import Path

REPOS = ("core", "extra", "multilib")


def sync_db_path(env=os.environ):
    return Path(env.get("CHECKUPDATES_DB") or Path.home() / ".cache" / "arctiva-center" / "syncdb")


@dataclass(frozen=True)
class PackageInfo:
    name: str
    version: str
    repo: str
    download_size: int
    installed_size: int
    installed: bool = False


class AlpmQuery:
    """Envoltorio de pyalpm; `pyalpm` se importa aquí para que el resto funcione sin él."""

    def __init__(self, db_path=None, repos=REPOS, handle_factory=None):
        if handle_factory is None:
            import pyalpm
            handle_factory = pyalpm.Handle
            self._optional = pyalpm.SIG_DATABASE_OPTIONAL
        else:
            self._optional = 0
        self.handle = handle_factory("/", str(db_path or sync_db_path()))
        self.dbs = [self.handle.register_syncdb(r, self._optional) for r in repos]
        self._local = self.handle.get_localdb()

    def installed_names(self):
        return {p.name for p in self._local.pkgcache}

    def explicit_names(self):
        return {p.name for p in self._local.pkgcache if p.reason == 0}

    def info(self, name):
        local = self._local.get_pkg(name)
        for db in self.dbs:
            pkg = db.get_pkg(name)
            if pkg:
                return PackageInfo(name, pkg.version, db.name, pkg.download_size, pkg.isize, local is not None)
        if local:
            return PackageInfo(name, local.version, "local", 0, local.isize, True)
        return None

    def infos(self, names):
        return {n: i for n in names if (i := self.info(n))}
