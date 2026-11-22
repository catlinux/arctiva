# SPDX-License-Identifier: GPL-3.0-or-later
"""Dónde están el QML, las traducciones y los datos: en el árbol de desarrollo o ya instalados."""
import os
from collections import namedtuple
from pathlib import Path

Paths = namedtuple("Paths", "qml translations data")

INSTALLED = Path("/usr/share/arctiva-games")
LIVE_MARKER = "/run/archiso"


def resolve():
    override = os.environ.get("ARCTIVA_GAMES_DATA")
    if override:
        share = Path(override)
        return Paths(share / "qml", share / "translations", share)
    # Árbol de desarrollo: games/ contiene arctiva_games/, qml/, translations/ y data/.
    tree = Path(__file__).resolve().parents[2]
    if (tree / "qml" / "Main.qml").is_file():
        return Paths(tree / "qml", tree / "translations", tree / "data")
    return Paths(INSTALLED / "qml", INSTALLED / "translations", INSTALLED)


def is_live(marker=LIVE_MARKER):
    return os.path.exists(marker)
