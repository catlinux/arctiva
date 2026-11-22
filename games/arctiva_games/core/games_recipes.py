# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: recetas propias (D-G9) de `data/games.toml`."""
import tomllib
from pathlib import Path


def load(data_dir):
    """Lista de recetas `{slug, name, description, script}`; vacía si el archivo falta o está roto."""
    try:
        data = tomllib.loads((Path(data_dir) / "games.toml").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for r in data.get("recipe", []):
        if isinstance(r, dict) and all(isinstance(r.get(k), str) and r[k] for k in ("slug", "name", "script")):
            out.append({"slug": r["slug"], "name": r["name"], "description": r.get("description", ""),
                        "script": r["script"],
                        "runners": [x for x in r.get("runners", []) if isinstance(x, str)]})
    return out
