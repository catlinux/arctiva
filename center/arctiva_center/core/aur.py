# SPDX-License-Identifier: GPL-3.0-or-later
"""AUR (decisión 7 de la fase 6): RPC, avisos, revisión del PKGBUILD, cadena de dependencias y diff.

Nada se ejecuta como root aquí: el clonado y `makepkg` corren como el usuario y solo lo ya
compilado pasa por el ayudante (`aur-install`). Las funciones que tocan la red o ejecutan órdenes
reciben `fetch` o `runner` para poder probarse sin ellas."""
import json
from concurrent.futures import ThreadPoolExecutor
import re
import subprocess
import time
import tomllib
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from . import fuzzy

RPC = "https://aur.archlinux.org/rpc/v5"
GIT_URL = "https://aur.archlinux.org/{}.git"
NAME_RE = re.compile(r"[a-z0-9@_+][a-z0-9@._+-]{0,99}")
DEP_RE = re.compile(r"^([a-z0-9@_+][a-z0-9@._+-]*)")
TIMEOUT = 10
MIN_AGE_DAYS = 30
MIN_VOTES = 10
MAX_CHAIN = 25          # tope de paquetes del AUR en una cadena de dependencias

CACHE = Path.home() / ".cache" / "arctiva-center" / "aur"
SRC_DIR = CACHE / "src"
BUILD_DIR = CACHE / "build"
STATE_FILE = Path.home() / ".local" / "state" / "arctiva-center" / "aur.json"
SETTINGS_FILE = Path.home() / ".config" / "arctiva-center" / "settings.toml"


class AurError(Exception):
    pass


@dataclass
class AurPackage:
    name: str
    base: str
    version: str
    description: str = ""
    votes: int = 0
    popularity: float = 0.0
    maintainer: str = ""
    first_submitted: int = 0
    last_modified: int = 0
    out_of_date: int = 0
    depends: tuple = ()
    makedepends: tuple = ()
    checkdepends: tuple = ()
    url: str = ""
    license: tuple = ()


def valid_name(name):
    return isinstance(name, str) and NAME_RE.fullmatch(name) is not None


def default_fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "arctiva-center"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")


def _package(r):
    return AurPackage(
        name=r["Name"], base=r.get("PackageBase") or r["Name"], version=r.get("Version", ""),
        description=r.get("Description") or "", votes=int(r.get("NumVotes") or 0),
        popularity=float(r.get("Popularity") or 0), maintainer=r.get("Maintainer") or "",
        first_submitted=int(r.get("FirstSubmitted") or 0), last_modified=int(r.get("LastModified") or 0),
        out_of_date=int(r.get("OutOfDate") or 0), depends=tuple(r.get("Depends") or ()),
        makedepends=tuple(r.get("MakeDepends") or ()), checkdepends=tuple(r.get("CheckDepends") or ()),
        url=r.get("URL") or "", license=tuple(r.get("License") or ()))


def _decode(text):
    try:
        data = json.loads(text)
    except ValueError as e:
        raise AurError("respuesta del AUR no válida") from e
    if data.get("type") == "error":
        raise AurError(data.get("error") or "error del AUR")
    return [_package(r) for r in data.get("results", []) if isinstance(r, dict) and "Name" in r]


def search(query, fetch=default_fetch):
    query = (query or "").strip()
    if len(query) < 2:
        return []
    url = f"{RPC}/search/{urllib.parse.quote(query, safe='')}?by=name-desc"
    return _decode(fetch(url))


SORTS = ("relevance", "votes", "popularity", "name")


def sort_packages(packages, key="votes"):
    """Ordena los resultados: por votos (los más usados primero), por popularidad o por nombre."""
    if key == "relevance":
        return list(packages)            # ya vienen por relevancia (search_smart)
    if key == "name":
        return sorted(packages, key=lambda p: p.name)
    if key == "popularity":
        return sorted(packages, key=lambda p: (-p.popularity, -p.votes, p.name))
    return sorted(packages, key=lambda p: (-p.votes, -p.popularity, p.name))


def _relevance(query, pkg):
    """(nivel, distancia) o None si el paquete no tiene que ver con la consulta. El nivel 0 es el nombre
    exacto; después, nombre que empieza por la consulta, que la contiene, descripción y, al final,
    parecidos con erratas."""
    words = fuzzy.tokens(query)
    whole = fuzzy.squash(query)
    name = fuzzy.squash(pkg.name)
    text = fuzzy.squash(pkg.name + " " + pkg.description)
    if name == whole:
        return 0, 0
    if name.startswith(whole):
        return 1, 0
    if whole in name or all(w in name for w in words):
        return 2, 0
    if whole in text or all(w in text for w in words):
        return 3, 0
    total = fuzzy.fuzzy_total(words, set(fuzzy.tokens(pkg.name)) | set(fuzzy.tokens(pkg.description)))
    return (4, total) if total is not None else None


