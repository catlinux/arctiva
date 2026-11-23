# SPDX-License-Identifier: GPL-3.0-or-later
"""Catálogo de aplicaciones (decisiones 2 y 3 de la fase 6): AppStream de Arch y de Flathub leído con
`xml.etree` (la API de GObject Introspection de libappstream no sirvió en la prueba de concepto),
fusionado por aplicación, con búsqueda sin tildes, categorías y fuente recomendada."""
import gzip
import pickle
import tomllib
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from . import fuzzy

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

ARCH_XML_DIR = "/usr/share/swcatalog/xml"
ARCH_ICON_DIR = "/usr/share/swcatalog/icons"
FLATHUB_DIR = "/var/lib/flatpak/appstream/flathub/x86_64/active"

# Categorías de la tienda (las principales de la especificación de menús de freedesktop).
CATEGORIES = ("AudioVideo", "Development", "Education", "Game", "Graphics", "Network", "Office",
              "Science", "System", "Utility")
SOURCES = ("arch", "flathub", "aur")


@dataclass
class Source:
    kind: str                  # «arch» o «flathub» («aur» lo añade la capa del AUR)
    ref: str                   # nombre de paquete (arch) o id de Flatpak (flathub)
    icon: str = ""
    origin: str = ""

    @property
    def label(self):
        return {"arch": "Arch", "flathub": "Flathub", "aur": "AUR"}[self.kind]


@dataclass
class App:
    id: str
    name: str
    summary: str = ""
    description: str = ""
    categories: tuple = ()
    keywords: tuple = ()
    license: str = ""
    homepage: str = ""
    screenshots: tuple = ()
    sources: list = field(default_factory=list)
    recommended: str = ""      # tipo de la fuente recomendada

    def source(self, kind):
        return next((s for s in self.sources if s.kind == kind), None)

    @property
    def icon(self):
        pick = self.source(self.recommended) or (self.sources[0] if self.sources else None)
        return pick.icon if pick and pick.icon else ""


def normalize(text):
    """Minúsculas y sin tildes: «Gráficos» y «graficos» coinciden."""
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold()


def app_id(raw):
    """Id común a las dos fuentes: sin «.desktop» y en minúsculas."""
    raw = (raw or "").strip()
    if raw.endswith(".desktop"):
        raw = raw[:-len(".desktop")]
    return raw.casefold()


def _text(el, tag, languages):
    """Elemento de `tag` en el primer idioma disponible; si no, el que no lleva idioma."""
    by_lang = {c.get(XML_LANG): c for c in el.findall(tag)}
    for lang in languages:
        for key in (lang, lang.replace("-", "_"), lang.replace("-", "_").split("_")[0]):
            if key in by_lang:
                return by_lang[key]
    return by_lang.get(None)


def _flat(el):
    """Descripción en texto: párrafos y listas separados por líneas."""
    if el is None:
        return ""
    lines = []
    for node in el:
        if node.tag == "p":
            lines.append(" ".join("".join(node.itertext()).split()))
        elif node.tag in ("ul", "ol"):
            lines.extend("• " + " ".join("".join(li.itertext()).split()) for li in node.findall("li"))
    return "\n".join(l for l in lines if l)


def _icon(comp, icon_dirs, origin):
    """Ruta del icono cacheado de mayor tamaño que exista (o el nombre de tema si es «stock»)."""
    best, size = "", -1
    for ic in comp.findall("icon"):
        kind, name = ic.get("type"), (ic.text or "").strip()
        if kind == "stock" and name and not best:
            best = name
        elif kind in ("cached", "local") and name:
            width = int(ic.get("width") or 0)
            for base in icon_dirs:
                for sub in (f"{origin}/{width}x{width}", f"{width}x{width}", f"{origin}/64x64", "64x64"):
                    path = Path(base) / sub / name
                    if path.is_file() and width >= size:
                        best, size = str(path), width
                        break
    return best


