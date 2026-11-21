# SPDX-License-Identifier: GPL-3.0-or-later
"""Órdenes para el ayudante privilegiado: siempre una lista de argumentos, nunca texto de shell.

El ayudante vuelve a validarlo todo; esto solo evita lanzar pkexec (y pedir la contraseña) para
una petición que va a rechazar.
"""
import re

HELPER = "/usr/lib/arctiva-center/arctiva-helper"
PKEXEC = "/usr/bin/pkexec"

ID_RE = re.compile(r"[a-z0-9-]{1,40}")

# Códigos de salida que no son de pacman.
EX_USAGE = 64
EX_UNAVAILABLE = 69
EX_TEMPFAIL = 75
PKEXEC_DISMISSED = 126
PKEXEC_NOT_AUTHORIZED = 127

_ARGS = {
    "update": lambda a: a in ([], ["--keyring-first"]),
    "extra-install": lambda a: len(a) == 1 and ID_RE.fullmatch(a[0]) is not None,
    "extra-remove": lambda a: len(a) == 1 and ID_RE.fullmatch(a[0]) is not None,
    "drivers-apply": lambda a: a == [],
    "pacnew-keep": lambda a: len(a) == 1 and a[0].startswith("/etc/") and a[0].endswith(".pacnew"),
    "pacnew-use": lambda a: len(a) == 1 and a[0].startswith("/etc/") and a[0].endswith(".pacnew"),
}


def build_argv(operation, args=()):
    args = list(args)
    check = _ARGS.get(operation)
    if check is None or not all(isinstance(a, str) for a in args) or not check(args):
        raise ValueError(f"operación no válida: {operation} {args}")
    return [PKEXEC, HELPER, operation, *args]


class LineSplitter:
    """Parte la salida en líneas. pacman redibuja las barras de progreso con «\\r»: cada
    redibujado cuenta como línea, igual que en un terminal se ve solo la última."""

    def __init__(self):
        self._buf = ""

    def feed(self, text):
        self._buf += text.replace("\r\n", "\n").replace("\r", "\n")
        *lines, self._buf = self._buf.split("\n")
        return lines

    def flush(self):
        rest, self._buf = self._buf, ""
        return [rest] if rest else []
