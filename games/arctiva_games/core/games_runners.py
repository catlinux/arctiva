# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: ejecutores de Wine disponibles (D-G8) y elección del mejor para una receta.

Un ejecutor es el `wine` del sistema o una carpeta de Proton (GE-Proton, Proton-Wineland, UMU-Proton…) que
se lanza con `umu-run`. Cada receta trae una lista de preferencia de nombres (prefijos, sin distinguir
mayúsculas); se usa el primero que esté instalado y, entre varias versiones del mismo nombre, la más nueva."""
import re
import shutil
import zlib
from dataclasses import dataclass
from pathlib import Path

# Proton-Wineland primero: usa el driver nativo de Wayland y es el que funcionó con Battle.net en Plasma Wayland.
DEFAULT_PREFERENCE = ("Proton-Wineland", "GE-Proton", "UMU-Proton", "wine")
SEARCH_DIRS = (
    Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d",
    Path.home() / ".steam" / "root" / "compatibilitytools.d",
    Path.home() / ".local" / "share" / "lutris" / "runners" / "wine",
    Path("/usr/share/steam/compatibilitytools.d"),
)
SYSTEM = "wine"


@dataclass(frozen=True)
class Runner:
    name: str           # «wine» o el nombre de la carpeta de Proton
    path: str = ""      # carpeta de Proton; vacío para el wine del sistema

    @property
    def is_proton(self):
        return bool(self.path)


def _natural(name):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", name)]


def find_umu():
    return shutil.which("umu-run")


def list_runners(dirs=SEARCH_DIRS, which=shutil.which):
    """Carpetas de Proton con un ejecutable `proton`, más el `wine` del sistema si está instalado."""
    found, seen = [], set()
    for base in dirs:
        try:
            entries = sorted(Path(base).iterdir())
        except OSError:
            continue
        for d in entries:
            if d.is_dir() and (d / "proton").is_file() and d.name not in seen:
                seen.add(d.name)
                found.append(Runner(d.name, str(d)))
    if which("wine"):
        found.append(Runner(SYSTEM))
    return found


def choose(preference, runners, umu=True):
    """Primer ejecutor que cumpla la lista de preferencia. Sin umu-run, los de Proton no se pueden usar."""
    usable = [r for r in runners if umu or not r.is_proton]
    for want in preference or DEFAULT_PREFERENCE:
        want = want.lower()
        if want == SYSTEM:
            match = [r for r in usable if not r.is_proton]
        else:
            match = sorted((r for r in usable if r.name.lower().startswith(want)),
                           key=lambda r: _natural(r.name), reverse=True)
        if match:
            return match[0]
    return None


def umu_env(proton_path, slug):
    """Variables de umu-run para un juego. Como Faugus (que con ellas enlaza bien Battle.net):
    un GAMEID propio por juego, `UMU_CONTAINER_NSENTER=1` (los `umu-run` del mismo juego comparten el
    contenedor y, con él, el wineserver y la comunicación entre el lanzador y el juego) y Wayland
    desactivado salvo en Proton-Wineland, que lo trae pensado."""
    env = {"PROTONPATH": proton_path, "GAMEID": f"umu-arctiva{zlib.crc32(slug.encode()):08x}",
           "UMU_CONTAINER_NSENTER": "1"}
    if "wineland" not in proton_path.lower():
        env["PROTON_ENABLE_WAYLAND"] = "0"
    return env


def by_name(name, runners):
    return next((r for r in runners if r.name == name), None)
