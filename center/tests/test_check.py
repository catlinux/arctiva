# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center import check
from arctiva_center.core.updates import Update


def test_only_new_updates_notify():
    current = [Update("linux", "1", "2"), Update("mesa", "1", "3")]
    assert check.new_since_last_notice(current, []) == ["linux 2", "mesa 3"]
    assert check.new_since_last_notice(current, ["linux 2", "mesa 3"]) == []
    # Una versión más nueva del mismo paquete vuelve a avisar.
    assert check.new_since_last_notice([Update("mesa", "1", "4")], ["mesa 3"]) == ["mesa 4"]


def test_texts_follow_language():
    assert check.texts({"LANGUAGE": "ca:es", "LANG": "es_ES.UTF-8"}) == check.TEXTS["ca"]
    assert check.texts({"LANG": "es_ES.UTF-8"}) == check.TEXTS["es"]
    assert check.texts({"LANG": "de_DE.UTF-8"}) == check.TEXTS["en"]
    assert check.texts({}) == check.TEXTS["en"]
    for title, body, action in check.TEXTS.values():
        assert "{n}" in body and title and action


class Out:
    def __init__(self, code, stdout=""):
        self.returncode, self.stdout = code, stdout


def fake_run(results):
    def run(argv, timeout):
        return results.get(argv[0])
    return run


def test_pending_joins_the_sources_the_settings_allow(tmp_path):
    cfg = tmp_path / "settings.toml"
    run = fake_run({"checkupdates": Out(0, "linux 1 -> 2\n"), "flatpak": Out(0, "org.a.B\tB\t3\n")})
    aur_up = lambda: [Update("yay", "1", "2")]
    names = lambda found: [u.name for u in found]
    assert names(check.pending(run, cfg, aur_up)) == ["linux", "B"]          # AUR desactivado
    cfg.write_text("aur_enabled = true\n", encoding="utf-8")
    assert names(check.pending(run, cfg, aur_up)) == ["linux", "B", "yay"]
    cfg.write_text("aur_enabled = true\nupdate_aur = false\nupdate_flatpak = false\n", encoding="utf-8")
    assert names(check.pending(run, cfg, aur_up)) == ["linux"]


def test_a_failing_source_does_not_hide_the_others(tmp_path):
    run = fake_run({"checkupdates": Out(1), "flatpak": Out(0, "org.a.B\tB\t3\n")})
    assert [u.name for u in check.pending(run, tmp_path / "none.toml")] == ["B"]
    run = fake_run({"checkupdates": Out(2), "flatpak": None})
    assert check.pending(run, tmp_path / "none.toml") == []
