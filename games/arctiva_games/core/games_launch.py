# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: lanzar un juego instalado sin ventana (`arctiva-games --play <slug>`), para los accesos directos."""
import os
import subprocess
import sys
import time
from pathlib import Path

from . import games_library, games_runners


def run(slug, base=games_library.BASE):
    game = games_library.get(slug, base)
    if game is None:
        return _fail(f"El juego «{slug}» no está instalado.")
    try:
        program, args, env = games_library.launch_argv(game, games_runners.find_umu())
    except games_library.LibraryError as e:
        return _fail(str(e))
    env.setdefault("WINEDEBUG", "-all")
    logs = Path(base) / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{slug}-play-{time.strftime('%Y%m%d-%H%M%S')}.log"
    try:
        with open(log, "w", encoding="utf-8") as out:
            return subprocess.call([program, *args], cwd=game.game_dir, env={**os.environ, **env},
                                   stdout=out, stderr=subprocess.STDOUT)
    except OSError as e:
        return _fail(f"No se pudo lanzar {program}: {e}")


def _fail(message):
    print(message, file=sys.stderr)
    try:
        subprocess.run(["notify-send", "-a", "Arctiva Games", "Arctiva Games", message], timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass
    return 1