def parse(fileobj, kind, languages=("en",), icon_dirs=()):
    """Componentes de un archivo AppStream (formato «catalog») → lista de App."""
    root = ET.parse(fileobj).getroot()
    origin = root.get("origin") or ""
    apps = []
    for comp in root.findall("component"):
        if comp.get("type") not in ("desktop-application", "desktop"):
            continue
        cid = (comp.findtext("id") or "").strip()
        name = _text(comp, "name", languages)
        if not cid or name is None or not (name.text or "").strip():
            continue
        launch = comp.findtext("launchable[@type='desktop-id']")
        if kind == "arch":
            ref = (comp.findtext("pkgname") or "").strip()
        else:
            bundle = (comp.findtext("bundle[@type='flatpak']") or "").split("/")
            ref = bundle[1] if len(bundle) > 1 else cid
        if not ref:
            continue
        summary = _text(comp, "summary", languages)
        app = App(
            id=app_id(launch if kind == "flathub" and launch else cid),
            name=name.text.strip(),
            summary=(summary.text or "").strip() if summary is not None else "",
            description=_flat(_text(comp, "description", languages)),
            categories=tuple(c.text for c in comp.findall("categories/category") if c.text),
            keywords=tuple(k.text.strip() for k in comp.findall("keywords/keyword")
                           if k.text and k.get(XML_LANG) in (None, *languages)),
            license=(comp.findtext("project_license") or "").strip(),
            homepage=(comp.findtext("url[@type='homepage']") or "").strip(),
            screenshots=tuple((i.text or "").strip() for i in
                              comp.findall("screenshots/screenshot/image[@type='source']") if i.text),
        )
        app.sources.append(Source(kind, ref, _icon(comp, icon_dirs, origin), origin))
        apps.append(app)
    return apps


def _open(path):
    path = str(path)
    return gzip.open(path) if path.endswith(".gz") else open(path, "rb")


def load_files(files, languages=("en",), icon_dirs=()):
    """files: [(tipo, ruta)]. Devuelve la lista de App ya fusionadas."""
    catalog = {}
    for kind, path in files:
        try:
            with _open(path) as fh:
                apps = parse(fh, kind, languages, icon_dirs)
        except (OSError, ET.ParseError):
            continue
        for app in apps:
            known = catalog.get(app.id)
            if known is None:
                catalog[app.id] = app
                continue
            if not known.source(kind):
                known.sources.extend(app.sources)
            for attr in ("summary", "description", "license", "homepage"):
                if not getattr(known, attr) and getattr(app, attr):
                    setattr(known, attr, getattr(app, attr))
            known.categories = known.categories or app.categories
            known.keywords = tuple(dict.fromkeys(known.keywords + app.keywords))
            known.screenshots = known.screenshots or app.screenshots
    return list(catalog.values())


def default_files():
    files = [("arch", p) for p in sorted(Path(ARCH_XML_DIR).glob("*.xml.gz"))]
    flathub = Path(FLATHUB_DIR) / "appstream.xml.gz"
    if flathub.exists():
        files.append(("flathub", flathub))
    return files


def load_sources(path):
    """sources.toml: excepciones a la fuente recomendada ({id: «arch»|«flathub»})."""
    try:
        with open(path, "rb") as f:
            return {app_id(k): v for k, v in tomllib.load(f).get("recommended", {}).items()}
    except OSError:
        return {}


def recommend(app, overrides=None):
    """Arch > Flathub; el AUR nunca. Una excepción solo vale si esa fuente existe."""
    forced = (overrides or {}).get(app.id)
    if forced and app.source(forced) and forced != "aur":
        return forced
    for kind in ("arch", "flathub"):
        if app.source(kind):
            return kind
    return ""


