# SPDX-License-Identifier: GPL-3.0-or-later
import os
import subprocess
import sys
import time

from arctiva_games.core import games_procs


def _spawn(prefix, tmp_path):
    exe = tmp_path / "Fake Launcher.exe"
    exe.write_text("#!/bin/sh\nexec sleep 30\n")
    exe.chmod(0o755)
    env = dict(os.environ, WINEPREFIX=str(prefix))
    return subprocess.Popen([str(exe)], env=env)


def _wait(cond, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def test_ve_aparecer_y_desaparecer(tmp_path):
    prefix = tmp_path / "prefix"
    mon = games_procs.PrefixMonitor(prefix)
    assert mon.poll() == ([], [], [])
    p = _spawn(prefix, tmp_path)
    try:
        assert _wait(lambda: any(x.pid == p.pid for x in games_procs.list_processes(prefix)))
        alive, new, gone = mon.poll()
        assert p.pid in [x.pid for x in new] and not gone
        proc = next(x for x in alive if x.pid == p.pid)
        assert proc.uptime >= 0
        assert mon.poll()[1] == []
    finally:
        p.kill()
        p.wait()
    assert _wait(lambda: not games_procs.list_processes(prefix))
    _, new, gone = mon.poll()
    assert [x.pid for x in gone] == [p.pid] and not new


def test_otro_prefijo_no_cuenta(tmp_path):
    p = _spawn(tmp_path / "otro", tmp_path)
    try:
        assert _wait(lambda: any(x.pid == p.pid for x in games_procs.list_processes(tmp_path / "otro")))
        assert games_procs.list_processes(tmp_path / "prefix") == []
    finally:
        p.kill()
        p.wait()


def test_prefijo_con_barra_final_y_nombre_de_windows(tmp_path):
    prefix = tmp_path / "p"
    env = dict(os.environ, WINEPREFIX=str(prefix) + "/")
    p = subprocess.Popen(["sh", "-c", "exec -a 'C:\\\\Games\\\\Battle.net.exe' sleep 30"], env=env)
    try:
        assert _wait(lambda: any(x.pid == p.pid for x in games_procs.list_processes(prefix)))
        assert next(x for x in games_procs.list_processes(prefix) if x.pid == p.pid).name == "Battle.net.exe"
    finally:
        p.kill()
        p.wait()


def test_proc_inexistente_o_ilegible(tmp_path):
    assert games_procs.list_processes(tmp_path, proc_root=str(tmp_path / "no")) == []
    (tmp_path / "123").mkdir()  # sin environ: se ignora
    assert games_procs.list_processes(tmp_path, proc_root=str(tmp_path)) == []
