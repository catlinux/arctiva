# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: accesos directos de un juego en el menú de aplicaciones (categoría Juegos) y en el escritorio.

El acceso directo ejecuta `arctiva-games --play <slug>`, que lanza el juego con su ejecutor sin abrir la ventana."""
import os
import re
from pathlib import Path

MENU_DIR = Path.home() / ".local" / "share" / "applications"
PREFIX = "arctiva-games-"


def desktop_dir(home=None):
    """Carpeta del escritorio según `user-dirs.dirs`, o `~/Desktop`."""
    home = Path(home) if home else Path.home()
    try:
        text = (home / ".config" / "user-dirs.dirs").read_text(encoding="utf-8")
        m = re.search(r'^XDG_DESKTOP_DIR="([^"]+)"', text, re.M)
        if m:
            return Path(m.group(1).replace("$HOME", str(home)))
    except OSError:
        pass
    return home / "Desktop"


def _quote(text):
    return '"' + re.sub(r'(["`$\\])', r"\\\1", text) + '"'


def entry(name, slug):
    safe = name.replace("\n", " ").replace("\r", " ")
    return (f"[Desktop Entry]\nType=Application\nName={safe}\nComment={safe} (Arctiva Games)\n"
            f"Exec=arctiva-games --play {_quote(slug)}\nIcon=applications-games\nTerminal=false\n"
            f"Categories=Game;\nStartupNotify=true\n")


def _paths(slug, menu_dir, desk_dir):
    return {"menu": Path(menu_dir) / f"{PREFIX}{slug}.desktop", "desktop": Path(desk_dir) / f"{PREFIX}{slug}.desktop"}


def create(game, menu=True, desktop=False, menu_dir=MENU_DIR, desk_dir=None):
    desk_dir = desk_dir or desktop_dir()
    for kind, wanted in (("menu", menu), ("desktop", desktop)):
        if not wanted:
            continue
        p = _paths(game.slug, menu_dir, desk_dir)[kind]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(entry(game.name, game.slug), encoding="utf-8")
        p.chmod(0o755)


def status(slug, menu_dir=MENU_DIR, desk_dir=None):
    paths = _paths(slug, menu_dir, desk_dir or desktop_dir())
    return {k: p.is_file() for k, p in paths.items()}


def remove(slug, menu_dir=MENU_DIR, desk_dir=None):
    for p in _paths(slug, menu_dir, desk_dir or desktop_dir()).values():
        try:
            p.unlink()
        except OSError:
            pass
