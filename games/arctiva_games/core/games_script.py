# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games (D-G2, D-G3): analiza un script de instalación compatible con los de Lutris.

Todo es puro: no descarga, no ejecuta y no toca el disco. Se analiza el script entero y, si contiene
algo fuera del subconjunto soportado, `plan` lanza `UnsupportedCommand` con el nombre exacto; nunca se
ignora una orden en silencio. En el plan, `$GAMEDIR` y `$WINEPREFIX` ya van sustituidos; el resto de
variables (`$CACHE`, `$<id de archivo>`…) las resuelve el motor. El prefijo de Wine es siempre
`<game_dir>/prefix` (D-G1), sea cual sea el `prefix` que diga el script."""
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

import yaml

PREFIX_DIRNAME = "prefix"

# Órdenes del bloque `installer`; cada una con los parámetros que aceptamos.
TASKS = {
    "create_prefix": {"prefix", "arch", "description"},
    "wineexec": {"executable", "args", "prefix", "arch", "working_dir", "description", "return_code",
                 "exclude_processes", "env", "wait", "wait_message"},
    "winetricks": {"app", "prefix", "arch", "silent", "description"},
    "winekill": {"prefix", "arch", "description"},
    "set_regedit": {"path", "key", "value", "type", "prefix", "arch", "description"},
    "delete_registry_key": {"key", "prefix", "arch", "description"},
}
COMMANDS = {
    "task": None,
    "write_file": {"file", "content", "mode"},
    "write_json": {"file", "data", "merge"},
    "chmodx": None,  # el valor es la ruta
    "execute": {"file", "command", "args", "env", "description"},
    "extract": {"file", "dst", "format", "description"},
    "move": {"src", "dst"},
    "merge": {"src", "dst", "optional"},
    "input_menu": {"description", "id", "options", "preselect"},
}
SECTIONS = {"files", "game", "system", "wine", "installer"}
GAME_KEYS = {"exe", "prefix", "arch", "args"}
SYSTEM_KEYS = {"env", "postexit_command"}
WINE_KEYS = {"overrides"}
FILE_KEYS = {"url", "filename"}
PREFIX_TASKS = ("create_prefix", "wineexec", "winetricks", "winekill", "set_regedit", "delete_registry_key")


class ScriptError(ValueError):
    """El texto no es un script válido (YAML roto, estructura inesperada, URL no http/https)."""


class UnsupportedCommand(Exception):
    """Orden, sección o parámetro fuera del subconjunto soportado. `name` es lo que se muestra."""

    def __init__(self, name):
        super().__init__(name)
        self.name = name


@dataclass(frozen=True)
class FileSpec:
    id: str
    url: str = ""          # vacío si lo aporta el usuario
    filename: str = ""
    prompt: str = ""       # mensaje cuando el usuario debe aportar el archivo («N/A:…»)

    @property
    def user_provided(self):
        return not self.url


@dataclass(frozen=True)
class Script:
    name: str
    slug: str
    runner: str
    author: str
    credits: str
    version: str
    files: tuple
    game: dict
    system: dict
    wine: dict
    installer: tuple  # órdenes crudas, una por elemento


@dataclass(frozen=True)
class Step:
    id: str
    kind: str                # nombre de la orden o de la tarea (`wineexec`, `write_file`…)
    description: str
    args: dict
    env: dict = field(default_factory=dict)
    wait_user: bool = False  # D-G5: lanzar sin esperar ni matar hasta que el usuario pulse Continuar
    wait_message: str = ""


@dataclass(frozen=True)
class Plan:
    name: str
    slug: str
    author: str
    credits: str
    game_dir: str
    prefix: str
    files: tuple
    game: dict
    env: dict
    overrides: dict
    postexit_command: object
    steps: tuple


def _text(v):
    return "" if v is None else str(v)


def _mapping(v, what):
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise ScriptError(f"{what} debe ser un mapa")
    return v


def _check_keys(keys, allowed, prefix):
    for k in keys:
        if k not in allowed:
            raise UnsupportedCommand(f"{prefix}.{k}")


def _parse_file(item):
    if not isinstance(item, dict) or len(item) != 1:
        raise ScriptError("cada entrada de `files` debe ser un mapa de un solo elemento")
    (fid, val), = item.items()
    fid = str(fid)
    if isinstance(val, dict):
        _check_keys(val, FILE_KEYS, "files")
        url, filename = _text(val.get("url")), _text(val.get("filename"))
    else:
        url, filename = _text(val), ""
    if url.upper().startswith("N/A"):
        return FileSpec(fid, "", filename, url[3:].lstrip(":").strip())
    if not re.match(r"https?://\S+$", url, re.I):
        raise ScriptError(f"la URL del archivo «{fid}» no es http/https")
    return FileSpec(fid, url, filename)


def parse(text):
    """Texto YAML o JSON de lutris.net (el JSON de la API con `script`, o solo el cuerpo) → `Script`."""
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise ScriptError(f"no es YAML ni JSON válido: {e}") from e
    if not isinstance(data, dict):
        raise ScriptError("el script debe ser un mapa")
    if "script" in data:
        meta, body = data, _mapping(data["script"], "`script`")
    else:
        meta, body = {}, data
    if "extends" in body or "extends" in meta:
        raise UnsupportedCommand("extends")
    for key in body:
        if key not in SECTIONS:
            raise UnsupportedCommand(key)
    runner = _text(meta.get("runner")) or "wine"
    files = body.get("files") or []
    installer = body.get("installer") or []
    if not isinstance(files, list) or not isinstance(installer, list):
        raise ScriptError("`files` e `installer` deben ser listas")
    if body.get("system") is not None:
        _check_keys(_mapping(body["system"], "`system`"), SYSTEM_KEYS, "system")
    if body.get("wine") is not None:
        _check_keys(_mapping(body["wine"], "`wine`"), WINE_KEYS, "wine")
    if body.get("game") is not None:
        _check_keys(_mapping(body["game"], "`game`"), GAME_KEYS, "game")
    return Script(
        name=_text(meta.get("name")), slug=_text(meta.get("slug") or meta.get("game_slug")), runner=runner,
        author=_text(meta.get("user")), credits=_text(meta.get("credits")), version=_text(meta.get("version")),
        files=tuple(_parse_file(f) for f in files), game=dict(_mapping(body.get("game"), "`game`")),
        system=dict(_mapping(body.get("system"), "`system`")),
        wine=dict(_mapping(body.get("wine"), "`wine`")), installer=tuple(installer))


def _subst(value, game_dir, prefix):
    if isinstance(value, str):
        value = re.sub(r"\$\{?GAMEDIR\}?(?![A-Za-z0-9_])", lambda m: game_dir, value)
        return re.sub(r"\$\{?WINEPREFIX\}?(?![A-Za-z0-9_])", lambda m: prefix, value)
    if isinstance(value, list):
        return [_subst(v, game_dir, prefix) for v in value]
    if isinstance(value, dict):
        return {k: _subst(v, game_dir, prefix) for k, v in value.items()}
    return value


def _describe(kind, a):
    base = lambda p: PurePosixPath(_text(p).replace("\\", "/")).name or _text(p)
    if kind == "create_prefix":
        return "Crear el prefijo de Wine"
    if kind == "wineexec":
        return f"Ejecutar {base(a.get('executable'))} con Wine"
    if kind == "winetricks":
        return f"Instalar con winetricks: {_text(a.get('app'))}"
    if kind == "winekill":
        return "Cerrar los procesos de Wine del prefijo"
    if kind == "set_regedit":
        return f"Cambiar el registro de Wine: {_text(a.get('path'))}"
    if kind == "delete_registry_key":
        return f"Borrar del registro de Wine: {_text(a.get('key'))}"
    if kind == "write_file":
        return f"Escribir el archivo {base(a.get('file'))}"
    if kind == "write_json":
        return f"Escribir el archivo JSON {base(a.get('file'))}"
    if kind == "chmodx":
        return f"Hacer ejecutable {base(a.get('path'))}"
    if kind == "execute":
        return f"Ejecutar {base(a.get('file') or a.get('command'))}"
    if kind == "extract":
        return f"Extraer {base(a.get('file'))}"
    if kind == "move":
        return f"Mover {base(a.get('src'))}"
    if kind == "merge":
        return f"Combinar {base(a.get('src'))}"
    return "Elegir una opción"


def _command(item):
    if not isinstance(item, dict) or len(item) != 1:
        raise ScriptError("cada orden de `installer` debe ser un mapa de un solo elemento")
    (name, val), = item.items()
    name = str(name)
    if name not in COMMANDS:
        raise UnsupportedCommand(name)
    if name == "task":
        a = dict(_mapping(val, "`task`"))
        task = _text(a.pop("name", ""))
        if task not in TASKS:
            raise UnsupportedCommand(f"task:{task or '?'}")
        _check_keys(a, TASKS[task], task)
        return task, a
    if name == "chmodx":
        return name, {"path": _text(val)}
    a = dict(_mapping(val, f"`{name}`"))
    _check_keys(a, COMMANDS[name], name)
    return name, a


def plan(script, game_dir):
    """`Script` → `Plan` con los pasos en orden. Lanza `UnsupportedCommand` si algo no se soporta."""
    if script.runner != "wine":
        raise UnsupportedCommand(f"runner:{script.runner}")
    game_dir = str(game_dir)
    prefix = f"{game_dir}/{PREFIX_DIRNAME}"
    cmds = [_command(item) for item in script.installer]
    steps = []
    for i, (kind, args) in enumerate(cmds):
        args = _subst(args, game_dir, prefix)
        if kind in PREFIX_TASKS:
            args["prefix"] = prefix
        nxt = cmds[i + 1][0] if i + 1 < len(cmds) else None
        explicit = kind == "wineexec" and _text(args.get("wait")).lower() == "user"
        # D-G5: un lanzador (wineexec) seguido de winekill se deja abierto hasta que el usuario continúe.
        wait = explicit or (kind == "wineexec" and nxt == "winekill")
        env = args.get("env") if isinstance(args.get("env"), dict) else {}
        steps.append(Step(
            id=f"step-{i + 1}", kind=kind, description=_text(args.get("description")) or _describe(kind, args),
            args=args, env={str(k): _text(v) for k, v in env.items()}, wait_user=wait,
            wait_message=(_text(args.get("wait_message")) or
                          "Cuando hayas terminado en el lanzador, pulsa Continuar.") if wait else ""))
    return Plan(
        name=script.name, slug=script.slug, author=script.author, credits=script.credits,
        game_dir=game_dir, prefix=prefix, files=script.files, game=_subst(script.game, game_dir, prefix),
        env={str(k): _text(v) for k, v in _subst(_mapping(script.system.get("env"), "`system.env`"),
                                                 game_dir, prefix).items()},
        overrides={str(k): _text(v) for k, v in _mapping(script.wine.get("overrides"), "`wine.overrides`").items()},
        postexit_command=_subst(script.system.get("postexit_command"), game_dir, prefix), steps=tuple(steps))


def summary(p):
    """Resumen de seguridad que se muestra antes de instalar (D-G3)."""
    urls = [f.url for f in p.files if f.url]
    execs, regs, tricks = [], [], []
    for s in p.steps:
        a = s.args
        if s.kind == "wineexec":
            execs.append(_text(a.get("executable")))
        elif s.kind == "execute":
            execs.append(_text(a.get("file") or a.get("command")))
        elif s.kind == "set_regedit":
            regs.append(_text(a.get("path")))
        elif s.kind == "delete_registry_key":
            regs.append(_text(a.get("key")))
        elif s.kind == "winetricks":
            tricks += _text(a.get("app")).split()
    if p.postexit_command:
        execs.append(_text(p.postexit_command))
    return {"name": p.name, "author": p.author, "credits": p.credits, "urls": urls,
            "user_files": [f.prompt or f.id for f in p.files if f.user_provided],
            "executables": execs, "registry_keys": regs, "winetricks": tricks}
