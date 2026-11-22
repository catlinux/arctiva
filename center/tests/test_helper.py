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
if [ "$1" = "-Qqe" ]; then cat "$ARCTIVA_FAKE_INSTALLED.explicit"; exit 0; fi
if [ "$1" = "-Rs" ]; then cat "$ARCTIVA_FAKE_INSTALLED.print" 2>/dev/null; fi
echo "$(basename "$0") $*" >>"$ARCTIVA_FAKE_LOG"
echo "LC_ALL=$LC_ALL LANGUAGE=$LANGUAGE" >>"$ARCTIVA_FAKE_LOG.env"
echo "salida de $(basename "$0")"
exit "${ARCTIVA_FAKE_RC:-0}"
"""

FAKE_CHECKUPDATES = """#!/bin/sh
echo "checkupdates CHECKUPDATES_DB=$CHECKUPDATES_DB" >>"$ARCTIVA_FAKE_LOG"
exit "${ARCTIVA_FAKE_CHECK_RC:-2}"
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
    (r / "usr/bin/checkupdates").write_text(FAKE_CHECKUPDATES)
    (r / "usr/bin/checkupdates").chmod(0o755)
    (r / "installed.explicit").write_text("")
    (r / "usr/share/arctiva-center/protected.toml").write_text(PROTECTED)
    return r


PROTECTED = """
version = 1
patterns = ["base", "linux", "linux-*", "plasma-*", "arctiva-*", "glibc"]
"""


def helper(root, *args, rc=0, check_rc=2, uid=None):
    log = root.parent / "calls.log"
    env = dict(os.environ, ARCTIVA_HELPER_TEST_ROOT=str(root), ARCTIVA_FAKE_LOG=str(log),
               ARCTIVA_FAKE_RC=str(rc), LANGUAGE="es", LC_ALL="es_ES.UTF-8",
               ARCTIVA_FAKE_INSTALLED=str(root / "installed"), ARCTIVA_FAKE_CHECK_RC=str(check_rc))
    if uid is not None:
        env["PKEXEC_UID"] = str(uid)
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


# --- operaciones de la tienda (fase 6) ---

BAD_NAMES = ["-x", "--overwrite=*", "../x", "a b", "A", "x" * 101, "", "a;id", "$(id)", "-Syu"]


@pytest.mark.parametrize("op", ["app-install", "app-remove", "aur-deps"])
@pytest.mark.parametrize("bad", BAD_NAMES)
def test_store_ops_reject_bad_names(root, op, bad):
    rc, calls, _ = helper(root, op, "krita", bad)
    assert rc == 64 and calls == []


@pytest.mark.parametrize("op", ["app-install", "app-remove", "aur-deps"])
def test_store_ops_reject_count(root, op):
    assert helper(root, op)[0] == 64
    names = [f"pkg{i}" for i in range(21)]
    rc, calls, _ = helper(root, op, *names)
    assert rc == 64 and calls == []


def test_app_install(root):
    rc, calls, _ = helper(root, "app-install", "krita", "gimp", "krita")
    assert rc == 0
    assert calls == ["pacman -Syu --needed --noconfirm -- krita gimp"]


def test_app_install_locked(root):
    (root / "var/lib/pacman/db.lck").write_text("")
    rc, calls, _ = helper(root, "app-install", "krita")
    assert rc == 75 and calls == []


def test_app_remove(root):
    (root / "installed.explicit").write_text("gimp\nkrita\n")
    (root / "installed.print").write_text("gimp\ngegl\n")
    rc, calls, _ = helper(root, "app-remove", "gimp")
    assert rc == 0
    assert calls == ["pacman -Rs --print --print-format %n -- gimp", "pacman -Rns --noconfirm -- gimp"]


