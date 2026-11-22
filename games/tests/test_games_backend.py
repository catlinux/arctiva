# SPDX-License-Identifier: GPL-3.0-or-later
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from arctiva_games import backend as gb
from arctiva_games.core import games_engine as ge
from arctiva_games.core import games_runtime
from arctiva_games.core.games_runners import Runner

DATA = Path(__file__).resolve().parents[1] / "data"


class FakeApi:
    def search(self, text):
        return [{"slug": "ejemplo", "name": "Ejemplo", "year": 2001}, {"slug": "../mal", "name": "Malo"}]

    def installers(self, slug):
        return [{"slug": slug, "name": "Ejemplo", "runner": "wine", "user": "alguien",
                 "script": {"game": {"exe": "$WINEPREFIX/Ej.exe"},
                            "installer": [{"execute": {"command": "echo hola"}}]}}]


WINE = [Runner("wine")]


@pytest.fixture(autouse=True)
def with_wine(monkeypatch):
    monkeypatch.setattr(gb.shutil, "which", lambda name: "/usr/bin/" + name)


@pytest.fixture
def app():
    return QCoreApplication.instance() or QCoreApplication([])


def wait_for(cond, timeout=10):
    end = time.time() + timeout
    while not cond():
        QCoreApplication.processEvents()
        time.sleep(0.01)
        assert time.time() < end, "tiempo agotado"


def make(tmp_path, live=False, runners=None, umu=None):
    scan = (lambda: (WINE if runners is None else runners, umu))
    return gb.GamesBackend(DATA, live, api=FakeApi(), base=tmp_path / "base", root=tmp_path / "Games",
                           downloads=tmp_path / "dl", runners=scan)


def test_busqueda_filtra_slugs_malos(app, tmp_path):
    b = make(tmp_path)
    b.search("ejemplo")
    wait_for(lambda: not b.searching)
    assert [r["slug"] for r in b.results] == ["ejemplo"]


def test_receta_da_resumen_y_pasos(app, tmp_path):
    b = make(tmp_path)
    assert {r["slug"] for r in b.recipes} >= {"battlenet", "epic-games"}
    b.prepareRecipe("battlenet")
    assert b.phase == "ready" and b.warnings == []
    assert b.summary["author"] == "Arctiva" and b.summary["urls"][0].startswith("https://")
    assert [s["state"] for s in b.steps] == ["pending", "pending"]


def test_instalar_registrar_y_desinstalar(app, tmp_path, monkeypatch):
    monkeypatch.setattr(ge, "default_command", lambda step, engine: ge.Command("sh", ["-c", "echo hecho"]))
    b = make(tmp_path)
    b.prepareOnline("ejemplo")
    wait_for(lambda: b.phase == "ready")
    assert b.summary["author"] == "alguien"
    b.install()
    wait_for(lambda: b.phase in ("done", "failed"))
    assert b.phase == "done"
    assert [g["slug"] for g in b.library] == ["ejemplo"]
    assert Path(b.logPath).is_file()
    assert b.uninstall("ejemplo") and b.library == []


def test_live_no_instala(app, tmp_path):
    b = make(tmp_path, live=True)
    b.prepareRecipe("battlenet")
    b.install()
    assert b.phase == "ready"


def test_orden_no_soportada_se_nombra(app, tmp_path):
    class Api(FakeApi):
        def installers(self, slug):
            return [{"slug": slug, "runner": "wine", "script": {"installer": [{"copy": {"src": "a", "dst": "b"}}]}}]
    b = gb.GamesBackend(DATA, False, api=Api(), base=tmp_path / "b", root=tmp_path / "G", runners=lambda: (WINE, None))
    b.prepareOnline("x")
    wait_for(lambda: b.error != "")
    assert "copy" in b.error and b.phase == "idle"


def test_descarga_fallida(app, tmp_path, monkeypatch):
    def boom(*a, **k):
        raise games_runtime.DownloadError("sin red")
    monkeypatch.setattr(games_runtime, "download_files", boom)
    b = make(tmp_path)
    b.prepareRecipe("battlenet")
    b.install()
    wait_for(lambda: b.phase == "failed")
    assert "sin red" in b.error


def test_sin_wine_no_se_instala(app, tmp_path, monkeypatch):
    monkeypatch.setattr(gb.shutil, "which", lambda name: None)
    b = make(tmp_path)
    b.prepareRecipe("ea-app")
    assert any("winetricks" in w for w in b.warnings)
    b.install()
    assert b.phase == "ready"
    b2 = make(tmp_path, runners=[])
    b2.prepareRecipe("ea-app")
    assert any("ningún ejecutor" in w for w in b2.warnings) and b2.runnerName == ""


def test_elige_proton_si_hay_umu(app, tmp_path):
    runners = [Runner("GE-Proton10-1", "/p/ge"), Runner("Proton-Wineland", "/p/wl"), Runner("wine")]
    b = make(tmp_path, runners=runners, umu="/usr/bin/umu-run")
    b.prepareRecipe("battlenet")
    assert b.runnerName == "GE-Proton10-1" and b.runnerChoices == ["GE-Proton10-1", "Proton-Wineland", "wine"]
    b.setRunner("wine")
    assert b.runnerName == "wine"
    sin_umu = make(tmp_path, runners=runners, umu=None)
    sin_umu.prepareRecipe("battlenet")
    assert sin_umu.runnerName == "wine" and sin_umu.runnerChoices == ["wine"]
