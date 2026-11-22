# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path

import pytest

from arctiva_games.core import games_script as gs

FIX = Path(__file__).parent / "fixtures" / "games"
GD = "/home/u/Games/ejemplo"


def load(name, game_dir=GD):
    return gs.plan(gs.parse((FIX / name).read_text()), game_dir)


def test_launcher_plan_and_heuristic():
    p = load("launcher-wait.yml")
    assert [s.kind for s in p.steps] == ["create_prefix", "set_regedit", "wineexec", "winekill", "write_json"]
    exec_step = p.steps[2]
    assert exec_step.wait_user and "Continuar" in exec_step.wait_message
    assert exec_step.description == "Instalando el lanzador"
    assert not p.steps[3].wait_user  # el winekill se ejecuta al continuar, no espera
    assert p.author == "autor-ejemplo" and p.credits == "Créditos de ejemplo"


def test_prefix_and_gamedir_substitution():
    p = load("launcher-wait.yml")
    assert p.prefix == f"{GD}/prefix"
    assert all(s.args["prefix"] == p.prefix for s in p.steps if s.kind != "write_json")
    assert p.steps[4].args["file"] == f"{GD}/drive_c/ProgramData/Launcher/config.json"
    assert p.game["exe"].startswith(GD)
    assert p.env == {"WINEDLLOVERRIDES": "dxgi=n"} and p.overrides == {"dxgi": "native"}
    assert p.steps[2].args["executable"] == "setup"  # `$id` de archivo lo resuelve el motor


def test_summary():
    s = gs.summary(load("launcher-wait.yml"))
    assert s["urls"] == ["https://example.com/Launcher-Setup.exe"]
    assert s["executables"] == ["setup"]
    assert s["registry_keys"] == [r"HKEY_CURRENT_USER\Software\Wine\Direct3D"]
    assert s["author"] == "autor-ejemplo" and s["credits"] == "Créditos de ejemplo"


def test_tricks_execute_and_user_files():
    p = load("tricks-execute.yml")
    s = gs.summary(p)
    assert s["winetricks"] == ["corefonts", "physx"]
    assert s["user_files"] == ["Selecciona el instalador del juego"]
    assert s["urls"] == ["https://example.com/setup.msi"]
    assert f"{GD}/run.sh" in s["executables"] and "killall helper" in s["executables"]
    assert p.steps[2].args["return_code"] == 768 and p.steps[2].args["exclude_processes"] == "helper.exe"
    assert not any(st.wait_user for st in p.steps)  # sin winekill detrás no hay espera
    assert p.steps[4].args == {"path": f"{GD}/run.sh"}


def test_api_json_and_explicit_wait():
    p = load("api.json")
    assert p.author == "autor-json" and p.steps[1].wait_user
    assert p.steps[1].wait_message == "Inicia sesión y pulsa Continuar."


def test_body_only_without_metadata():
    p = gs.plan(gs.parse("files: []\ninstaller:\n  - task: {name: create_prefix}\n"), GD)
    assert p.author == "" and len(p.steps) == 1


@pytest.mark.parametrize("text,name", [
    ("installer:\n  - copy: {src: a, dst: b}\n", "copy"),
    ("installer:\n  - task: {name: dosexec, executable: x}\n", "task:dosexec"),
    ("installer:\n  - task: {name: wineexec, executable: x, blocking: true}\n", "wineexec.blocking"),
    ("installer:\n  - task: {name: create_prefix, install_mono: true}\n", "create_prefix.install_mono"),
    ("system:\n  gamemode: true\ninstaller: []\n", "system.gamemode"),
    ("wine:\n  version: x\ninstaller: []\n", "wine.version"),
    ("game: {working_dir: x}\ninstaller: []\n", "game.working_dir"),
    ("require_binaries: x\ninstaller: []\n", "require_binaries"),
    ("extends: otro\ninstaller: []\n", "extends"),
])
def test_unsupported_names_the_command(text, name):
    with pytest.raises(gs.UnsupportedCommand) as e:
        gs.plan(gs.parse(text), GD)
    assert e.value.name == name


def test_unsupported_runner():
    with pytest.raises(gs.UnsupportedCommand) as e:
        gs.plan(gs.parse('{"runner": "dosbox", "script": {"installer": []}}'), GD)
    assert e.value.name == "runner:dosbox"


@pytest.mark.parametrize("text", [
    "- lista", "esto: [no cierra", "files:\n  - a: file:///etc/passwd\n", "installer:\n  - {a: 1, b: 2}\n",
    "files: x\n",
])
def test_invalid_script(text):
    with pytest.raises(gs.ScriptError):
        gs.plan(gs.parse(text), GD)
