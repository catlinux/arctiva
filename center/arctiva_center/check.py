# SPDX-License-Identifier: GPL-3.0-or-later
"""arctiva-center --check: aviso periódico de actualizaciones (temporizador de usuario), sin ventana."""
import json
import os
import subprocess
import sys
from pathlib import Path

from .core import aur, i18n, updates

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


def _run(argv, timeout):
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None


def pending(run=_run, settings_path=aur.SETTINGS_FILE, aur_updates=None):
    """Lo mismo que actualiza el módulo Actualizaciones: pacman, Flatpak y el AUR según los ajustes.
    Una fuente que falla (sin red, sin flatpak) no impide avisar de las demás."""
    found = []
    out = run(["checkupdates"], 300)
    # checkupdates: 0 hay actualizaciones, 2 no hay, 1 error (sin red, por ejemplo).
    if out is not None and out.returncode == 0:
        found += updates.parse_checkupdates(out.stdout)
    if aur.get_setting("update_flatpak", True, settings_path):
        out = run(["flatpak", "remote-ls", "--updates", "--columns=application,name,version"], 120)
        if out is not None and out.returncode == 0:
            found += updates.parse_flatpak_updates(out.stdout)
    if aur.aur_enabled(settings_path) and aur.get_setting("update_aur", True, settings_path):
        found += (aur_updates or _aur_updates)()
    return found


def _aur_updates():
    try:
        import pyalpm
        state = aur.load_state()
        foreign = {n: v for n, v in aur.foreign_packages().items() if n in state}
        if not foreign:
            return []
        return [updates.Update(p.name, foreign[p.name], p.version)
                for p in aur.newer_versions(foreign, pyalpm.vercmp)]
    except Exception:  # sin red, RPC caído: se avisará la próxima vez
        return []


def main():
    if os.path.exists("/run/archiso"):
        return 0
    current = pending()
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
