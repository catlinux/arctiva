# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: descarga de los archivos (`files`) de un plan antes de lanzar el motor (D-G2).

Solo http/https; los archivos que debe aportar el usuario (`N/A`) no se soportan todavía y se avisan
antes de empezar. Las órdenes `extract`, `move`, `merge` e `input_menu` tampoco están implementadas en
el motor: `unsupported_steps` las lista para avisar antes de instalar."""
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .. import __version__

DOWNLOADS = Path.home() / ".cache" / "arctiva-games" / "downloads"
TIMEOUT = 30
NOT_IMPLEMENTED = ("extract", "move", "merge", "input_menu")


class DownloadError(Exception):
    pass


def unsupported_steps(plan):
    """Descripciones de lo que el motor aún no puede hacer: pasos sin implementar y archivos del usuario."""
    out = [s.description for s in plan.steps if s.kind in NOT_IMPLEMENTED]
    out += [f"archivo que debe aportar el usuario: {f.prompt or f.id}" for f in plan.files if f.user_provided]
    return out


def _filename(spec):
    name = spec.filename or os.path.basename(urllib.parse.urlparse(spec.url).path) or spec.id
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).lstrip(".")
    return name or "archivo"


def default_open(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"Arctiva-Games/{__version__}"})
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def download_files(plan, dest, log=lambda text: None, opener=default_open):
    """Descarga los `files` del plan a `dest/<slug>/` y devuelve `{id: ruta}`. Bloqueante: va en un hilo."""
    folder = Path(dest) / (plan.slug or "juego")
    folder.mkdir(parents=True, exist_ok=True)
    result = {}
    for spec in plan.files:
        if spec.user_provided:
            raise DownloadError(f"hay que aportar el archivo «{spec.prompt or spec.id}»: aún no se soporta")
        target = folder / _filename(spec)
        part = target.with_name(target.name + ".part")
        log(f"Descargando {spec.url}")
        try:
            with opener(spec.url) as resp, open(part, "wb") as out:
                total = 0
                while True:
                    chunk = resp.read(1 << 16)
                    if not chunk:
                        break
                    out.write(chunk)
                    total += len(chunk)
            if total == 0:
                raise DownloadError(f"la descarga de «{spec.id}» llegó vacía")
            os.replace(part, target)
        except (OSError, ValueError) as e:
            raise DownloadError(f"no se pudo descargar «{spec.id}»: {e}") from e
        finally:
            try:
                part.unlink()
            except OSError:
                pass
        log(f"  guardado en {target} ({total} bytes)")
        result[spec.id] = str(target)
    return result
