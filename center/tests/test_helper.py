# SPDX-License-Identifier: GPL-3.0-or-later
"""El ayudante con pacman, systemctl e install-drivers falsos bajo ARCTIVA_HELPER_TEST_ROOT."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from arctiva_center.core import helper_client

HELPER = Path(__file__).resolve().parents[1] / "helper" / "arctiva-helper"

pytestmark = pytest.mark.skipif(
    os.name != "posix" or os.geteuid() == 0,
    reason="necesita un sistema POSIX y un usuario sin privilegios (el modo de prueba se ignora con root)",
)

CATALOG = """
version = 1

[[extra]]
id = "office"
packages = ["libreoffice-fresh", "thunderbird"]
services = ["cups.service"]

[[extra]]
id = "games"
packages = ["steam", "ttf-liberation"]

[[extra]]
id = "lts"
packages = ["linux-lts"]
remove_also = ["nvidia-open-lts"]
update_grub = true
with_drivers = true

[[extra]]
id = "evil"
packages = ["--overwrite=*"]

[[extra]]
id = "evil-unit"
packages = ["ufw"]
services = ["-H root@host"]
"""

FAKE = """#!/bin/sh
if [ "$1" = "-Qq" ]; then cat "$ARCTIVA_FAKE_INSTALLED"; exit 0; fi
echo "$(basename "$0") $*" >>"$ARCTIVA_FAKE_LOG"
echo "LC_ALL=$LC_ALL LANGUAGE=$LANGUAGE" >>"$ARCTIVA_FAKE_LOG.env"
echo "salida de $(basename "$0")"
exit "${ARCTIVA_FAKE_RC:-0}"
"""


@pytest.fixture
def root(tmp_path):
    r = tmp_path / "root"
    for d in ("usr/bin", "usr/share/arctiva-center", "var/lib/pacman", "etc/sub", "usr/lib/arctiva"):
        (r / d).mkdir(parents=True)
    (r / "usr/share/arctiva-center/extras.toml").write_text(CATALOG, encoding="utf-8")
    (r / "installed").write_text("")
    for name in ("pacman", "systemctl", "grub-mkconfig"):
        f = r / "usr/bin" / name
        f.write_text(FAKE)
        f.chmod(0o755)
    return r


def helper(root, *args, rc=0):
    log = root.parent / "calls.log"
    env = dict(os.environ, ARCTIVA_HELPER_TEST_ROOT=str(root), ARCTIVA_FAKE_LOG=str(log),
               ARCTIVA_FAKE_RC=str(rc), LANGUAGE="es", LC_ALL="es_ES.UTF-8",
               ARCTIVA_FAKE_INSTALLED=str(root / "installed"))
    p = subprocess.run([sys.executable, "-I", str(HELPER), *args], env=env,
                       capture_output=True, text=True)
    calls = log.read_text().splitlines() if log.exists() else []
    return p.returncode, calls, p.stdout + p.stderr


def test_no_root_without_test_mode():
    env = {k: v for k, v in os.environ.items() if k != "ARCTIVA_HELPER_TEST_ROOT"}
    p = subprocess.run([sys.executable, "-I", str(HELPER), "update"], env=env, capture_output=True)
    assert p.returncode == 77


@pytest.mark.parametrize("args", [
    [], ["rm"], ["update", "--force"], ["update", "--keyring-first", "x"], ["UPDATE"],
    ["drivers-apply", "x"], ["extra-install"], ["extra-install", "office", "lts"],
    ["sh", "-c", "id"], ["update;id"],
])
def test_unknown_or_malformed_runs_nothing(root, args):
    rc, calls, _ = helper(root, *args)
    assert rc == 64
    assert calls == []


def test_update(root):
    rc, calls, out = helper(root, "update")
    assert rc == 0
    assert calls == ["pacman -Syu --noconfirm"]
    assert "salida de pacman" in out


def test_pacman_messages_in_english(root):
    helper(root, "update")
    env_log = root.parent / "calls.log.env"
    assert env_log.read_text().splitlines() == ["LC_ALL=C.UTF-8 LANGUAGE="]


def test_update_returns_pacman_code(root):
    rc, _, _ = helper(root, "update", rc=1)
    assert rc == 1


def test_update_keyring_first(root):
    rc, calls, _ = helper(root, "update", "--keyring-first")
    assert rc == 0
    assert calls == ["pacman -Sy --needed --noconfirm archlinux-keyring", "pacman -Su --noconfirm"]


def test_keyring_failure_stops(root):
    rc, calls, _ = helper(root, "update", "--keyring-first", rc=1)
    assert rc == 1
    assert calls == ["pacman -Sy --needed --noconfirm archlinux-keyring"]


@pytest.mark.parametrize("op", [["update"], ["extra-install", "office"], ["drivers-apply"]])
def test_locked_database(root, op):
    (root / "var/lib/pacman/db.lck").touch()
    rc, calls, _ = helper(root, *op)
    assert rc == 75
    assert calls == []
    assert (root / "var/lib/pacman/db.lck").exists()


def test_extra_install(root):
    rc, calls, _ = helper(root, "extra-install", "office")
    assert rc == 0
    assert calls == [
        "pacman -Syu --needed --noconfirm -- libreoffice-fresh thunderbird",
        "systemctl enable --now -- cups.service",
    ]


def test_extra_install_failure_skips_services(root):
    rc, calls, _ = helper(root, "extra-install", "office", rc=1)
    assert rc == 1
    assert calls == ["pacman -Syu --needed --noconfirm -- libreoffice-fresh thunderbird"]


def test_extra_with_drivers_unavailable(root):
    rc, calls, _ = helper(root, "extra-install", "lts")
    assert rc == 69
    assert calls == ["pacman -Syu --needed --noconfirm -- linux-lts"]


def test_extra_with_drivers_and_grub(root):
    drivers = root / "usr/lib/arctiva/install-drivers"
    drivers.write_text(FAKE)
    drivers.chmod(0o755)
    real = os.path.realpath(root)
    # Sin grub.cfg (por ejemplo, otro cargador de arranque) no se regenera el menú.
    rc, calls, _ = helper(root, "extra-install", "lts")
    assert rc == 0
    assert calls[-1] == f"install-drivers --upgrade {real}"
    (root / "boot/grub").mkdir(parents=True)
    (root / "boot/grub/grub.cfg").write_text("")
    (root.parent / "calls.log").unlink()
    rc, calls, _ = helper(root, "extra-install", "lts")
    assert calls[-2:] == [f"install-drivers --upgrade {real}",
                          f"grub-mkconfig -o {real}/boot/grub/grub.cfg"]


def test_extra_remove_lts_with_nvidia(root):
    (root / "boot/grub").mkdir(parents=True)
    (root / "boot/grub/grub.cfg").write_text("")
    (root / "installed").write_text("linux\nlinux-lts\nnvidia-open-lts\n")
    rc, calls, _ = helper(root, "extra-remove", "lts")
    real = os.path.realpath(root)
    assert rc == 0
    assert calls == ["pacman -Rs --print -- linux-lts nvidia-open-lts",
                     "pacman -Rns --noconfirm -- linux-lts nvidia-open-lts",
                     f"grub-mkconfig -o {real}/boot/grub/grub.cfg"]


def test_extra_remove_keeps_shared_packages(root):
    # ttf-liberation es también de «games», que está instalado entero: se queda.
    (root / "installed").write_text("libreoffice-fresh\nthunderbird\nsteam\nttf-liberation\n")
    (root / "usr/share/arctiva-center/extras.toml").write_text(CATALOG.replace(
        'packages = ["libreoffice-fresh", "thunderbird"]',
        'packages = ["libreoffice-fresh", "thunderbird", "ttf-liberation"]'), encoding="utf-8")
    rc, calls, _ = helper(root, "extra-remove", "office")
    assert rc == 0
    assert calls[0] == "pacman -Rs --print -- libreoffice-fresh thunderbird"


def test_extra_remove_nothing_installed(root):
    rc, calls, out = helper(root, "extra-remove", "office")
    assert rc == 0 and calls == [] and "nada que quitar" in out


def test_extra_remove(root):
    (root / "installed").write_text("libreoffice-fresh\nthunderbird\n")
    rc, calls, _ = helper(root, "extra-remove", "office")
    assert rc == 0
    assert calls == [
        "pacman -Rs --print -- libreoffice-fresh thunderbird",
        "systemctl disable --now -- cups.service",
        "pacman -Rns --noconfirm -- libreoffice-fresh thunderbird",
    ]


def test_extra_remove_blocked_keeps_services(root):
    (root / "installed").write_text("libreoffice-fresh\nthunderbird\n")
    rc, calls, _ = helper(root, "extra-remove", "office", rc=1)
    assert rc == 1
    assert calls == ["pacman -Rs --print -- libreoffice-fresh thunderbird"]


@pytest.mark.parametrize("extra_id", [
    "nope", "Office", "../office", "office ", "-office", "a" * 41, "", "evil", "evil-unit",
])
def test_invalid_or_unknown_ids(root, extra_id):
    rc, calls, _ = helper(root, "extra-install", extra_id)
    assert rc == 64
    assert calls == []


def make_pacnew(root, rel="etc/sub/app.conf"):
    original = root / rel
    original.write_text("viejo")
    pacnew = root / (rel + ".pacnew")
    pacnew.write_text("nuevo")
    return original, pacnew


def test_pacnew_keep(root):
    original, pacnew = make_pacnew(root)
    rc, calls, _ = helper(root, "pacnew-keep", str(pacnew))
    assert rc == 0 and calls == []
    assert not pacnew.exists() and original.read_text() == "viejo"


def test_pacnew_use(root):
    original, pacnew = make_pacnew(root)
    rc, _, _ = helper(root, "pacnew-use", str(pacnew))
    assert rc == 0
    assert original.read_text() == "nuevo"
    assert not pacnew.exists()
    assert Path(str(original) + ".pacsave").read_text() == "viejo"


def test_pacnew_use_replaces_old_pacsave(root):
    original, pacnew = make_pacnew(root)
    Path(str(original) + ".pacsave").write_text("muy viejo")
    rc, _, _ = helper(root, "pacnew-use", str(pacnew))
    assert rc == 0
    assert Path(str(original) + ".pacsave").read_text() == "viejo"


def test_pacnew_traps(root, tmp_path):
    original, pacnew = make_pacnew(root)
    outside = tmp_path / "fuera"
    outside.mkdir()
    (outside / "x.conf").write_text("a")
    (outside / "x.conf.pacnew").write_text("b")
    # Enlace a un .pacnew de fuera de /etc.
    (root / "etc/link.conf").write_text("a")
    (root / "etc/link.conf.pacnew").symlink_to(outside / "x.conf.pacnew")
    # Directorio enlazado dentro de /etc que apunta fuera.
    (root / "etc/dirlink").symlink_to(outside, target_is_directory=True)
    # Original que es un enlace.
    (root / "etc/orig-link.conf").symlink_to(outside / "x.conf")
    (root / "etc/orig-link.conf.pacnew").write_text("b")
    # Sin original y un directorio con nombre .pacnew.
    (root / "etc/huerfano.conf.pacnew").write_text("b")
    (root / "etc/dir.conf").write_text("a")
    (root / "etc/dir.conf.pacnew").mkdir()
    traps = [
        str(outside / "x.conf.pacnew"),
        # Como texto: pathlib normalizaría «//».
        f"{root}/etc/sub/../sub/app.conf.pacnew",
        f"{root}/etc/sub//app.conf.pacnew",
        f"{root}/etc/./sub/app.conf.pacnew",
        str(root / "etc/link.conf.pacnew"),
        str(root / "etc/dirlink/x.conf.pacnew"),
        str(root / "etc/orig-link.conf.pacnew"),
        str(root / "etc/huerfano.conf.pacnew"),
        str(root / "etc/dir.conf.pacnew"),
        str(root / "etc/sub/app.conf"),
        "etc/sub/app.conf.pacnew",
        str(root / "etc/sub/no-existe.conf.pacnew"),
    ]
    for op in ("pacnew-keep", "pacnew-use"):
        for path in traps:
            rc, calls, out = helper(root, op, path)
            assert rc == 64, (op, path, out)
    assert pacnew.read_text() == "nuevo" and original.read_text() == "viejo"
    assert (outside / "x.conf.pacnew").read_text() == "b"
    assert (outside / "x.conf").read_text() == "a"


def test_client_and_helper_agree_on_operations():
    text = HELPER.read_text(encoding="utf-8")
    for op in helper_client._ARGS:
        assert f'"{op}": op_' in text
