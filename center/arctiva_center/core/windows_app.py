# SPDX-License-Identifier: GPL-3.0-or-later
"""Abrir programas de Windows (D-12, decisión 8 de la fase 6): comprobación del archivo y órdenes."""
import os
import re
from pathlib import Path

BOTTLES = "com.usebottles.bottles"
EXTENSIONS = (".exe", ".msi", ".lnk", ".bat")

LINKS = (
    ("WineHQ AppDB", "https://appdb.winehq.org/"),
    ("ProtonDB", "https://www.protondb.com/"),
    ("Are We Anti-Cheat Yet?", "https://areweanticheatyet.com/"),
)


def check_file(path):
    """Ruta absoluta normalizada de un archivo de Windows existente, o None.

    Solo se acepta un archivo normal con una extensión conocida: lo que llega por la línea de
    órdenes (doble clic o terminal) no se confía."""
    if not path or "\0" in path or "\n" in path:
        return None
    p = Path(path)
    if p.suffix.lower() not in EXTENSIONS:
        return None
    try:
        real = os.path.realpath(p)
    except OSError:
        return None
    return real if os.path.isfile(real) else None


def bottles_argv(path):
    """Orden para abrir el archivo con Bottles (Flatpak): `-e` pide ejecutarlo en una botella."""
    real = check_file(path)
    if real is None:
        raise ValueError(f"archivo no válido: {path!r}")
    flag = "--lnk" if real.lower().endswith(".lnk") else "-e"
    return ["flatpak", "run", BOTTLES, flag, real]


def bottles_installed(flatpak_ids):
    return BOTTLES in flatpak_ids


def display_name(path):
    return re.sub(r"[\x00-\x1f]", "", os.path.basename(path or ""))
