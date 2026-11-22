# SPDX-License-Identifier: GPL-3.0-or-later
import json
import time

import pytest
from PySide6.QtCore import QCoreApplication

from arctiva_games.core import games_engine as ge
from arctiva_games.core import games_script as gs


@pytest.fixture(scope="module")
def app():
    return QCoreApplication.instance() or QCoreApplication([])


def wait_for(cond, timeout=10):
    end = time.time() + timeout
    while not cond():
        QCoreApplication.processEvents()
        time.sleep(0.01)
        assert time.time() < end, "tiempo agotado"


def make_plan(tmp_path, commands, wait_exec=None):
    """`commands`: órdenes de shell, cada una un paso `execute`; `wait_exec`: un wineexec con espera."""
    inst = [{"execute": {"command": c}} for c in commands]
    if wait_exec:
        inst.insert(1, {"task": {"name": "wineexec", "executable": "x", "args": wait_exec, "wait": "user",
                                 "description": "Lanzador"}})
    script = gs.parse(json.dumps({"name": "Ej", "slug": "ej", "script": {"installer": inst}}))
    return gs.plan(script, tmp_path / "game")


def command_for(step, engine):
    if step.kind == "wineexec":
        return ge.Command("sh", ["-c", step.args["args"]])
    return ge.default_command(step, engine)


def make_engine(tmp_path, plan, **kw):
    e = ge.GameEngine(plan, tmp_path / "games", command_for=command_for, stop_command=kw.pop("stop", False),
                      **kw)
    e.events = []
    e.stepChanged.connect(lambda i, s: e.events.append((i, s)))
    e.logs = []
    e.logLine.connect(e.logs.append)
    e.result = []
    e.finished.connect(e.result.append)
    e.waits = []
    e.waitingForUser.connect(lambda i, m: e.waits.append((i, m)))
    return e


def test_success_and_log(app, tmp_path):
    e = make_engine(tmp_path, make_plan(tmp_path, ["echo uno", "echo $WINEDEBUG; echo $WINEPREFIX"]))
    e.start()
    wait_for(lambda: e.result)
    assert e.result == [True] and e.states == [ge.DONE, ge.DONE]
    log = e.log_path.read_text()
    assert "=== [1/2]" in log and "=== [2/2]" in log and "uno" in log
    assert "-all" in log and f"{tmp_path}/game/prefix" in log
    assert e.log_path.parent == tmp_path / "games" / "logs" and e.log_path.name.startswith("ej-")
    assert not e.state_path.exists()  # terminado: no queda estado que reanudar


def test_detailed_does_not_set_winedebug(app, tmp_path, monkeypatch):
    monkeypatch.delenv("WINEDEBUG", raising=False)
    e = make_engine(tmp_path, make_plan(tmp_path, ["echo debug=[$WINEDEBUG]"]), detailed=True)
    e.start()
    wait_for(lambda: e.result)
    assert "debug=[]" in e.log_path.read_text()


def test_fail_stops_then_retry_succeeds(app, tmp_path):
    flag = tmp_path / "flag"
    e = make_engine(tmp_path, make_plan(tmp_path, [f"test -f {flag}", "echo después"]))
    e.start()
    wait_for(lambda: (0, ge.FAILED) in e.events)
    assert e.states == [ge.FAILED, ge.PENDING] and not e.result  # no sigue solo
    assert "código de salida 1" in "\n".join(e.logs)
    flag.write_text("x")
    e.retry()
    wait_for(lambda: e.result)
    assert e.result == [True] and e.states == [ge.DONE, ge.DONE]


def test_skip_failed(app, tmp_path):
    e = make_engine(tmp_path, make_plan(tmp_path, ["false", "echo ok"]))
    e.start()
    wait_for(lambda: (0, ge.FAILED) in e.events)
    e.skip()
    wait_for(lambda: e.result)
    assert e.states == [ge.SKIPPED, ge.DONE] and e.result == [True]


def test_failed_to_start(app, tmp_path):
    plan = make_plan(tmp_path, ["true"])
    e = ge.GameEngine(plan, tmp_path / "games", command_for=lambda s, en: ge.Command("/no/existe", []),
                      stop_command=False)
    e.start()
    wait_for(lambda: e.states == [ge.FAILED])


def test_return_code_accepts_old_multiplied_codes(app, tmp_path):
    inst = [{"task": {"name": "wineexec", "executable": "x", "args": "exit 3", "return_code": 768}}]
    plan = gs.plan(gs.parse(json.dumps({"slug": "rc", "script": {"installer": inst}})), tmp_path / "g")
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.result)
    assert e.states == [ge.DONE]


def test_stop_midway_runs_stop_command_and_keeps_state(app, tmp_path):
    marker = tmp_path / "killed"
    stop = ge.Command("sh", ["-c", f'echo "$WINEPREFIX" > {marker}'])
    e = make_engine(tmp_path, make_plan(tmp_path, ["echo a", "sleep 30", "echo c"]), stop=stop)
    e.start()
    wait_for(lambda: (1, ge.RUNNING) in e.events)
    e.stop()
    assert e.result == [False]
    assert marker.read_text().strip() == f"{tmp_path}/game/prefix"
    assert e.states == [ge.DONE, ge.PENDING, ge.PENDING]
    assert json.loads(e.state_path.read_text())["steps"][1]["state"] == ge.PENDING


