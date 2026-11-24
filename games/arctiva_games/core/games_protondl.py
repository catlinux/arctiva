# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: Proton de serie (D-G8). Se descarga solo, como si viniera con el paquete, desde las
publicaciones oficiales de su proyecto en GitHub, y se comprueba con su suma SHA-512 antes de usarlo.

De serie va Proton-Wineland (driver nativo de Wayland; es con el que Battle.net funciona en Plasma Wayland).
GE-Proton se puede instalar igual. Arctiva no aloja ni redistribuye ninguno: cada equipo lo baja de su origen.
Queda en la carpeta de herramientas de Steam del usuario (donde lo buscan también Steam, Lutris y umu-run),
marcado como instalado por Arctiva Games para poder retirar después las versiones viejas que ningún juego use.
Como hay proyectos que publican cada pocos días, se busca versión nueva como mucho una vez por semana."""
import hashlib
import json
import re
import shutil
import tarfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DEST = Path.home() / ".local" / "share" / "Steam" / "compatibilitytools.d"
STATE = Path.home() / ".local" / "state" / "arctiva-games" / "proton.json"
MARK = ".arctiva-games"          # archivo dentro de cada versión que instaló Arctiva Games
CHECK_EVERY = 7 * 24 * 3600      # segundos entre comprobaciones de versión nueva
TIMEOUT = 30
CHUNK = 1 << 20


class ProtonError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    key: str
    name: str           # para mostrar
    api: str            # última publicación en la API de GitHub
    tag_re: str
    prefix: str         # comienzo del nombre de las carpetas instaladas
    bases: tuple        # nombres posibles del archivo, a partir de la etiqueta («{tag}», «{ver}»)
    ext: str


WINELAND = Source("wineland", "Proton-Wineland",
                  "https://api.github.com/repos/nanomatters/proton-salkim/releases/latest",
                  r"wineland-(?P<ver>[\d.]+-\d{8})", "proton-wineland",
                  ("proton-wineland-{ver}-x86_64",), ".tar.xz")
# Desde GE-Proton11 cada arquitectura va aparte («-x86_64»); las anteriores no llevan sufijo.
GE = Source("ge", "GE-Proton", "https://api.github.com/repos/GloriousEggroll/proton-ge-custom/releases/latest",
            r"GE-Proton(?P<ver>\d+-\d+)", "GE-Proton", ("{tag}-x86_64", "{tag}"), ".tar.gz")
DEFAULT = WINELAND


@dataclass(frozen=True)
class Release:
    tag: str
    tar_url: str
    sha_url: str
    size: int = 0
    folder: str = ""        # carpeta que trae el archivo (y nombre con el que queda instalada)

    @property
    def dir_name(self):
        return self.folder or self.tag


def _open(url):
    req = urllib.request.Request(url, headers={"User-Agent": "arctiva-games", "Accept": "application/json"})
    return urllib.request.urlopen(req, timeout=TIMEOUT)


def latest(source=DEFAULT, opener=_open):
    """La última versión publicada: su etiqueta, el archivo para x86_64 y su .sha512sum."""
    try:
        with opener(source.api) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (OSError, ValueError) as e:
        raise ProtonError(f"no se pudo consultar la última versión de {source.name}: {e}") from e
    tag = str(data.get("tag_name") or "")
    m = re.fullmatch(source.tag_re, tag)
    if not m:
        raise ProtonError(f"versión de {source.name} inesperada: {tag!r}")
    assets = {a.get("name"): a for a in data.get("assets") or [] if isinstance(a, dict)}
    for pattern in source.bases:
        base = pattern.format(tag=tag, ver=m.group("ver"))
        tar, sha = assets.get(base + source.ext), assets.get(base + ".sha512sum")
        if tar and sha:
            return Release(tag, tar["browser_download_url"], sha["browser_download_url"],
                           int(tar.get("size") or 0), base)
    raise ProtonError(f"la publicación {tag} de {source.name} no trae el archivo para x86_64 y su suma")


def is_installed(name, dest=DEST):
    return (Path(dest) / name / "proton").is_file()


def _natural(name):
    return [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", name)]


def _safe_filter(member, path):
    """El filtro «data» de tarfile, salvo que deja los enlaces simbólicos absolutos (Proton-Wineland enlaza a la
    configuración de Mesa del sistema). No abre ningún hueco: cada miembro posterior se sigue comprobando con su
    ruta real, así que nada se puede escribir a través de esos enlaces fuera de la carpeta."""
    try:
        return tarfile.data_filter(member, path)
    except tarfile.AbsoluteLinkError:
        if member.issym():
            return member
        raise


def install(release, dest=DEST, progress=None, opener=_open):
    """Descarga, comprueba y deja instalada una versión. Nada queda a medias: se trabaja en una carpeta
    temporal dentro de `dest` y solo al final se renombra."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    final = dest / release.dir_name
    if is_installed(release.dir_name, dest):
        return final
    # Hace falta sitio para el archivo y lo descomprimido (que ocupa unas cuatro veces más).
    if release.size and shutil.disk_usage(dest).free < release.size * 6:
        raise ProtonError("no hay espacio suficiente en el disco para Proton")
    work = dest / f".{release.dir_name}.descarga"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    try:
        archive = work / "archivo"
        digest = hashlib.sha512()
        try:
            with opener(release.tar_url) as resp, open(archive, "wb") as out:
                total = int(resp.headers.get("Content-Length") or release.size or 0)
                done = 0
                while chunk := resp.read(CHUNK):
                    out.write(chunk)
                    digest.update(chunk)
                    done += len(chunk)
                    if progress:
                        progress(done, total)
            with opener(release.sha_url) as resp:
                expected = resp.read().decode("utf-8", "replace").split()
        except OSError as e:
            raise ProtonError(f"no se pudo descargar Proton: {e}") from e
        if not expected or expected[0].lower() != digest.hexdigest():
            raise ProtonError("la suma SHA-512 no coincide: descarga descartada")
        unpacked = work / "contenido"
        try:
            with tarfile.open(archive, "r:*") as tar:
                # Ni rutas absolutas, ni «..», ni escribir fuera de la carpeta (ver _safe_filter).
                tar.extractall(unpacked, filter=_safe_filter)
        except (tarfile.TarError, OSError) as e:
            raise ProtonError(f"Proton no se pudo descomprimir: {e}") from e
        top = unpacked / release.dir_name
        if [p.name for p in unpacked.iterdir()] != [release.dir_name] or not (top / "proton").is_file():
            raise ProtonError("el archivo de Proton no tiene la estructura esperada")
        (top / MARK).write_text(release.tag + "\n", encoding="utf-8")
        top.rename(final)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return final


