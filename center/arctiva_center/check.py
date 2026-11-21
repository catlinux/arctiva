# SPDX-License-Identifier: GPL-3.0-or-later
"""arctiva-center --check: aviso periódico de actualizaciones (temporizador de usuario), sin ventana."""
import json
import os
import subprocess
import sys
from pathlib import Path

from .core import i18n, updates

STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "arctiva-center"

# Sin Qt en este modo: los textos de la notificación van aquí.
TEXTS = {
    "en": ("Updates available", "{n} updates are ready to install.", "Open Arctiva Center"),
    "es": ("Actualizaciones disponibles", "Hay {n} actualizaciones listas para instalar.",
           "Abrir Arctiva Center"),
    "ca": ("Actualitzacions disponibles", "Hi ha {n} actualitzacions a punt per instal·lar.",
           "Obre Arctiva Center"),
}


def texts(env=os.environ):
    langs = [x for x in env.get("LANGUAGE", "").split(":") if x] + [env.get("LANG", "")]
    for name in i18n.catalog_candidates(l.split(".")[0] for l in langs if l):
        if name in TEXTS:
            return TEXTS[name]
    return TEXTS["en"]


def notify(title, body, action_label, timeout=3600):
    """Muestra la notificación y devuelve True si el usuario pulsa la acción.

    notify-send sigue conectado al bus mientras espera: Plasma solo muestra los botones de una
    aplicación que puede recibir la respuesta (con gdbus call, que se desconecta, no salen).
    """
    reply = subprocess.run(
        ["notify-send", "--app-name=Arctiva Center", "--icon=arctiva", "--wait",
         "--hint=string:desktop-entry:arctiva-center", f"--action=open={action_label}",
         title, body],
        capture_output=True, text=True, timeout=timeout)
    return reply.stdout.strip() == "open"


def new_since_last_notice(current, notified):
    """Actualizaciones que no estaban en el último aviso (nombre y versión nueva)."""
    return sorted({f"{u.name} {u.new}" for u in current} - set(notified))


def main():
    if os.path.exists("/run/archiso"):
        return 0
    try:
        out = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    # checkupdates: 0 hay actualizaciones, 2 no hay, 1 error (sin red, por ejemplo).
    if out.returncode != 0:
        return 0
    current = updates.parse_checkupdates(out.stdout)
    state = STATE / "notified.json"
    try:
        notified = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        notified = []
    fresh = new_since_last_notice(current, notified if isinstance(notified, list) else [])
    if not fresh:
        return 0
    STATE.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps(sorted(f"{u.name} {u.new}" for u in current)), encoding="utf-8")
    title, body, action = texts()
    try:
        opened = notify(title, body.format(n=len(current)), action)
    except (OSError, subprocess.SubprocessError):
        return 0
    if opened:
        subprocess.Popen([sys.argv[0], "--module", "updates"], start_new_session=True)
    return 0
