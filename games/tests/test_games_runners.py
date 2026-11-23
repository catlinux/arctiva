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
    assert gr.choose(gr.DEFAULT_PREFERENCE, runners).name == "Proton-Wineland Latest"
    assert gr.choose(["GE-Proton", "wine"], runners).name == "GE-Proton10-4"
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
    assert cmds[1].env["PROTONPATH"] == "/p/ge" and cmds[1].env["GAMEID"].startswith("umu-arctiva")
    assert cmds[1].env["UMU_CONTAINER_NSENTER"] == "1" and cmds[1].env["PROTON_ENABLE_WAYLAND"] == "0"
    wl = gr.umu_env("/p/Proton-Wineland Latest", "x")
    assert "PROTON_ENABLE_WAYLAND" not in wl and wl["GAMEID"] == gr.umu_env("/q/ge", "x")["GAMEID"]
    assert cmds[4].program == "/p/ge/files/bin/wineserver" and e.stop_command.program == cmds[4].program


def test_ordenes_con_wine_del_sistema(tmp_path):
    e = make_engine(tmp_path, None)
    cmds = [ge.default_command(s, e) for s in e.plan.steps]
    assert [c.program for c in cmds] == ["wineboot", "wine", "winetricks", "wine", "wineserver"]


def test_jugar_con_proton(tmp_path):
    g = lib.Game("x", "X", "/g/x.exe", "/g", "/g/prefix", {"A": "1"}, "/p/ge")
    assert lib.launch_argv(g, "/usr/bin/umu-run") == (
        "/usr/bin/umu-run", ["/g/x.exe"],
        {"WINEPREFIX": "/g/prefix", "A": "1", **gr.umu_env("/p/ge", "x")})
    try:
        lib.launch_argv(g, None)
        assert False
    except lib.LibraryError:
        pass
    g.runner = "wine"
    assert lib.launch_argv(g)[0] == "wine"


def test_sin_ejecutores_instalados_se_prefiere_descargar_ge_proton_al_wine_del_sistema(tmp_path):
    runners = gr.list_runners([tmp_path / "no"], which=lambda n: "/usr/bin/wine") + gr.virtual_runners()
    assert gr.choose(gr.DEFAULT_PREFERENCE, runners).path == gr.AUTO_GE             # antes: wine
    assert gr.choose(gr.DEFAULT_PREFERENCE, runners, umu=False).path == ""          # sin umu-run, solo wine
    assert gr.choose(["wine"], runners).path == ""                                  # la receta manda
    assert gr.choose(["Proton-Wineland", "wine"], runners).path == ""
    # Lo experimental (Wayland nativo) no se elige solo, pero se puede elegir a mano.
    wayland = [r for r in runners if r.name.startswith("GE-Proton, Wayland")][0]
    assert not wayland.auto_pick and wayland.wayland and gr.by_name(wayland.name, runners) is wayland


def test_lo_instalado_va_antes_que_lo_que_se_descarga(tmp_path):
    proton_dirs(tmp_path, ["UMU-Proton-9.0", "GE-Proton9-2"])
    runners = gr.list_runners([tmp_path], which=lambda n: "/usr/bin/wine") + gr.virtual_runners()
    assert gr.choose(gr.DEFAULT_PREFERENCE, runners).name == "GE-Proton9-2"
    only_umu = [r for r in runners if r.name != "GE-Proton9-2"]
    assert gr.choose(gr.DEFAULT_PREFERENCE, only_umu).name == "UMU-Proton-9.0"       # no descarga si ya hay uno


def test_umu_env_con_nombre_en_clave_y_wayland():
    auto = gr.umu_env(gr.AUTO_GE, "x")
    assert auto["PROTONPATH"] == "GE-Proton" and auto["PROTON_ENABLE_WAYLAND"] == "0"
    wl = gr.umu_env(gr.AUTO_GE + gr.WAYLAND, "x")
    assert wl["PROTONPATH"] == "GE-Proton" and wl["PROTON_ENABLE_WAYLAND"] == "1"
    assert gr.split_spec("/p/ge+wayland") == ("/p/ge", True) and gr.split_spec("/p/ge") == ("/p/ge", False)


def test_proton_dir_resuelve_el_nombre_en_clave(tmp_path):
    assert gr.proton_dir("GE-Proton", [tmp_path]) is None                             # aún sin descargar
    proton_dirs(tmp_path, ["GE-Proton9-2", "GE-Proton10-4", "UMU-Proton-9.0"])
    assert gr.proton_dir("GE-Proton", [tmp_path]).name == "GE-Proton10-4"
    assert gr.proton_dir("GE-Proton+wayland", [tmp_path]).name == "GE-Proton10-4"
    assert gr.proton_dir(str(tmp_path / "GE-Proton9-2")).name == "GE-Proton9-2"
    assert gr.proton_dir(str(tmp_path / "no-existe")) is None


def test_parar_un_ejecutor_sin_descargar_no_falla():
    assert ge.stop_command_for({"path": "GE-Proton-que-no-existe-todavia"}).program == "true"
    assert ge.stop_command_for(None).program == "wineserver"