def _mine(dest, source):
    try:
        return sorted((d for d in Path(dest).iterdir()
                       if d.is_dir() and (d / MARK).is_file() and d.name.lower().startswith(source.prefix.lower())),
                      key=lambda d: _natural(d.name))
    except OSError:
        return []


def cleanup(dest=DEST, keep=(), source=DEFAULT):
    """Borra las versiones de `source` instaladas por Arctiva Games salvo la más nueva y las que use algún
    juego. Las que instaló el usuario (sin la marca) no se tocan nunca."""
    keep = {str(Path(k).resolve()) for k in keep if k}
    removed = []
    for d in _mine(dest, source)[:-1]:
        if str(d.resolve()) not in keep:
            shutil.rmtree(d, ignore_errors=True)
            removed.append(d.name)
    return removed


def _load_state(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_state(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


def ensure(dest=DEST, progress=None, keep=(), opener=_open, source=DEFAULT, state=STATE, now=None, force=False):
    """Deja instalada la última versión de `source`. Devuelve (nombre de la carpeta, ¿se ha descargado ahora?).
    Si ya hay una instalada y se comprobó hace menos de una semana, no consulta la red."""
    now = time.time() if now is None else now
    mine = _mine(dest, source)
    checked = _load_state(state).get(source.key, 0)
    if mine and not force and now - checked < CHECK_EVERY:
        return mine[-1].name, False
    release = latest(source, opener)
    fresh = not is_installed(release.dir_name, dest)
    if fresh:
        install(release, dest, progress, opener)
    data = _load_state(state)
    data[source.key] = now
    _save_state(state, data)
    cleanup(dest, keep, source)
    return release.dir_name, fresh
