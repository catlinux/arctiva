# SPDX-License-Identifier: GPL-3.0-or-later
import gzip
import shutil
from pathlib import Path

import pytest

from arctiva_center.core import appstream as ap

FIX = Path(__file__).parent / "fixtures"
FILES = [("arch", FIX / "arch-catalog.xml"), ("flathub", FIX / "flathub-catalog.xml")]


@pytest.fixture
def catalog():
    return ap.Catalog(ap.load_files(FILES, ("es", "en")), {"org.ejemplo.bottles": "flathub"})


def test_normalize_and_id():
    assert ap.normalize("Gráficos Ñandú") == "graficos nandu"
    assert ap.app_id("Editor.desktop") == "editor"
    assert ap.app_id(" org.Foo.Bar ") == "org.foo.bar"


def test_parse_arch_skips_non_apps_and_picks_language():
    with open(FILES[0][1], "rb") as f:
        apps = ap.parse(f, "arch", ("es", "en"))
    assert [a.id for a in apps] == ["org.ejemplo.pintor", "editor", "org.ejemplo.bottles"]
    pintor = apps[0]
    assert pintor.name == "Pintor digital"          # idioma preferido
    assert pintor.summary == "Draw and touch up pictures"  # solo hay en inglés y sin idioma: el de «en»
    assert pintor.sources[0].ref == "pintor" and pintor.sources[0].kind == "arch"
    assert pintor.description == "Primer párrafo.\n• Capas\n• Pinceles"
    assert pintor.categories == ("Graphics", "Qt") and pintor.keywords == ("dibujo", "paint")
    assert pintor.screenshots == ("https://ejemplo.org/a.png",)
    with open(FILES[0][1], "rb") as f:
        fallback = ap.parse(f, "arch", ("fr",))
    assert fallback[0].name == "Pintor" and fallback[0].summary == "Dibuja y retoca imágenes"


def test_merge_sources(catalog):
    pintor = catalog.get("org.ejemplo.pintor")
    assert [s.kind for s in pintor.sources] == ["arch", "flathub"]
    assert pintor.source("flathub").ref == "org.ejemplo.pintor"
    assert pintor.description  # se conserva el de Arch
    assert len(catalog) == 4


def test_recommended(catalog):
    assert catalog.get("org.ejemplo.pintor").recommended == "arch"      # Arch > Flathub
    assert catalog.get("org.ejemplo.bottles").recommended == "flathub"  # excepción
    assert catalog.get("org.ejemplo.soloflathub").recommended == "flathub"
    assert catalog.get("editor.desktop").recommended == "arch"


def test_recommend_ignores_override_without_source_and_never_aur():
    app = ap.App("x", "X", sources=[ap.Source("arch", "x")])
    assert ap.recommend(app, {"x": "flathub"}) == "arch"
    assert ap.recommend(app, {"x": "aur"}) == "arch"
    assert ap.recommend(ap.App("y", "Y"), {}) == ""


def test_search_accents_words_and_ranking(catalog):
    assert [a.id for a in catalog.search("pintor")][0] == "org.ejemplo.pintor"
    assert [a.id for a in catalog.search("EDITOR texto")] == ["editor"]
    assert [a.id for a in catalog.search("naipes")] == ["org.ejemplo.soloflathub"]   # palabra clave
    assert [a.id for a in catalog.search("DRAW pintór")] == ["org.ejemplo.pintor"]  # resumen y sin tildes
    assert catalog.search("") == [] and catalog.search("zzzz") == []


def test_categories(catalog):
    assert [a.id for a in catalog.category("Utility")] == ["org.ejemplo.bottles", "editor"]
    assert catalog.category_counts()["Game"] == 1 and catalog.category_counts()["Science"] == 0


def test_icons_from_cache_dir(tmp_path):
    icons = tmp_path / "icons" / "prueba-arch" / "64x64"
    icons.mkdir(parents=True)
    (icons / "org.ejemplo.pintor.png").write_bytes(b"png")
    apps = ap.load_files(FILES[:1], ("en",), [tmp_path / "icons"])
    by_id = {a.id: a for a in apps}
    assert by_id["org.ejemplo.pintor"].icon.endswith("org.ejemplo.pintor.png")
    assert by_id["editor"].icon == "accessories-text-editor"   # icono de tema
    assert by_id["org.ejemplo.bottles"].icon == ""


def test_featured_only_existing(tmp_path, catalog):
    path = tmp_path / "f.toml"
    path.write_text('[featured]\nids = ["org.ejemplo.pintor", "no.existe", "editor"]\n')
    assert [a.id for a in ap.load_featured(path, catalog)] == ["org.ejemplo.pintor", "editor"]
    assert ap.load_featured(tmp_path / "nada.toml", catalog) == []


def test_load_sources_and_shipped_data():
    data = Path(__file__).resolve().parents[1] / "data"
    sources = ap.load_sources(data / "sources.toml")
    assert sources["com.usebottles.bottles"] == "flathub"
    assert all(v in ("arch", "flathub") for v in sources.values())
    assert ap.load_sources(data / "no-existe.toml") == {}
    import tomllib
    featured = tomllib.loads((data / "featured.toml").read_text(encoding="utf-8"))["featured"]["ids"]
    assert len(featured) == 12 and len(set(featured)) == 12


def test_gz_and_broken_files(tmp_path):
    gz = tmp_path / "a.xml.gz"
    with open(FILES[0][1], "rb") as src, gzip.open(gz, "wb") as dst:
        shutil.copyfileobj(src, dst)
    bad = tmp_path / "bad.xml"
    bad.write_text("<components><component>")
    apps = ap.load_files([("arch", gz), ("arch", bad), ("arch", tmp_path / "falta.xml")])
    assert len(apps) == 3


def test_cache_roundtrip_and_invalidation(tmp_path):
    xml = tmp_path / "arch.xml"
    shutil.copy(FILES[0][1], xml)
    cache = tmp_path / "cache" / "catalog.pickle"
    files = [("arch", xml)]
    first = ap.load_cached(files, cache, ("en",))
    assert cache.exists() and len(first) == 3
    xml.write_text(xml.read_text(encoding="utf-8").replace("Editor de texto", "Editor nuevo"), encoding="utf-8")
    again = ap.load_cached(files, cache, ("en",))   # el XML cambió: se recarga
    assert again.get("editor").name == "Editor nuevo"
    cache.write_bytes(b"roto")
    assert len(ap.load_cached(files, cache, ("en",))) == 3   # caché dañada: se rehace
