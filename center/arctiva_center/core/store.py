# SPDX-License-Identifier: GPL-3.0-or-later
"""Lógica de la tienda sin Qt (fase 6): Flatpak por línea de órdenes, filas de fuentes de una
aplicación y comprobación de actualizaciones pendientes."""
import re
import time
from pathlib import Path

FLATPAK = "flatpak"
FLATPAK_ID_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,200}")
# Pasa de Flathub a refrescar su catálogo si es más viejo que esto.
APPSTREAM_MAX_AGE_DAYS = 7


def flatpak_install_argv(ref):
    _check_ref(ref)
    return [FLATPAK, "install", "--system", "--noninteractive", "flathub", ref]


def flatpak_uninstall_argv(ref):
    _check_ref(ref)
    return [FLATPAK, "uninstall", "--system", "--noninteractive", ref]


def flatpak_list_argv():
    return [FLATPAK, "list", "--system", "--app", "--columns=application"]


def flatpak_refresh_argv():
    return [FLATPAK, "update", "--appstream", "--system", "--noninteractive"]


def _check_ref(ref):
    if not FLATPAK_ID_RE.fullmatch(ref or ""):
        raise ValueError(f"id de Flatpak no válido: {ref!r}")


def parse_flatpak_list(text):
    return {line.strip() for line in text.splitlines() if FLATPAK_ID_RE.fullmatch(line.strip())}


def appstream_stale(path, now=None, max_age_days=APPSTREAM_MAX_AGE_DAYS):
    """True si falta el catálogo de Flathub o es más viejo que `max_age_days`."""
    try:
        age = (now if now is not None else time.time()) - Path(path).stat().st_mtime
    except OSError:
        return True
    return age > max_age_days * 86400


def human_size(size):
    if not size or size < 0:
        return ""
    value = float(size)
    for unit in ("B", "KiB", "MiB", "GiB"):
        if value < 1024 or unit == "GiB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024


def icon_source(icon):
    """Ruta absoluta → URL de archivo; nombre de tema → tal cual; vacío → icono genérico."""
    if not icon:
        return "package-x-generic"
    return "file://" + icon if icon.startswith("/") else icon


def source_rows(app, pacman_installed, flatpak_installed, alpm_info=None):
    """Una fila por fuente de la aplicación, con lo que la ventana muestra y decide."""
    rows = []
    for source in app.sources:
        row = {"kind": source.kind, "label": source.label, "ref": source.ref,
               "recommended": source.kind == app.recommended, "version": "", "size": "", "installed": False}
        if source.kind == "arch":
            row["installed"] = source.ref in pacman_installed
            info = (alpm_info or {}).get(source.ref)
            if info:
                row["version"] = info.version
                row["size"] = human_size(info.download_size)
        elif source.kind == "flathub":
            row["installed"] = source.ref in flatpak_installed
        rows.append(row)
    return rows


def app_summary(app, pacman_installed, flatpak_installed):
    """Datos de una tarjeta de la cuadrícula."""
    rows = source_rows(app, pacman_installed, flatpak_installed)
    return {"id": app.id, "name": app.name, "summary": app.summary, "icon": icon_source(app.icon),
            "sources": [r["label"] for r in rows], "installed": any(r["installed"] for r in rows)}


def app_detail(app, pacman_installed, flatpak_installed, alpm_info=None):
    data = app_summary(app, pacman_installed, flatpak_installed)
    data.update({"description": app.description, "license": app.license, "homepage": app.homepage,
                 "screenshots": list(app.screenshots), "categories": list(app.categories),
                 "rows": source_rows(app, pacman_installed, flatpak_installed, alpm_info)})
    return data


def checkupdates_pending(returncode):
    """Código de salida de `checkupdates`: 0 hay actualizaciones, 2 no hay, otro, error."""
    if returncode == 0:
        return True
    if returncode == 2:
        return False
    return None
