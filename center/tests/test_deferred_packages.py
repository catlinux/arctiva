# SPDX-License-Identifier: GPL-3.0-or-later
"""Aplicaciones que no van en la ISO: la lista, el instalador y los dos scripts (con pacman, nm-online y
notify-send de mentira)."""
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SETTINGS = ROOT / "packages" / "arctiva-settings" / "files"
LIST = SETTINGS / "usr" / "share" / "arctiva" / "deferred-packages"
INSTALL = SETTINGS / "usr" / "lib" / "arctiva" / "install-deferred"
NOTIFY = SETTINGS / "usr" / "lib" / "arctiva" / "notify-deferred"
SH = shutil.which("sh")


def listed():
    return [l.strip() for l in LIST.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]


def try_install_blocks():
    """Paquetes de cada `try_install` de packages.conf, en orden."""
    blocks, current, indent = [], None, 0
    for line in (ROOT / "installer/calamares/modules/packages.conf").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "- try_install:":
            current, indent = [], len(line) - len(line.lstrip())
            blocks.append(current)
        elif current is not None and stripped.startswith("- ") and len(line) - len(line.lstrip()) > indent:
            current.append(stripped[2:].strip())
        elif stripped and not stripped.startswith("#"):
            current = None
    return blocks


def test_list_is_what_calamares_installs_and_the_iso_leaves_out():
    names = listed()
    assert len(names) == len(set(names)) >= 1
    assert names in try_install_blocks()
    iso = {l.strip() for l in (ROOT / "iso/packages.x86_64").read_text(encoding="utf-8").splitlines()
           if l.strip() and not l.startswith("#")}
    assert not iso & set(names)
    assert all(re.fullmatch(r"[a-z0-9@._+-]+", n) for n in names)


def test_package_installs_the_units_and_links():
    pkgbuild = (ROOT / "packages/arctiva-settings/PKGBUILD").read_text(encoding="utf-8")
    for needle in ("deferred-packages", "install-deferred", "notify-deferred", "arctiva-deferred.service",
                   "90-arctiva-deferred", "arctiva-deferred-notify.path", "multi-user.target.wants",
                   "paths.target.wants", "default.target.wants", "libnotify", "networkmanager"):
        assert needle in pkgbuild, needle
    for rel in ("usr/lib/systemd/system/arctiva-deferred.service", "usr/lib/systemd/user/arctiva-deferred-notify.path",
                "usr/lib/systemd/user/arctiva-deferred-notify.service", "etc/NetworkManager/dispatcher.d/90-arctiva-deferred"):
        assert (SETTINGS / rel).is_file(), rel
    # La live no los usa: ninguna unidad debe arrancar allí.
    for rel in ("usr/lib/systemd/system/arctiva-deferred.service", "usr/lib/systemd/user/arctiva-deferred-notify.path",
                "usr/lib/systemd/user/arctiva-deferred-notify.service"):
        assert "ConditionPathExists=!/run/archiso" in (SETTINGS / rel).read_text(encoding="utf-8")


pytestmark_sh = pytest.mark.skipif(SH is None, reason="hace falta sh")


def stub(path, body):
    path.write_text("#!/bin/sh\n" + body, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


@pytest.fixture
def env(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    state = tmp_path / "state"
    installed = tmp_path / "installed"
    installed.write_text("", encoding="utf-8")
    calls = tmp_path / "calls"
    stub(bin_dir / "pacman", f'''case "$1" in
    -Qq) grep -qx -- "$3" "{installed}" ;;
    -Syu) echo "$@" >> "{calls}"; [ -e "{tmp_path}/pacman-fails" ] && exit 1; exit 0 ;;
esac
''')
    stub(bin_dir / "nm-online", f'[ ! -e "{tmp_path}/offline" ]\n')
    e = dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}", DEFERRED_LIST=str(LIST),
             DEFERRED_STATE_DIR=str(state), DEFERRED_LOCK=str(tmp_path / "db.lck"))
    return NS(env=e, tmp=tmp_path, state=state / "deferred.status", calls=calls, installed=installed, bin=bin_dir)


