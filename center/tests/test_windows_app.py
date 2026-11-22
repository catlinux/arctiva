# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from arctiva_center.__main__ import build_parser
from arctiva_center.core import windows_app as wa


def test_check_file(tmp_path):
    exe = tmp_path / "Setup.EXE"
    exe.write_bytes(b"MZ")
    assert wa.check_file(str(exe)) == str(exe.resolve())
    (tmp_path / "a.msi").write_bytes(b"x")
    assert wa.check_file(str(tmp_path / "a.msi"))
    for bad in (None, "", "no-existe.exe", str(tmp_path), str(tmp_path / "doc.txt"), "x\0.exe", "a\nb.exe"):
        assert wa.check_file(bad) is None
    (tmp_path / "carpeta.exe").mkdir()
    assert wa.check_file(str(tmp_path / "carpeta.exe")) is None


def test_bottles_argv(tmp_path):
    exe = tmp_path / "7z.exe"
    exe.write_bytes(b"MZ")
    assert wa.bottles_argv(str(exe)) == ["flatpak", "run", "com.usebottles.bottles", "-e", str(exe.resolve())]
    lnk = tmp_path / "atajo.lnk"
    lnk.write_bytes(b"L")
    assert wa.bottles_argv(str(lnk))[3] == "--lnk"
    with pytest.raises(ValueError):
        wa.bottles_argv(str(tmp_path / "x.sh"))
    # Un nombre que parece una opción no llega como opción: va como ruta absoluta.
    odd = tmp_path / "-e.exe"
    odd.write_bytes(b"MZ")
    assert wa.bottles_argv(str(odd))[-1].startswith(str(tmp_path.resolve()))


def test_bottles_installed_and_name():
    assert wa.bottles_installed({"com.usebottles.bottles"}) and not wa.bottles_installed(set())
    assert wa.display_name("/a/b/Setup\x07.exe") == "Setup.exe"


def test_links_are_https():
    assert wa.LINKS and all(u.startswith("https://") for _, u in wa.LINKS)


def test_parser_windows_app():
    args = build_parser().parse_args(["--windows-app", "/tmp/x.exe"])
    assert args.windows_app == "/tmp/x.exe"
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--windows-app", "x.exe", "--check"])