@pytest.mark.parametrize("name", ["base", "linux", "linux-lts", "plasma-desktop", "arctiva-center", "glibc"])
def test_app_remove_protected_runs_nothing(root, name):
    (root / "installed.explicit").write_text(name + "\n")
    rc, calls, out = helper(root, "app-remove", name)
    assert rc == 64 and calls == [] and "protegidos" in out


def test_app_remove_not_explicit(root):
    (root / "installed.explicit").write_text("krita\n")
    rc, calls, out = helper(root, "app-remove", "gimp")
    assert rc == 64 and calls == [] and "explícita" in out


def test_app_remove_would_drag_protected(root):
    (root / "installed.explicit").write_text("gimp\n")
    (root / "installed.print").write_text("gimp\nplasma-nm\n")
    rc, calls, out = helper(root, "app-remove", "gimp")
    assert rc == 64 and "arrastraría" in out
    assert calls == ["pacman -Rs --print --print-format %n -- gimp"]   # solo la simulación


def test_app_remove_pacman_refuses(root):
    (root / "installed.explicit").write_text("gimp\n")
    rc, calls, _ = helper(root, "app-remove", "gimp", rc=1)
    assert rc == 1 and calls == ["pacman -Rs --print --print-format %n -- gimp"]


def test_app_remove_unreadable_protected_list(root):
    (root / "usr/share/arctiva-center/protected.toml").unlink()
    (root / "installed.explicit").write_text("gimp\n")
    rc, calls, _ = helper(root, "app-remove", "gimp")
    assert rc == 70 and calls == []


def test_aur_prepare(root):
    rc, calls, _ = helper(root, "aur-prepare")
    assert rc == 0 and calls == ["pacman -Syu --needed --noconfirm -- base-devel git"]
    assert helper(root, "aur-prepare", "x")[0] == 64


def test_aur_deps_with_pending_updates(root):
    rc, calls, out = helper(root, "aur-deps", "libfoo", check_rc=0)
    assert rc == 65 and "actualizaciones pendientes" in out
    assert len(calls) == 1 and calls[0].startswith("checkupdates CHECKUPDATES_DB=")
    assert "/var/cache/arctiva-center/checkupdates" in calls[0]


def test_aur_deps_up_to_date(root):
    rc, calls, _ = helper(root, "aur-deps", "libfoo", check_rc=2)
    assert rc == 0 and calls[-1] == "pacman -S --needed --asdeps --noconfirm -- libfoo"


def test_aur_deps_check_failure_stops(root):
    rc, calls, _ = helper(root, "aur-deps", "libfoo", check_rc=1)
    assert rc == 75 and not any(c.startswith("pacman") for c in calls)


@pytest.fixture
def build(root):
    d = root / "home/user/.cache/arctiva-center/aur/build/yay"
    d.mkdir(parents=True)
    return d


def test_aur_install_copies_and_cleans(root, build):
    pkg = build / "yay-1-1-x86_64.pkg.tar.zst"
    pkg.write_bytes(b"contenido")
    rc, calls, _ = helper(root, "aur-install", str(pkg), uid=os.getuid())
    assert rc == 0
    assert len(calls) == 1 and calls[0].startswith("pacman -U --needed --noconfirm -- ")
    copy = calls[0].split("-- ")[1]
    assert "/var/tmp/arctiva-aur-" in copy and copy.endswith("yay-1-1-x86_64.pkg.tar.zst")
    assert not os.path.exists(copy)                      # la copia temporal se borra
    assert pkg.read_bytes() == b"contenido"


def test_aur_install_needs_caller(root, build):
    pkg = build / "a-1-1-any.pkg.tar.zst"
    pkg.write_bytes(b"x")
    for env_uid in (None, "x"):
        rc, calls, _ = helper(root, "aur-install", str(pkg), uid=env_uid)
        assert rc == 64 and calls == []


