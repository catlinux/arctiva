# SPDX-License-Identifier: GPL-3.0-or-later
"""Instantáneas de Snapper: cuántas hay y cuánto espacio libre queda en el disco."""
import shutil
from pathlib import Path

SNAPSHOTS_DIR = "/.snapshots"


def count(directory=SNAPSHOTS_DIR):
    """Número de instantáneas (carpetas numéricas); -1 si no hay Snapper o no se puede leer."""
    try:
        return sum(1 for p in Path(directory).iterdir() if p.name.isdigit() and p.is_dir())
    except OSError:
        return -1


def free_bytes(path="/"):
    try:
        return shutil.disk_usage(path).free
    except OSError:
        return -1
