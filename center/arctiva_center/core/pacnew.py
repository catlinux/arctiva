# SPDX-License-Identifier: GPL-3.0-or-later
"""Archivos .pacnew pendientes (pacdiff --output) y su diferencia con el original."""
import difflib
from pathlib import Path

MAX_DIFF_BYTES = 256 * 1024


def parse_pacdiff(text):
    """pacdiff --output lista una ruta por línea; solo interesan los .pacnew de /etc."""
    return [line.strip() for line in text.splitlines()
            if line.strip().startswith("/etc/") and line.strip().endswith(".pacnew")]


def unified_diff(pacnew_path):
    """Diferencia entre el original y el .pacnew, o None si no se puede mostrar
    (sin permiso de lectura, binario o demasiado grande)."""
    pacnew = Path(pacnew_path)
    original = pacnew.with_name(pacnew.name[: -len(".pacnew")])
    try:
        texts = []
        for p in (original, pacnew):
            if p.stat().st_size > MAX_DIFF_BYTES:
                return None
            texts.append(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        return None
    return "".join(difflib.unified_diff(
        texts[0].splitlines(keepends=True), texts[1].splitlines(keepends=True),
        fromfile=str(original), tofile=str(pacnew)))
