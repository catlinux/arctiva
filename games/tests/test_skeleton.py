# SPDX-License-Identifier: GPL-3.0-or-later
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from arctiva_games.core import paths

GAMES = Path(__file__).resolve().parents[1]


def test_paths_in_tree(monkeypatch):
    monkeypatch.delenv("ARCTIVA_GAMES_DATA", raising=False)
    where = paths.resolve()
    assert where.qml == GAMES / "qml" and (where.data / "games.toml").is_file()


def test_paths_override(monkeypatch, tmp_path):
    monkeypatch.setenv("ARCTIVA_GAMES_DATA", str(tmp_path))
    assert paths.resolve().qml == tmp_path / "qml"


@pytest.mark.parametrize("lang", ["es", "ca"])
def test_translations_cover_qml(lang):
    root = ET.parse(GAMES / "translations" / f"{lang}.ts").getroot()
    assert root.get("language") == lang
    contexts = {c.findtext("name"): c for c in root.findall("context")}
    for qml in sorted((GAMES / "qml").glob("*.qml")):
        sources = set(re.findall(r'qsTr\("([^"]+)"', qml.read_text(encoding="utf-8")))
        if not sources:
            continue
        translated = {m.findtext("source"): m.findtext("translation") for m in contexts[qml.stem].findall("message")}
        assert set(translated) == sources, qml.name
        assert all(translated.values()), qml.name


def test_desktop_file():
    text = (GAMES / "desktop" / "arctiva-games.desktop").read_text(encoding="utf-8")
    assert "Exec=arctiva-games\n" in text and "Comment[es]=" in text and "Comment[ca]=" in text
