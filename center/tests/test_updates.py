# SPDX-License-Identifier: GPL-3.0-or-later
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from arctiva_center.core import errors, pacnew, paths, updates

FIX = Path(__file__).resolve().parent / "fixtures"
CET = timezone(timedelta(hours=1))


def news():
    return updates.parse_news((FIX / "news.xml").read_text(encoding="utf-8"))


def test_parse_checkupdates():
    text = "linux 6.17.1.arch1-1 -> 6.17.2.arch1-1\nffmpeg 2:9.0.2-5 -> 2:9.1-1\n\nbasura\n"
    assert updates.parse_checkupdates(text) == [
        updates.Update("linux", "6.17.1.arch1-1", "6.17.2.arch1-1"),
        updates.Update("ffmpeg", "2:9.0.2-5", "2:9.1-1"),
    ]


def test_last_full_upgrade_ignores_failed_attempts():
    log = (FIX / "pacman.log").read_text(encoding="utf-8")
    assert updates.last_full_upgrade(log) == datetime(2026, 11, 1, 9, 0, 3, tzinfo=CET)
    assert updates.last_full_upgrade("") is None


def test_upgraded_packages():
    log = (FIX / "pacman.log").read_text(encoding="utf-8")
    since = datetime(2026, 11, 1, 9, 0, 0, tzinfo=CET)
    assert updates.upgraded_packages(log, since) == ["linux", "firefox"]
    assert updates.upgraded_packages(log, since + timedelta(days=1)) == []


def test_news():
    items = news()
    assert [n.title for n in items][:2] == [
        "foo >= 2.0 update requires manual intervention", "Bar now defaults to the new backend"]
    assert len(items) == 4  # la de fecha rota se descarta
    assert items[0].text.startswith("The foo package moved its configuration. Run")
    assert [n.manual for n in items] == [True, True, False, False]


def test_news_since_last_upgrade_and_blocking():
    shown = updates.news_since(news(), datetime(2026, 11, 5, tzinfo=timezone.utc))
    assert [n.link for n in shown] == ["https://archlinux.org/news/foo-20/",
                                       "https://archlinux.org/news/bar/"]
    assert updates.blocking_news(shown, {shown[1].guid}) == [shown[0]]
    assert updates.blocking_news(shown, {n.guid for n in shown}) == []


def test_news_without_upgrade_uses_30_days():
    now = datetime(2026, 11, 20, tzinfo=timezone.utc)
    assert len(updates.news_since(news(), None, now)) == 3


def test_read_news_state(tmp_path):
    state = updates.ReadNews(tmp_path / "state" / "news.json")
    assert state.load() == set()
    state.mark("a")
    assert state.mark("b") == {"a", "b"}
    assert updates.ReadNews(state.path).load() == {"a", "b"}
    state.path.write_text("no es json")
    assert state.load() == set()


def test_delicate_and_reboot():
    data = (paths.resolve().data / "delicate.toml").read_text(encoding="utf-8")
    patterns = tomllib.loads(data)["patterns"]
    ups = [updates.Update(n, "1", "2")
           for n in ("linux-lts", "nvidia-utils", "firefox", "mesa", "kwin")]
    assert [u.name for u in updates.delicate(ups, patterns)] == [
        "linux-lts", "nvidia-utils", "mesa", "kwin"]
    assert updates.needs_reboot(["firefox", "linux"])
    assert not updates.needs_reboot(["firefox", "kwin"])


@pytest.fixture(scope="module")
def catalog():
    return errors.ErrorCatalog.load(paths.resolve().data / "errors.toml")


@pytest.mark.parametrize("name,expected", [
    ("locked", ("locked", "retry")),
    ("no-space", ("no-space", "free-space")),
    ("pgp", ("pgp", "keyring-first")),
    ("pgp-key", ("pgp", "keyring-first")),
    ("conflicting-files", ("conflicting-files", "none")),
    ("dependencies", ("dependencies", "none")),
    ("network", ("network", "check-network")),
])
def test_errors(catalog, name, expected):
    text = (FIX / "pacman-errors" / f"{name}.txt").read_text(encoding="utf-8")
    e = catalog.explain(text, ["es_ES", "es"])
    assert (e.id, e.action) == expected
    assert e.message == catalog.explain(text, ["es"]).message
    assert catalog.explain(text, ["ca"]).message != e.message
    assert catalog.explain(text, ["de"]).message == catalog.explain(text, ["en"]).message


def test_errors_unknown(catalog):
    assert catalog.explain("todo bien") is None


def test_every_error_has_three_languages(catalog):
    for _, _, messages, _ in catalog.entries:
        assert set(messages) == {"en", "es", "ca"}


def test_bad_action_rejected():
    with pytest.raises(ValueError):
        errors.ErrorCatalog.parse({"error": [
            {"id": "x", "pattern": "x", "action": "rm", "message": {"en": "x"}}]})


def test_pacnew(tmp_path):
    out = "/etc/pacman.conf.pacnew\n/etc/mkinitcpio.conf.pacsave\n/home/x.pacnew\n"
    assert pacnew.parse_pacdiff(out) == ["/etc/pacman.conf.pacnew"]
    (tmp_path / "a.conf").write_text("uno\ndos\n")
    (tmp_path / "a.conf.pacnew").write_text("uno\ntres\n")
    diff = pacnew.unified_diff(tmp_path / "a.conf.pacnew")
    assert "-dos" in diff and "+tres" in diff
    (tmp_path / "b.conf.pacnew").write_bytes(b"\xff\xfe")
    (tmp_path / "b.conf").write_text("x")
    assert pacnew.unified_diff(tmp_path / "b.conf.pacnew") is None
    assert pacnew.unified_diff(tmp_path / "no.conf.pacnew") is None


def test_flatpak_updates():
    out = "org.mozilla.firefox\tFirefox\t140.0\ncom.valvesoftware.Steam\tSteam\t\norg.x.Sin\n\n"
    found = updates.parse_flatpak_updates(out)
    assert [(u.name, u.new) for u in found] == [("Firefox", "140.0"), ("Steam", ""), ("org.x.Sin", "")]
    assert updates.parse_flatpak_updates("") == []