def test_aur_install_rejects_outside_build_dir(root, build, tmp_path):
    other = root / "home/user/otra"
    other.mkdir(parents=True)
    pkg = other / "a-1-1-any.pkg.tar.zst"
    pkg.write_bytes(b"x")
    assert helper(root, "aur-install", str(pkg), uid=os.getuid())[0] == 64
    outside = tmp_path / "b-1-1-any.pkg.tar.zst"
    outside.write_bytes(b"x")
    rc, calls, _ = helper(root, "aur-install", str(outside), uid=os.getuid())
    assert rc == 64 and calls == []


@pytest.mark.parametrize("name", ["a.tar.zst", "a.pkg.tar.xz", "-a.pkg.tar.zst", "a b.pkg.tar.zst"])
def test_aur_install_rejects_bad_names(root, build, name):
    pkg = build / name
    pkg.write_bytes(b"x")
    rc, calls, _ = helper(root, "aur-install", str(pkg), uid=os.getuid())
    assert rc == 64 and calls == []


def test_aur_install_rejects_symlink(root, build, tmp_path):
    target = tmp_path / "real.pkg.tar.zst"
    target.write_bytes(b"x")
    link = build / "link-1-1-any.pkg.tar.zst"
    link.symlink_to(target)
    rc, calls, _ = helper(root, "aur-install", str(link), uid=os.getuid())
    assert rc == 64 and calls == []


def test_aur_install_rejects_symlinked_build_dir(root, tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    (real / "a-1-1-any.pkg.tar.zst").write_bytes(b"x")
    base = root / "home/user/.cache/arctiva-center/aur"
    base.mkdir(parents=True)
    (base / "build").symlink_to(real)
    rc, calls, _ = helper(root, "aur-install", str(base / "build/a-1-1-any.pkg.tar.zst"), uid=os.getuid())
    assert rc == 64 and calls == []


def test_aur_install_rejects_other_owner(root, build):
    pkg = build / "a-1-1-any.pkg.tar.zst"
    pkg.write_bytes(b"x")
    rc, calls, _ = helper(root, "aur-install", str(pkg), uid=os.getuid() + 1)
    assert rc == 64 and calls == []


def test_aur_install_rejects_directory_and_missing(root, build):
    (build / "d-1-1-any.pkg.tar.zst").mkdir()
    for name in ("d-1-1-any.pkg.tar.zst", "no-1-1-any.pkg.tar.zst"):
        rc, calls, _ = helper(root, "aur-install", str(build / name), uid=os.getuid())
        assert rc == 64 and calls == []


def test_aur_install_too_many_files(root, build):
    files = []
    for i in range(41):
        f = build / f"p{i}-1-1-any.pkg.tar.zst"
        f.write_bytes(b"x")
        files.append(str(f))
    rc, calls, _ = helper(root, "aur-install", *files, uid=os.getuid())
    assert rc == 64 and calls == []


def test_client_store_arguments():
    from arctiva_center.core.helper_client import build_argv
    assert build_argv("app-install", ["krita"])[-2:] == ["app-install", "krita"]
    assert build_argv("aur-prepare")[-1] == "aur-prepare"
    assert build_argv("aur-install", ["/home/u/.cache/x/a-1-any.pkg.tar.zst"])
    for op, args in (("app-install", []), ("app-remove", ["-x"]), ("aur-deps", ["A"]),
                     ("aur-prepare", ["x"]), ("aur-install", ["relativo.pkg.tar.zst"]),
                     ("aur-install", ["/a/b.tar.zst"]), ("app-install", ["x"] * 21)):
        with pytest.raises(ValueError):
            build_argv(op, args)


def test_aur_deps_refuses_untrusted_check_dir(root, tmp_path):
    cache = root / "var/cache/arctiva-center"
    cache.mkdir(parents=True)
    (cache / "checkupdates").symlink_to(tmp_path)            # enlace plantado por otro
    rc, calls, out = helper(root, "aur-deps", "libfoo", check_rc=2)
    assert rc == 75 and "no es de confianza" in out
    assert not any(c.startswith("pacman") or c.startswith("checkupdates") for c in calls)