def test_resume_from_saved_state(app, tmp_path):
    flag = tmp_path / "flag"
    plan = make_plan(tmp_path, ["echo a", f"[ -f {flag} ] || sleep 30", "echo c"])
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: (1, ge.RUNNING) in e.events)
    e.stop()
    flag.write_text("x")
    e2 = make_engine(tmp_path, plan)
    assert e2.has_saved_state()
    e2.start()
    wait_for(lambda: e2.result)
    assert e2.result == [True]
    # Si los dos registros caen en el mismo segundo comparten archivo: el paso 1 aparece solo de la 1.ª vez.
    assert e2.log_path.read_text().count("=== [1/3]") == 1
    assert e2.states == [ge.DONE] * 3


def test_saved_state_of_other_plan_is_ignored(app, tmp_path):
    e = make_engine(tmp_path, make_plan(tmp_path, ["echo a", "false"]))
    e.start()
    wait_for(lambda: e.states == [ge.DONE, ge.FAILED])
    e.stop()
    assert make_engine(tmp_path, make_plan(tmp_path, ["echo a", "false"])).has_saved_state()
    # Mismo número de pasos (mismos ids) pero script cambiado: no se reanuda.
    assert not make_engine(tmp_path, make_plan(tmp_path, ["echo a", "echo b"])).has_saved_state()


def test_winedebug_cannot_be_reenabled_by_script(app, tmp_path):
    inst = [{"execute": {"command": "echo dbg=$WINEDEBUG", "env": {"WINEDEBUG": "+all"}}}]
    plan = gs.plan(gs.parse(json.dumps({"slug": "dbg", "script": {"installer": inst}})), tmp_path / "g")
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.result)
    assert "dbg=-all" in e.log_path.read_text()


def test_launcher_output_does_not_mix_with_next_step(app, tmp_path):
    # El lanzador escribe sin salto de línea mientras corre el paso siguiente.
    launcher = "printf AAAA; sleep 0.3; printf BBBB; sleep 30"
    plan = make_plan(tmp_path, ["echo a", "printf xx; sleep 0.5; echo yy"], wait_exec=launcher)
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.waits)
    proc = e._background[0]
    e.continue_()
    wait_for(lambda: e.result)
    assert "xxyy" in e.logs and not any("AAAA" in line and "xx" in line for line in e.logs)
    proc.kill()
    proc.waitForFinished(2000)


def test_wait_for_user_does_not_wait_nor_kill(app, tmp_path):
    out = tmp_path / "out"
    plan = make_plan(tmp_path, ["echo antes", "echo después"], wait_exec=f"echo lanzador; sleep 30")
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.waits)
    assert e.waits[0][0] == 1 and "Continuar" in e.waits[0][1]
    assert e.states == [ge.DONE, ge.RUNNING, ge.PENDING] and not e.result
    proc = e._background[0]
    wait_for(lambda: "lanzador" in "\n".join(e.logs))
    e.continue_()
    wait_for(lambda: e.result)
    assert e.result == [True] and e.states == [ge.DONE] * 3
    assert proc.state() != proc.ProcessState.NotRunning  # sigue vivo: lo cierra el winekill posterior
    proc.kill()
    proc.waitForFinished(2000)


def test_wait_process_exit_is_logged_and_still_waits(app, tmp_path):
    plan = make_plan(tmp_path, ["echo a"], wait_exec="exit 5")
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: "terminó con código 5" in "\n".join(e.logs))
    assert e.waits and not e.result
    e.continue_()
    wait_for(lambda: e.result)
    assert e.result == [True]


def test_stop_while_waiting_kills_launcher(app, tmp_path):
    plan = make_plan(tmp_path, ["echo a"], wait_exec="sleep 30")
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.waits)
    proc = e._background[0]
    e.stop()
    assert proc.state() == proc.ProcessState.NotRunning and e.result == [False]
    assert e.states[1] == ge.PENDING


def test_native_steps_stay_inside_game_dir(app, tmp_path):
    game = tmp_path / "game"
    inst = [{"write_file": {"file": "$GAMEDIR/a/run.sh", "content": "#!/bin/sh\n"}},
            {"chmodx": "$GAMEDIR/a/run.sh"},
            {"write_json": {"file": "$GAMEDIR/c.json", "data": {"k": 1}}},
            {"write_file": {"file": str(tmp_path / "fuera.txt"), "content": "no"}}]
    plan = gs.plan(gs.parse(json.dumps({"slug": "nat", "script": {"installer": inst}})), game)
    e = make_engine(tmp_path, plan)
    e.start()
    wait_for(lambda: e.states[3] == ge.FAILED)
    assert e.states[:3] == [ge.DONE] * 3
    assert (game / "a" / "run.sh").stat().st_mode & 0o111
    assert json.loads((game / "c.json").read_text()) == {"k": 1}
    assert not (tmp_path / "fuera.txt").exists() and "fuera de la carpeta" in "\n".join(e.logs)


def test_codes_and_overrides():
    from types import SimpleNamespace as NS
    assert ge.accepted_codes(NS(args={})) == {0}
    assert ge.accepted_codes(NS(args={"return_code": "0,3"})) == {0, 3}
    assert ge.accepted_codes(NS(args={"return_code": 768})) == {768, 3}
    assert ge.dll_overrides({"dxgi": "native", "d3d9": "native,builtin"}) == "dxgi=n;d3d9=n,b"
