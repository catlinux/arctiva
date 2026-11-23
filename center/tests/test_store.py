# SPDX-License-Identifier: GPL-3.0-or-later
import os
import time
from types import SimpleNamespace as NS

import pytest

from arctiva_center.core import appstream as ap
from arctiva_center.core import store


def make_app(kinds=("arch", "flathub"), recommended="arch"):
    app = ap.App("org.x.app", "App X", "Resumen", "Descripción", ("Graphics",), (), "GPL-3.0-only",
                 "https://x.org", ("https://x.org/s.png",))
    refs = {"arch": "app-x", "flathub": "org.x.App"}
    app.sources = [ap.Source(k, refs[k], "/ic/app.png" if k == "arch" else "") for k in kinds]
    app.recommended = recommended
    return app


def test_flatpak_argv():
    assert store.flatpak_install_argv("org.kde.kcalc") == [
        "flatpak", "install", "--system", "--noninteractive", "flathub", "org.kde.kcalc"]
    assert store.flatpak_uninstall_argv("org.kde.kcalc")[-1] == "org.kde.kcalc"
    for bad in ("", "-x", "a b", "a;id", "../x", "$(id)", "x" * 300):
        with pytest.raises(ValueError):
            store.flatpak_install_argv(bad)
        with pytest.raises(ValueError):
            store.flatpak_uninstall_argv(bad)


def test_parse_flatpak_list():
    assert store.parse_flatpak_list("org.kde.kcalc\ncom.usebottles.bottles\n\n  \nBasura con espacios\n") == {
        "org.kde.kcalc", "com.usebottles.bottles"}


def test_appstream_stale(tmp_path):
    f = tmp_path / "appstream.xml.gz"
    assert store.appstream_stale(f)                       # no existe
    f.write_bytes(b"x")
    assert not store.appstream_stale(f)
    old = time.time() - 8 * 86400
    os.utime(f, (old, old))
    assert store.appstream_stale(f)
    assert not store.appstream_stale(f, now=old + 3600)


def test_human_size():
    assert store.human_size(0) == "" and store.human_size(None) == "" and store.human_size(-1) == ""
    assert store.human_size(512) == "512 B"
    assert store.human_size(2048) == "2.0 KiB"
    assert store.human_size(73797100) == "70.4 MiB"


def test_icon_source():
    assert store.icon_source("") == "package-x-generic"
    assert store.icon_source("accessories-text-editor") == "accessories-text-editor"
    assert store.icon_source("/usr/share/x.png") == "file:///usr/share/x.png"


def test_source_rows():
    app = make_app()
    info = {"app-x": NS(version="1.2-1", download_size=5 * 1024 * 1024)}
    rows = store.source_rows(app, {"app-x"}, set(), info)
    assert [r["label"] for r in rows] == ["Arch", "Flathub"]
    arch, flathub = rows
    assert arch["installed"] and arch["recommended"] and arch["version"] == "1.2-1" and arch["size"] == "5.0 MiB"
    assert not flathub["installed"] and not flathub["recommended"]
    rows = store.source_rows(app, set(), {"org.x.App"})
    assert [r["installed"] for r in rows] == [False, True]


def test_summary_and_detail():
    app = make_app()
    card = store.app_summary(app, set(), {"org.x.App"})
    assert card["installed"] and card["sources"] == ["Arch", "Flathub"] and card["icon"] == "file:///ic/app.png"
    detail = store.app_detail(app, set(), set())
    assert detail["description"] == "Descripción" and detail["screenshots"] == ["https://x.org/s.png"]
    assert len(detail["rows"]) == 2 and not detail["installed"]
    only_flathub = make_app(("flathub",), "flathub")
    assert store.app_summary(only_flathub, set(), set())["icon"] == "package-x-generic"


def test_checkupdates_code():
    assert store.checkupdates_pending(0) is True
    assert store.checkupdates_pending(2) is False
    assert store.checkupdates_pending(1) is None
    assert store.checkupdates_pending(-1) is None


def test_preferred_kind_for_bulk_installs():
    assert store.preferred_kind(make_app()) == "arch"
    assert store.preferred_kind(make_app(recommended="flathub")) == "flathub"
    assert store.preferred_kind(make_app(("flathub",), "arch")) == "flathub"     # la recomendada no existe
    assert store.preferred_kind(make_app(())) == ""
    assert store.app_summary(make_app(("flathub",), "flathub"), set(), set())["kind"] == "flathub"
