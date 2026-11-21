# SPDX-License-Identifier: GPL-3.0-or-later
import pytest

from arctiva_center.core import helper_client as hc


def test_build_argv():
    assert hc.build_argv("update") == [hc.PKEXEC, hc.HELPER, "update"]
    assert hc.build_argv("update", ["--keyring-first"])[-1] == "--keyring-first"
    assert hc.build_argv("extra-install", ["lts"])[-2:] == ["extra-install", "lts"]
    assert hc.build_argv("pacnew-use", ["/etc/a.conf.pacnew"])[-1] == "/etc/a.conf.pacnew"


@pytest.mark.parametrize("op,args", [
    ("rm", []), ("update", ["--force"]), ("extra-install", []), ("extra-install", ["A"]),
    ("extra-install", ["a b"]), ("drivers-apply", ["x"]), ("pacnew-keep", ["/tmp/x.pacnew"]),
    ("pacnew-keep", ["/etc/x.conf"]), ("update", [1]),
])
def test_build_argv_rejects(op, args):
    with pytest.raises(ValueError):
        hc.build_argv(op, args)


def test_line_splitter():
    s = hc.LineSplitter()
    assert s.feed("uno\ndo") == ["uno"]
    assert s.feed("s\r\ntres 10%\rtres 100%\n") == ["dos", "tres 10%", "tres 100%"]
    assert s.feed("cola") == []
    assert s.flush() == ["cola"]
    assert s.flush() == []
