# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_games.core import games_engine as ge
from arctiva_games.core import games_library as lib
from arctiva_games.core import games_runners as gr
from arctiva_games.core import games_script as gs


def proton_dirs(tmp_path, names):
    for n in names:
        (tmp_path / n).mkdir()
        (tmp_path / n / "proton").write_text("#!/bin/sh\n")
    (tmp_path / "otra").mkdir()  # sin `proton`: no cuenta


def test_lista_y_elige_la_mas_nueva(tmp_path):
    proton_dirs(tmp_path, ["GE-Proton9-2", "GE-Proton10-4", "Proton-Wineland Latest", "UMU-Proton-9.0"])
    runners = gr.list_runners([tmp_path], which=lambda n: "/usr/bin/wine")
    assert [r.name for r in runners][-1] == "wine" and "otra" not in [r.name for r in runners]
    assert gr.choose(gr.DEFAULT_PREFERENCE, runners).name == "GE-Proton10-4"
    assert gr.choose(["proton-wineland", "wine"], runners).name == "Proton-Wineland Latest"
    assert gr.choose(["wine"], runners).path == ""
    assert gr.choose(["GE-Proton"], runners, umu=False) is None


def test_sin_nada(tmp_path):
    assert gr.list_runners([tmp_path / "no"], which=lambda n: None) == []
    assert gr.choose(None, []) is None


def make_engine(tmp_path, runner):
    script = gs.parse('{"slug":"x","script":{"files":[{"setup":"https://e.com/a.exe"}],"installer":['
                      '{"task":{"name":"create_prefix"}},{"task":{"name":"wineexec","executable":"setup","args":"/S"}},'
                      '{"task":{"name":"winetricks","app":"corefonts win10"}},'
                      '{"task":{"name":"set_regedit","path":"HKCU\\\\X","key":"k","value":"1"}},'
                      '{"task":{"name":"winekill"}}]}}')
    return ge.GameEngine(gs.plan(script, tmp_path / "g"), tmp_path / "b", files={"setup": "/dl/a.exe"}, runner=runner)


def test_ordenes_con_proton(tmp_path):
    e = make_engine(tmp_path, {"path": "/p/ge", "umu": "/usr/bin/umu-run"})
    cmds = [ge.default_command(s, e) for s in e.plan.steps]
    assert all(c.program == "/usr/bin/umu-run" for c in cmds[:4])
    assert cmds[0].args == ["wineboot", "-u"] and cmds[1].args == ["/dl/a.exe", "/S"]
    assert cmds[2].args == ["winetricks", "-q", "corefonts", "win10"] and cmds[3].args[:2] == ["reg", "add"]
    assert cmds[1].env == {"PROTONPATH": "/p/ge", "GAMEID": "umu-0"}
    assert cmds[4].program == "/p/ge/files/bin/wineserver" and e.stop_command.program == cmds[4].program


def test_ordenes_con_wine_del_sistema(tmp_path):
    e = make_engine(tmp_path, None)
    cmds = [ge.default_command(s, e) for s in e.plan.steps]
    assert [c.program for c in cmds] == ["wineboot", "wine", "winetricks", "wine", "wineserver"]


def test_jugar_con_proton(tmp_path):
    g = lib.Game("x", "X", "/g/x.exe", "/g", "/g/prefix", {"A": "1"}, "/p/ge")
    assert lib.launch_argv(g, "/usr/bin/umu-run") == (
        "/usr/bin/umu-run", ["/g/x.exe"],
        {"WINEPREFIX": "/g/prefix", "A": "1", "PROTONPATH": "/p/ge", "GAMEID": "umu-0"})
    try:
        lib.launch_argv(g, None)
        assert False
    except lib.LibraryError:
        pass
    g.runner = "wine"
    assert lib.launch_argv(g)[0] == "wine"
