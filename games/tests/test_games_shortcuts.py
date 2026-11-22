# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_games.core import games_launch, games_library as lib, games_shortcuts as sc


def game(tmp_path, runner="wine"):
    d = tmp_path / "Games" / "demo"
    return lib.Game("demo", 'Demo "uno"', str(d / "Demo.exe"), str(d), str(d / "prefix"), {"A": "1"}, runner)


def test_crear_estado_y_quitar(tmp_path):
    g = game(tmp_path)
    sc.create(g, True, True, tmp_path / "menu", tmp_path / "desk")
    assert sc.status("demo", tmp_path / "menu", tmp_path / "desk") == {"menu": True, "desktop": True}
    text = (tmp_path / "menu" / "arctiva-games-demo.desktop").read_text()
    assert 'Exec=arctiva-games --play "demo"' in text and "Categories=Game;" in text
    assert (tmp_path / "desk" / "arctiva-games-demo.desktop").stat().st_mode & 0o100
    sc.remove("demo", tmp_path / "menu", tmp_path / "desk")
    assert sc.status("demo", tmp_path / "menu", tmp_path / "desk") == {"menu": False, "desktop": False}


def test_carpeta_del_escritorio(tmp_path):
    assert sc.desktop_dir(tmp_path) == tmp_path / "Desktop"
    (tmp_path / ".config").mkdir()
    (tmp_path / ".config" / "user-dirs.dirs").write_text('XDG_DESKTOP_DIR="$HOME/Escritorio"\n')
    assert sc.desktop_dir(tmp_path) == tmp_path / "Escritorio"


def test_nombre_sin_saltos_de_linea(tmp_path):
    g = game(tmp_path)
    g.name = "A\nExec=malo"
    assert "\nExec=malo" not in sc.entry(g.name, g.slug)


def test_play_lanza_y_registra(tmp_path, monkeypatch):
    g = game(tmp_path)
    (tmp_path / "Games" / "demo").mkdir(parents=True)
    lib.save(g, tmp_path / "base")
    seen = {}
    monkeypatch.setattr(games_launch.subprocess, "call",
                        lambda argv, cwd, env, stdout, stderr: seen.update(argv=argv, cwd=cwd, env=env) or 0)
    assert games_launch.run("demo", tmp_path / "base") == 0
    assert seen["argv"][0] == "wine" and seen["env"]["WINEPREFIX"].endswith("prefix")
    assert list((tmp_path / "base" / "logs").glob("demo-play-*.log"))
    assert games_launch.run("nada", tmp_path / "base") == 1
