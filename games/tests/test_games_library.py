# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from arctiva_games.core import games_library as lib
from arctiva_games.core import games_recipes, games_runtime, games_script
from arctiva_games.core.games_runtime import DownloadError

CENTER = Path(__file__).resolve().parents[1]


def sample(tmp_path, slug="demo"):
    d = tmp_path / "Games" / slug
    (d / "prefix").mkdir(parents=True)
    (d / "prefix" / "f.txt").write_text("x")
    return lib.Game(slug, 'Demo "uno"', str(d / "prefix/Demo.exe"), str(d), str(d / "prefix"),
                    {"WINEDEBUG": "-all", "A B": "ñ\\x"})


def test_guardar_y_leer(tmp_path):
    base, g = tmp_path / "base", sample(tmp_path)
    lib.save(g, base)
    assert lib.list_games(base) == [g]
    assert lib.get("demo", base) == g
    assert lib.get("../x", base) is None


def test_lanzar(tmp_path):
    prog, args, env = lib.launch_argv(sample(tmp_path))
    assert prog == "wine" and args == [str(tmp_path / "Games/demo/prefix/Demo.exe")]
    assert env["WINEPREFIX"].endswith("prefix")


def test_desinstalar(tmp_path):
    base, g = tmp_path / "base", sample(tmp_path)
    lib.save(g, base)
    (base / "demo.state.json").write_text("{}")
    lib.remove("demo", base, tmp_path / "Games")
    assert not (tmp_path / "Games" / "demo").exists()
    assert lib.list_games(base) == [] and not (base / "demo.state.json").exists()


def test_no_borra_fuera_de_la_raiz(tmp_path):
    base, g = tmp_path / "base", sample(tmp_path)
    g.game_dir = str(tmp_path)
    lib.save(g, base)
    with pytest.raises(lib.LibraryError):
        lib.remove("demo", base, tmp_path / "Games")
    assert (tmp_path / "Games" / "demo").exists()
    with pytest.raises(lib.LibraryError):
        lib.remove("nada", base, tmp_path / "Games")


def test_slug_invalido():
    for bad in ("", "../x", "a/b", "A", "a..b"):
        with pytest.raises(lib.LibraryError):
            lib.game_dir(bad)


class Resp:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self, n):
        d, self.data = self.data[:n], self.data[n:]
        return d


def test_descarga(tmp_path):
    script = games_script.parse((CENTER / "tests/fixtures/games/launcher-wait.yml").read_text())
    plan = games_script.plan(script, tmp_path / "g")
    seen = []
    files = games_runtime.download_files(plan, tmp_path / "dl", seen.append, lambda url: Resp(b"MZ" * 10))
    assert (tmp_path / "dl/launcher-example/Launcher-Setup.exe").read_bytes() == b"MZ" * 10
    assert files == {"setup": str(tmp_path / "dl/launcher-example/Launcher-Setup.exe")}
    assert any("example.com" in s for s in seen)


def test_descarga_vacia_o_fallida(tmp_path):
    script = games_script.parse((CENTER / "tests/fixtures/games/launcher-wait.yml").read_text())
    plan = games_script.plan(script, tmp_path / "g")
    with pytest.raises(DownloadError):
        games_runtime.download_files(plan, tmp_path / "dl", opener=lambda u: Resp(b""))

    def boom(url):
        raise OSError("sin red")
    with pytest.raises(DownloadError, match="sin red"):
        games_runtime.download_files(plan, tmp_path / "dl", opener=boom)
    assert not list((tmp_path / "dl").rglob("*.part"))


def test_recetas_propias_se_entienden(tmp_path):
    recipes = games_recipes.load(CENTER / "data")
    assert {r["slug"] for r in recipes} >= {"battlenet", "ea-app", "ubisoft-connect", "gog-galaxy", "epic-games"}
    for r in recipes:
        plan = games_script.plan(games_script.parse(r["script"]), tmp_path / r["slug"])
        assert plan.steps and plan.game["exe"].startswith(plan.prefix)
        assert not games_runtime.unsupported_steps(plan), r["slug"]
        assert all(f.url.startswith("https://") for f in plan.files)
    bn = games_script.plan(games_script.parse(recipes[0]["script"]), tmp_path / "b")
    assert bn.steps[-1].wait_user  # D-G5: Battle.net queda abierto hasta pulsar Continuar
