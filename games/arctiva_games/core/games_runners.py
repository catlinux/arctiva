# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: ejecutores de Wine disponibles (D-G8) y elección del mejor para una receta.

Un ejecutor es el `wine` del sistema o una carpeta de Proton (GE-Proton, Proton-Wineland, UMU-Proton…) que
se lanza con `umu-run`. Cada receta trae una lista de preferencia de nombres (prefijos, sin distinguir
mayúsculas); se usa el primero que esté instalado y, entre varias versiones del mismo nombre, la más nueva."""
import os
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
# Nombre en clave de umu-run: descarga el último GE-Proton la primera vez que se usa (con su comprobación).
AUTO_GE = "GE-Proton"
# Sufijo de la ruta guardada para pedir Wayland nativo (experimental) con ese Proton.
WAYLAND = "+wayland"


@dataclass(frozen=True)
class Runner:
    name: str           # «wine» o el nombre de la carpeta de Proton
    path: str = ""      # carpeta de Proton (o nombre en clave de umu-run); vacío para el wine del sistema
    virtual: bool = False     # aún no está en el disco: umu-run lo descarga al usarlo
    auto_pick: bool = True    # puede elegirse solo; lo experimental solo se elige a mano

    @property
    def is_proton(self):
        return bool(self.path)

    @property
    def wayland(self):
        return self.path.endswith(WAYLAND) or "wineland" in self.path.lower()


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


def virtual_runners():
    """Ejecutores que umu-run descarga solo la primera vez (hace falta `umu-run`): GE-Proton, que es lo que
    suele hacer falta cuando solo está el wine del sistema, y su variante con Wayland nativo (experimental)."""
    return [Runner("GE-Proton (se descarga al usarlo)", AUTO_GE, virtual=True),
            Runner("GE-Proton, Wayland nativo (experimental, se descarga al usarlo)", AUTO_GE + WAYLAND,
                   virtual=True, auto_pick=False)]


def scan():
    """`(ejecutores, ruta de umu-run)` del equipo: los instalados y, si hay umu-run, los que se descargan solos."""
    umu = find_umu()
    runners = list_runners()
    return (runners + virtual_runners() if umu else runners), umu


def choose(preference, runners, umu=True):
    """Ejecutor que cumpla la lista de preferencia. Los de Proton instalados van antes que los que hay que
    descargar, y estos antes que el wine del sistema (que se queda corto con lanzadores como Battle.net), salvo
    que la receta solo pida wine. Sin umu-run, los de Proton no se pueden usar."""
    usable = [r for r in runners if umu or not r.is_proton]
    wants = [w.lower() for w in (preference or DEFAULT_PREFERENCE)]
    protons = [w for w in wants if w != SYSTEM]
    for virtual in (False, True):
        for want in protons:
            match = sorted((r for r in usable if r.virtual == virtual and r.auto_pick and r.name.lower().startswith(want)),
                           key=lambda r: _natural(r.name), reverse=True)
            if match:
                return match[0]
    if SYSTEM in wants:
        match = [r for r in usable if not r.is_proton]
        if match:
            return match[0]
    return None


def split_spec(spec):
    """Ruta guardada de un ejecutor → (ruta o nombre en clave, ¿Wayland nativo pedido a mano?)."""
    if spec.endswith(WAYLAND):
        return spec[:-len(WAYLAND)], True
    return spec, False


def proton_dir(spec, dirs=SEARCH_DIRS):
    """Carpeta real de un ejecutor guardado: la ruta tal cual o, si es un nombre en clave («GE-Proton»), la
    versión más nueva ya descargada. None si todavía no está en el disco."""
    path, _ = split_spec(spec)
    if os.path.isabs(path):
        return Path(path) if Path(path).is_dir() else None
    found = []
    for base in dirs:
        try:
            entries = Path(base).iterdir()
        except OSError:
            continue
        found += [d for d in entries if d.is_dir() and (d / "proton").is_file() and d.name.lower().startswith(path.lower())]
    return max(found, key=lambda d: _natural(d.name)) if found else None


def umu_env(proton_path, slug):
    """Variables de umu-run para un juego. Como Faugus (que con ellas enlaza bien Battle.net):
    un GAMEID propio por juego, `UMU_CONTAINER_NSENTER=1` (los `umu-run` del mismo juego comparten el
    contenedor y, con él, el wineserver y la comunicación entre el lanzador y el juego) y Wayland
    desactivado salvo en Proton-Wineland, que lo trae pensado, o si se pidió Wayland nativo a mano."""
    path, wayland = split_spec(proton_path)
    env = {"PROTONPATH": path, "GAMEID": f"umu-arctiva{zlib.crc32(slug.encode()):08x}",
           "UMU_CONTAINER_NSENTER": "1"}
    if wayland:
        env["PROTON_ENABLE_WAYLAND"] = "1"
    elif "wineland" not in path.lower():
        env["PROTON_ENABLE_WAYLAND"] = "0"
    return env


def by_name(name, runners):
    return next((r for r in runners if r.name == name), None)
