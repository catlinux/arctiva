# SPDX-License-Identifier: GPL-3.0-or-later
import re
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from arctiva_center.__main__ import build_parser
from arctiva_center.core import i18n, paths
from arctiva_center.modules import MODULES

CENTER = Path(__file__).resolve().parents[1]


def test_catalog_candidates():
    assert i18n.catalog_candidates(["es-ES", "en-US"]) == ["es_ES", "es"]
    assert i18n.catalog_candidates(["ca"]) == ["ca"]
    assert i18n.catalog_candidates(["ca-ES", "es-ES"]) == ["ca_ES", "ca", "es_ES", "es"]
    # El inglés (idioma de los textos fuente) por delante de otro idioma: sin catálogo.
    assert i18n.catalog_candidates(["en-GB", "es-ES"]) == []
    assert i18n.catalog_candidates([]) == []


def test_paths_in_tree(monkeypatch):
    monkeypatch.delenv("ARCTIVA_CENTER_DATA", raising=False)
    where = paths.resolve()
    assert where.qml == CENTER / "qml"
    assert (where.data / "extras.toml").is_file()


def test_paths_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCTIVA_CENTER_DATA", str(tmp_path))
    assert paths.resolve().qml == tmp_path / "qml"


def test_parser():
    parser = build_parser()
    assert parser.parse_args([]).module is None
    assert parser.parse_args(["--welcome"]).welcome
    assert parser.parse_args(["--check"]).check
    for name in MODULES:
        assert parser.parse_args(["--module", name]).module == name
    with pytest.raises(SystemExit):
        parser.parse_args(["--module", "nope"])
    with pytest.raises(SystemExit):
        parser.parse_args(["--welcome", "--check"])


@pytest.mark.parametrize("name", ["extras", "errors", "delicate"])
def test_data_files_parse(name):
    data = tomllib.loads((CENTER / "data" / f"{name}.toml").read_text(encoding="utf-8"))
    assert data["version"] == 1


def test_delicate_patterns():
    data = tomllib.loads((CENTER / "data" / "delicate.toml").read_text(encoding="utf-8"))
    assert "linux*" in data["patterns"] and "grub" in data["patterns"]


@pytest.mark.parametrize("lang", ["es", "ca"])
def test_translations_cover_qml(lang):
    root = ET.parse(CENTER / "translations" / f"{lang}.ts").getroot()
    assert root.get("language") == lang
    contexts = {c.findtext("name"): c for c in root.findall("context")}
    # En QML, el contexto de qsTr es el nombre del archivo.
    for qml in sorted((CENTER / "qml").glob("*.qml")):
        sources = set(re.findall(r'qsTr\("([^"]+)"\)', qml.read_text(encoding="utf-8")))
        if not sources:
            continue
        context = contexts[qml.stem]
        translated = {
            m.findtext("source"): m.findtext("translation") for m in context.findall("message")
        }
        assert set(translated) == sources, qml.name
        assert all(translated.values()), qml.name


def test_desktop_file():
    text = (CENTER / "desktop" / "arctiva-center.desktop").read_text(encoding="utf-8")
    assert "Exec=arctiva-center\n" in text
    assert "Icon=arctiva\n" in text
    assert "Comment[es]=" in text and "Comment[ca]=" in text
