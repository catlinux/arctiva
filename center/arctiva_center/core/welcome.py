# SPDX-License-Identifier: GPL-3.0-or-later
"""Bienvenida del primer inicio de sesión (decisión 9 de la fase 4)."""
import os
from pathlib import Path

LIVE_MARKER = "/run/archiso"


def done_file(env=os.environ):
    config = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "arctiva-center" / "welcome.done"


def is_live(marker=LIVE_MARKER):
    return os.path.exists(marker)


def should_show(env=os.environ, marker=LIVE_MARKER):
    """El arranque automático (--welcome) sale sin ventana en la live o si ya se desmarcó."""
    return not is_live(marker) and not done_file(env).exists()


def set_show_at_login(show, env=os.environ):
    path = done_file(env)
    if show:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