class Catalog:
    def __init__(self, apps, overrides=None):
        self.apps = {a.id: a for a in apps}
        for app in self.apps.values():
            app.recommended = recommend(app, overrides)
        self._index = {a.id: normalize(" ".join((a.name, a.id, " ".join(a.keywords)))) for a in apps}
        self._summary = {a.id: normalize(a.summary) for a in apps}
        # Sin separadores («claude-code» = «claude code» = «claudecode») y con las palabras sueltas para las erratas.
        self._index_sq = {k: fuzzy.squash(v) for k, v in self._index.items()}
        self._summary_sq = {k: fuzzy.squash(v) for k, v in self._summary.items()}
        self._words = {k: set(fuzzy.tokens(v)) for k, v in self._index.items()}

    def __len__(self):
        return len(self.apps)

    def get(self, id_):
        return self.apps.get(app_id(id_))

    # Con menos aciertos exactos que estos, se completa con coincidencias con erratas.
    FUZZY_BELOW = 5

    def search(self, query, limit=400):
        """Todas las palabras deben aparecer (sin fijarse en guiones, espacios ni tildes); el nombre pesa
        más que las palabras clave y el resumen. Si salen pocos, se añaden los parecidos con erratas."""
        words = fuzzy.tokens(query)
        whole = fuzzy.squash(query)
        if not words:
            return []
        scored, seen = [], set()
        for app in self.apps.values():
            index, summary = self._index_sq[app.id], self._summary_sq[app.id]
            if not (all(w in index or w in summary for w in words) or whole in index):
                continue
            name = fuzzy.squash(app.name)
            score = sum(100 if name == w else 60 if name.startswith(w) else 30 if w in name
                        else 10 if w in index else 1 for w in words)
            if whole in name:
                score += 40
            scored.append((-score, name, app))
            seen.add(app.id)
        scored.sort(key=lambda t: t[:2])
        found = [a for _, _, a in scored]
        if len(found) < self.FUZZY_BELOW:
            near = []
            for app in self.apps.values():
                if app.id in seen:
                    continue
                total = fuzzy.fuzzy_total(words, self._words[app.id])
                if total is not None:
                    near.append((total, fuzzy.squash(app.name), app))
            near.sort(key=lambda t: t[:2])
            found += [a for _, _, a in near]
        return found[:limit]

    def category(self, name, limit=3000):
        found = [a for a in self.apps.values() if name in a.categories]
        found.sort(key=lambda a: normalize(a.name))
        return found[:limit]

    def category_counts(self):
        return {c: sum(1 for a in self.apps.values() if c in a.categories) for c in CATEGORIES}


def load_featured(path, catalog):
    """featured.toml: ids destacados, solo los que existen en el catálogo cargado."""
    try:
        with open(path, "rb") as f:
            ids = tomllib.load(f).get("featured", {}).get("ids", [])
    except OSError:
        return []
    return [a for a in (catalog.get(i) for i in ids) if a]


def cache_key(files):
    stats = [(str(p), Path(p).stat()) for _, p in files if Path(p).exists()]
    return [(name, st.st_mtime_ns, st.st_size) for name, st in stats]


def load_cached(files, cache_path, languages=("en",), icon_dirs=(), overrides=None):
    """Catálogo con caché `pickle`, invalidada por la fecha de los XML y el idioma."""
    key = (cache_key(files), tuple(languages), 1)
    try:
        with open(cache_path, "rb") as f:
            saved_key, apps = pickle.load(f)
        if saved_key == key:
            return Catalog(apps, overrides)
    except (OSError, pickle.UnpicklingError, EOFError, ValueError, AttributeError):
        pass
    apps = load_files(files, languages, icon_dirs)
    try:
        Path(cache_path).parent.mkdir(parents=True, exist_ok=True)
        tmp = str(cache_path) + ".tmp"
        with open(tmp, "wb") as f:
            pickle.dump((key, apps), f)
        Path(tmp).replace(cache_path)
    except OSError:
        pass
    return Catalog(apps, overrides)