def _variants(word):
    """Otras palabras por las que preguntar al AUR cuando la escrita no aparece: el AUR solo entiende
    subcadenas exactas, así que se prueban la primera y la segunda mitad (una sustitución estropea una
    sola), cada pareja de letras intercambiada y cada letra quitada (una letra de más)."""
    half = max(3, (len(word) + 1) // 2)
    candidates = [word[:half], word[-half:]]
    candidates += [word[:i] + word[i + 1] + word[i] + word[i + 2:] for i in range(len(word) - 1)]
    candidates += [word[:i] + word[i + 1:] for i in range(len(word))]
    found = []
    for v in candidates:
        if len(v) >= 3 and v != word and v not in found:
            found.append(v)
    return found[:24]


def search_smart(query, fetch=default_fetch, min_results=5):
    """Búsqueda tolerante en el AUR: el AUR solo entiende subcadenas exactas, así que se le pregunta por
    la palabra más larga y el resto (varias palabras, guiones, erratas) se resuelve aquí. Devuelve los
    paquetes por relevancia y, a igualdad, por votos."""
    words = fuzzy.tokens(query)
    if not words or max(len(w) for w in words) < 2:
        return []
    primary = max(words, key=len)
    pool = {p.name: p for p in search(primary, fetch)}
    ranked = {n: r for n, p in pool.items() if (r := _relevance(query, p)) is not None}
    if len(ranked) < min_results and len(primary) >= 4:
        def ask(variant):
            try:
                return search(variant, fetch)
            except (AurError, OSError):
                return []          # una variante que falla no estropea la búsqueda
        with ThreadPoolExecutor(max_workers=8) as pool_of_threads:
            for found in pool_of_threads.map(ask, _variants(primary)):
                for p in found:
                    pool.setdefault(p.name, p)
        ranked = {n: r for n, p in pool.items() if (r := _relevance(query, p)) is not None}
    ordered = sorted(ranked, key=lambda n: (ranked[n], -pool[n].votes, -pool[n].popularity, n))
    return [pool[n] for n in ordered]


def info(names, fetch=default_fetch):
    names = [n for n in dict.fromkeys(names) if valid_name(n)]
    if not names:
        return []
    args = "&".join("arg[]=" + urllib.parse.quote(n, safe="") for n in names)
    return _decode(fetch(f"{RPC}/info?{args}"))


def warnings(pkg, now=None):
    """Motivos para el aviso reforzado (en rojo): lista de claves."""
    now = now if now is not None else time.time()
    reasons = []
    if not pkg.maintainer:
        reasons.append("orphan")
    if pkg.first_submitted and now - pkg.first_submitted < MIN_AGE_DAYS * 86400:
        reasons.append("new")
    if pkg.out_of_date:
        reasons.append("out-of-date")
    if pkg.votes < MIN_VOTES:
        reasons.append("few-votes")
    return reasons


def dep_name(dep):
    """«libfoo>=1.2: texto» → «libfoo»; None si no es un nombre válido."""
    m = DEP_RE.match((dep or "").split(":")[0].strip())
    return m.group(1) if m and valid_name(m.group(1)) else None


# --- settings y estado ---

def get_setting(key, default, path=SETTINGS_FILE):
    try:
        with open(path, "rb") as f:
            value = tomllib.load(f).get(key, default)
    except (OSError, tomllib.TOMLDecodeError):
        return default
    return value if isinstance(value, type(default)) else default


def set_setting(key, value, path=SETTINGS_FILE):
    path = Path(path)
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        data = {}
    data[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{k} = {str(v).lower() if isinstance(v, bool) else json.dumps(v)}" for k, v in data.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def aur_enabled(path=SETTINGS_FILE):
    return get_setting("aur_enabled", False, path)


def set_aur_enabled(enabled, path=SETTINGS_FILE):
    set_setting("aur_enabled", bool(enabled), path)


def load_state(path=STATE_FILE):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_state(state, path=STATE_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def record_install(pkgname, base, commit, version, path=STATE_FILE):
    state = load_state(path)
    state[pkgname] = {"base": base, "commit": commit, "version": version}
    save_state(state, path)


# --- git ---

def _git(runner, *args, cwd=None):
    out = runner(["git", *args], cwd)
    if out.returncode != 0:
        raise AurError((out.stderr or out.stdout or "git ha fallado").strip().splitlines()[-1])
    return out.stdout


def run_command(argv, cwd=None, timeout=300):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                          env={"GIT_TERMINAL_PROMPT": "0", "PATH": "/usr/bin:/bin", "LC_ALL": "C.UTF-8",
                                "HOME": str(Path.home())})


def clone(base, src_dir=SRC_DIR, runner=run_command, url_for=GIT_URL.format):
    """Clona (o actualiza) el repositorio del paquete base; devuelve (carpeta, commit)."""
    if not valid_name(base):
        raise AurError(f"nombre de paquete no válido: {base!r}")
    dest = Path(src_dir) / base
    Path(src_dir).mkdir(parents=True, exist_ok=True)
    if (dest / ".git").is_dir():
        _git(runner, "fetch", "--quiet", "origin", cwd=dest)
        _git(runner, "reset", "--quiet", "--hard", "origin/HEAD", cwd=dest)
    else:
        _git(runner, "clone", "--quiet", url_for(base), str(dest))
    return dest, _git(runner, "rev-parse", "HEAD", cwd=dest).strip()


def unchanged_since_review(folder, commit, runner=run_command):
    """True si la carpeta sigue en el commit revisado y sin cambios: entre la revisión y la
    compilación pueden pasar minutos (la actualización del sistema va antes)."""
    try:
        head = _git(runner, "rev-parse", "HEAD", cwd=folder).strip()
        dirty = _git(runner, "status", "--porcelain", "--untracked-files=all", cwd=folder).strip()
    except (AurError, OSError, subprocess.SubprocessError):
        return False
    return head == commit and not dirty


def _install_scripts(folder):
    """Nombres de los scripts que el PKGBUILD declara con `install=` (pacman los ejecuta como root al
    instalar, y pueden llamarse como sea, no solo `*.install`) más los `*.install` de la carpeta."""
    folder = Path(folder)
    names = {p.name for p in folder.glob("*.install")}
    pkgbuild = folder / "PKGBUILD"
    if pkgbuild.is_file() and not pkgbuild.is_symlink():
        text = pkgbuild.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"^\s*install=['\"]?([^'\"\s;#$]+)", text, re.M):
            if "/" not in m.group(1) and m.group(1) not in (".", ".."):
                names.add(m.group(1))
    return sorted(names)


def review_files(folder):
    """PKGBUILD y todos los scripts de instalación completos, en ese orden: lo que el usuario debe leer."""
    folder = Path(folder)
    result = []
    for name in ["PKGBUILD", *_install_scripts(folder)]:
        path = folder / name
        if path.is_file() and not path.is_symlink():
            result.append((name, path.read_text(encoding="utf-8", errors="replace")))
    return result


def unreviewable(folder):
    """Archivos que makepkg usaría pero que no se pueden mostrar al usuario (enlaces simbólicos)."""
    folder = Path(folder)
    return [n for n in ["PKGBUILD", *_install_scripts(folder)] if (folder / n).is_symlink()]


def diff_since(folder, old_commit, runner=run_command):
    """Cambios del PKGBUILD y los .install entre lo instalado y lo último; vacío si no hay."""
    if not re.fullmatch(r"[0-9a-f]{7,64}", old_commit or ""):
        raise AurError("commit instalado no válido")
    paths = ["PKGBUILD", "*.install", *_install_scripts(folder)]
    return _git(runner, "diff", f"{old_commit}..HEAD", "--", *dict.fromkeys(paths), cwd=folder)


# --- dependencias ---

@dataclass
class Plan:
    """Lo que hay que hacer para instalar un paquete: dependencias de los repos, paquetes del AUR
    (orden de instalación: primero las dependencias) y lo que no se ha podido resolver."""
    repo_deps: list = field(default_factory=list)
    aur_chain: list = field(default_factory=list)
    unresolved: list = field(default_factory=list)


def resolve(root, satisfied, in_repos, fetch=default_fetch):
    """Cadena de dependencias de `root` (AurPackage).

    satisfied(dep) → True si ya está instalada una dependencia (nombre o provides);
    in_repos(dep) → True si algún repositorio oficial la ofrece. El resto se busca en el AUR y
    cada paquete del AUR entra en la cadena (y se revisa) antes de usarse."""
    plan = Plan()
    seen = {root.name}

    def visit(pkg):
        for raw in (*pkg.depends, *pkg.makedepends, *pkg.checkdepends):
            name = dep_name(raw)
            if name is None:
                plan.unresolved.append(raw)
                continue
            if satisfied(name) or name in seen:
                continue
            if in_repos(name):
                if name not in plan.repo_deps:
                    plan.repo_deps.append(name)
                continue
            found = info([name], fetch)
            match = next((p for p in found if p.name == name), None)
            if match is None:
                plan.unresolved.append(name)
                continue
            seen.add(name)
            if len(seen) > MAX_CHAIN:
                raise AurError("la cadena de dependencias del AUR es demasiado larga")
            visit(match)
            plan.aur_chain.append(match)

    visit(root)
    plan.aur_chain.append(root)
    return plan


# --- actualizaciones ---

def newer_versions(installed, vercmp, fetch=default_fetch):
    """installed: {pkgname: versión}. Devuelve [AurPackage] cuya versión en el AUR es mayor."""
    names = [n for n in installed if valid_name(n)]
    found = {}
    for i in range(0, len(names), 40):
        for p in info(names[i:i + 40], fetch):
            found[p.name] = p
    return [p for n, p in found.items() if vercmp(p.version, installed[n]) > 0]


def foreign_packages(runner=run_command):
    """`pacman -Qm`: {nombre: versión} de lo que no está en los repos (el AUR, a efectos prácticos)."""
    out = runner(["pacman", "-Qm"])
    if out.returncode != 0:
        return {}
    pairs = (line.split() for line in out.stdout.splitlines())
    return {p[0]: p[1] for p in pairs if len(p) == 2}
