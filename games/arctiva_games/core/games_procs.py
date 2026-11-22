# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: monitor de procesos de un prefijo de Wine (D-G6).

Recorre `/proc` y devuelve los procesos del usuario cuyo entorno tiene `WINEPREFIX` igual al del juego.
Sin efectos y sin Qt: el sondeo periódico (cada 1 s con la página visible) lo pone quien lo use, llamando a
`PrefixMonitor.poll()`, que informa de los procesos nuevos y de los desaparecidos."""
import os
from collections import namedtuple
from pathlib import Path

WineProc = namedtuple("WineProc", "pid name uptime")

_TICKS = os.sysconf("SC_CLK_TCK")


def _norm(path):
    return os.path.normpath(os.path.expanduser(str(path)))


def _read(path):
    return Path(path).read_bytes()


def _name(proc_dir):
    """Nombre del ejecutable: el último componente de `argv[0]` (también con rutas de Windows) o `comm`."""
    try:
        argv0 = _read(proc_dir / "cmdline").split(b"\0", 1)[0].decode(errors="replace")
    except OSError:
        argv0 = ""
    argv0 = argv0.replace("\\", "/").rstrip("/")
    if argv0:
        return argv0.rsplit("/", 1)[-1]
    return _read(proc_dir / "comm").decode(errors="replace").strip()


def _uptime(proc_dir, proc_root):
    """Segundos desde que arrancó el proceso (campo 22 de `stat`, tras el nombre entre paréntesis)."""
    stat = _read(proc_dir / "stat").decode(errors="replace")
    start = int(stat.rsplit(")", 1)[1].split()[19]) / _TICKS
    boot = float(_read(Path(proc_root) / "uptime").split()[0])
    return max(0.0, boot - start)


def list_processes(prefix, proc_root="/proc"):
    """Procesos propios con `WINEPREFIX == prefix`. Ignora en silencio los ilegibles o desaparecidos."""
    wanted = _norm(prefix)
    uid = os.getuid()
    found = []
    try:
        entries = list(Path(proc_root).iterdir())
    except OSError:
        return found
    for entry in entries:
        if not entry.name.isdigit():
            continue
        try:
            if entry.stat().st_uid != uid:
                continue
            env = _read(entry / "environ")
            value = None
            for item in env.split(b"\0"):
                if item.startswith(b"WINEPREFIX="):
                    value = item[len(b"WINEPREFIX="):].decode(errors="replace")
                    break
            if value is None or _norm(value) != wanted:
                continue
            found.append(WineProc(int(entry.name), _name(entry), _uptime(entry, proc_root)))
        except (OSError, ValueError, IndexError):
            continue
    return sorted(found, key=lambda p: p.pid)


class PrefixMonitor:
    """Compara sondeos sucesivos: `poll()` devuelve `(vivos, nuevos, terminados)`; los terminados son
    los `WineProc` del sondeo anterior que ya no existen (el código de salida de los que lanzó el
    motor lo registra el motor, que es su padre)."""

    def __init__(self, prefix, proc_root="/proc"):
        self.prefix = prefix
        self.proc_root = proc_root
        self._last = {}

    def poll(self):
        alive = list_processes(self.prefix, self.proc_root)
        now = {p.pid: p for p in alive}
        new = [p for pid, p in now.items() if pid not in self._last]
        gone = [p for pid, p in self._last.items() if pid not in now]
        self._last = now
        return alive, new, gone
