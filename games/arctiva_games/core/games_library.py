# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: juegos instalados (`<base>/<slug>.toml`), orden de lanzarlos y desinstalación.

Todo vive en el home del usuario (D-G1): juegos en `~/Games/<slug>/`, estado en
`~/.local/share/arctiva-games/`. Desinstalar solo borra una carpeta que cuelgue de la raíz de juegos."""
import json
import os
import re
import shutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from . import games_runners

ROOT = Path.home() / "Games"
BASE = Path.home() / ".local" / "share" / "arctiva-games"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")


class LibraryError(Exception):
    pass


@dataclass
class Game:
    slug: str
    name: str
    exe: str
    game_dir: str
    prefix: str
    env: dict = field(default_factory=dict)
    runner: str = "wine"   # «wine» o la carpeta de Proton con la que se instaló


def valid_slug(slug):
    return isinstance(slug, str) and SLUG_RE.fullmatch(slug) is not None and ".." not in slug


def game_dir(slug, root=ROOT):
    if not valid_slug(slug):
        raise LibraryError(f"nombre de juego no válido: {slug!r}")
    return Path(root) / slug


def _q(value):
    return json.dumps(str(value), ensure_ascii=False)


def save(game, base=BASE):
    if not valid_slug(game.slug):
        raise LibraryError(f"nombre de juego no válido: {game.slug!r}")
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    lines = [f"slug = {_q(game.slug)}", f"name = {_q(game.name)}", f"exe = {_q(game.exe)}",
             f"game_dir = {_q(game.game_dir)}", f"prefix = {_q(game.prefix)}", f"runner = {_q(game.runner)}",
             "", "[env]"] + [f"{_q(k)} = {_q(v)}" for k, v in game.env.items()]
    tmp = base / f"{game.slug}.tmp"
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, base / f"{game.slug}.toml")


def _load(path):
    try:
        d = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        env = d.get("env") or {}
        return Game(d["slug"], d["name"], d["exe"], d["game_dir"], d["prefix"],
                    {str(k): str(v) for k, v in env.items()}, d.get("runner", "wine"))
    except (OSError, ValueError, KeyError, TypeError):
        return None


def list_games(base=BASE):
    games = [g for g in (_load(p) for p in sorted(Path(base).glob("*.toml"))) if g and valid_slug(g.slug)]
    return sorted(games, key=lambda g: g.name.lower())


def get(slug, base=BASE):
    return _load(Path(base) / f"{slug}.toml") if valid_slug(slug) else None


def launch_argv(game, umu=None):
    """`(programa, argumentos, entorno)` para jugar con el ejecutor del juego (Proton con `umu`, o `wine`)."""
    env = {"WINEPREFIX": game.prefix, **game.env}
    if game.runner != "wine":
        if not umu:
            raise LibraryError("falta umu-run (paquete umu-launcher) para jugar con Proton")
        return umu, [game.exe], {**env, **games_runners.umu_env(game.runner, game.slug)}
    return "wine", [game.exe], env


def remove(slug, base=BASE, root=ROOT):
    """Borra la carpeta del juego y su ficha. Solo si la carpeta registrada cuelga de `root`."""
    game = get(slug, base)
    if game is None:
        raise LibraryError("el juego no está instalado")
    real_root = Path(os.path.realpath(root))
    real = Path(os.path.realpath(game.game_dir))
    if real == real_root or real_root not in real.parents or real.name != slug:
        raise LibraryError(f"la carpeta {game.game_dir} no está en {root}: no se borra")
    shutil.rmtree(real, ignore_errors=True)
    for name in (f"{slug}.toml", f"{slug}.state.json"):
        try:
            (Path(base) / name).unlink()
        except OSError:
            pass