class NS:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def run_install(ctx):
    return subprocess.run([SH, str(INSTALL)], env=ctx.env, capture_output=True, text=True)


def status(ctx):
    lines = ctx.state.read_text(encoding="utf-8").splitlines()
    return lines[0], (lines[1] if len(lines) > 1 else "")


@pytestmark_sh
def test_nothing_missing_is_done(env):
    env.installed.write_text("\n".join(listed()) + "\n", encoding="utf-8")
    assert run_install(env).returncode == 0
    assert status(env) == ("done", "")
    assert not env.calls.exists()


@pytestmark_sh
def test_offline_is_pending_and_does_not_install(env):
    (env.tmp / "offline").write_text("", encoding="utf-8")
    assert run_install(env).returncode == 0
    state, pkgs = status(env)
    assert state == "pending" and pkgs.split() == listed()
    assert not env.calls.exists()


@pytestmark_sh
def test_online_installs_only_what_is_missing_with_a_full_sync(env):
    env.installed.write_text("kate\nark\n", encoding="utf-8")
    assert run_install(env).returncode == 0
    assert status(env) == ("done", "")
    call = env.calls.read_text(encoding="utf-8").split()
    assert call[:4] == ["-Syu", "--noconfirm", "--needed", "okular"]
    assert "kate" not in call and "ark" not in call
    assert set(call[3:]) == set(listed()) - {"kate", "ark"}


@pytestmark_sh
def test_failure_is_reported_and_retried_later(env):
    (env.tmp / "pacman-fails").write_text("", encoding="utf-8")
    assert run_install(env).returncode == 1
    state, pkgs = status(env)
    assert state == "failed" and pkgs.split() == listed()


@pytestmark_sh
def test_pacman_lock_leaves_it_pending(env):
    (env.tmp / "db.lck").write_text("", encoding="utf-8")
    assert run_install(env).returncode == 0
    assert status(env)[0] == "pending" and not env.calls.exists()


def run_notify(ctx, state, pkgs="kate ark", lang="es_ES.UTF-8"):
    ctx.state.parent.mkdir(parents=True, exist_ok=True)
    ctx.state.write_text(f"{state}\n{pkgs}\n", encoding="utf-8")
    e = dict(ctx.env, DEFERRED_STATUS=str(ctx.state), XDG_RUNTIME_DIR=str(ctx.tmp), LANG=lang)
    subprocess.run([SH, str(NOTIFY)], env=e, check=True)


@pytest.fixture
def notes(env):
    out = env.tmp / "notes"
    stub(env.bin / "notify-send", f'printf "%s|%s\\n" "$(printf "%s" "$@" | tail -c 0)" "$*" >> "{out}"\n')
    return out


def sent(notes):
    return notes.read_text(encoding="utf-8").splitlines() if notes.exists() else []


@pytestmark_sh
def test_notifications_follow_the_state_changes_once(env, notes):
    run_notify(env, "pending")
    run_notify(env, "pending")                  # el mismo estado: no se repite
    run_notify(env, "running")
    run_notify(env, "done")
    messages = sent(notes)
    assert len(messages) == 3
    assert "kate ark" in messages[0] and "primera vez" in messages[0]
    assert "Instalando" in messages[1] and "Aplicaciones instaladas" in messages[2]


@pytestmark_sh
def test_done_at_login_is_silent_and_failed_is_reported(env, notes):
    run_notify(env, "done")
    assert sent(notes) == []
    run_notify(env, "failed")
    assert len(sent(notes)) == 1 and "volverá a intentar" in sent(notes)[0]


@pytestmark_sh
def test_notification_language(env, notes):
    run_notify(env, "pending", lang="ca_ES.UTF-8")
    assert "primera vegada" in sent(notes)[0]
    (env.tmp / "arctiva-deferred.last").unlink()
    run_notify(env, "pending", lang="en_US.UTF-8")
    assert "first time you connect" in sent(notes)[1]
