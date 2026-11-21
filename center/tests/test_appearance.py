# SPDX-License-Identifier: GPL-3.0-or-later
import json

import pytest

from arctiva_center.core import appearance as ap


def test_mode_light_and_dark():
    light = ap.mode_commands("light")
    assert ["plasma-apply-colorscheme", "ArctivaLight"] in light
    assert light[-1] == ["plasma-apply-colorscheme", "--accent-color", "#1d4ed8"]
    dark = ap.mode_commands("dark")
    assert ["plasma-apply-colorscheme", "BreezeDark"] in dark
    assert dark[-1] == ["plasma-apply-colorscheme", "--accent-color", "#3d86ff"]


def test_mode_keeps_custom_accent_only():
    assert ap.mode_commands("dark", "#16a34a")[-1][-1] == "#16a34a"
    # el acento por defecto del otro modo no se arrastra
    assert ap.mode_commands("light", "#3d86ff")[-1][-1] == "#1d4ed8"


def test_mode_auto_uses_both_look_and_feels():
    flat = [" ".join(c) for c in ap.mode_commands("auto")]
    assert any("AutomaticLookAndFeel true" in c for c in flat)
    assert any("DefaultDarkLookAndFeel org.arctiva.desktop.dark" in c for c in flat)


def test_mode_invalid():
    with pytest.raises(ValueError):
        ap.mode_commands("sepia")


def test_accent_validates_color():
    assert ap.accent_commands("#1d4ed8")[0][-1] == "#1d4ed8"
    for bad in ("red", "#12345", "1d4ed8; rm"):
        with pytest.raises(ValueError):
            ap.accent_commands(bad)


def test_alignment_scripts_toggle_left_spacer():
    centered = ap.alignment_commands(True)[0][-1]
    left = ap.alignment_commands(False)[0][-1]
    assert 'writeConfig("expanding", true)' in centered
    assert 'writeConfig("expanding", false)' in left
    assert ap.alignment_commands(True)[0][:4] == [
        "qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript"]


def test_floating_script():
    assert "panel.floating = true" in ap.floating_commands(True)[0][-1]
    assert "panel.floating = false" in ap.floating_commands(False)[0][-1]


def test_scale_font_keeps_family():
    assert ap.scale_font("Inter,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1", 12).startswith("Inter,12,")
    assert ap.scale_font("", 9).startswith("Noto Sans,9,")


def test_text_commands():
    cmds = ap.text_commands(1.3, {"font": "Inter,10,-1,5,400,0,0,0,0,0,0,0,0,0,0,1"})
    values = {c[6]: c[7] for c in cmds if c[0] == "kwriteconfig6"}
    assert values["font"].startswith("Inter,13,")
    assert values["smallestReadableFont"].startswith("Noto Sans,10,")  # 8 * 1.3 = 10,4
    assert cmds[-1][0] == "dbus-send"


KSCREEN = json.dumps({"outputs": [
    {"name": "eDP-1", "enabled": True, "scale": 1.5},
    {"name": "HDMI-A-1", "enabled": False, "scale": 1.0},
    {"name": "DP-2", "enabled": True, "scale": 1.0},
]})


def test_screen():
    assert ap.parse_outputs(KSCREEN) == ["eDP-1", "DP-2"]
    assert ap.parse_scale(KSCREEN) == 1.5
    assert ap.parse_outputs("no es json") == [] and ap.parse_scale("") == 1.0
    assert ap.screen_commands(1.25, ["eDP-1", "DP-2"]) == [
        ["kscreen-doctor", "output.eDP-1.scale.1.25", "output.DP-2.scale.1.25"]]
    assert ap.screen_commands(1.25, []) == []


def test_night_light():
    cmds = ap.night_light_commands(True)
    assert cmds[0][-1] == "true" and cmds[1] == ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"]


def test_restore_resets_layout_and_wallpaper():
    cmds = ap.restore_commands()
    assert ["lookandfeeltool", "-a", "org.arctiva.desktop", "--resetLayout"] in cmds
    assert ["plasma-apply-wallpaperimage", ap.WALLPAPER] in cmds
    assert cmds[-1] == ["plasma-apply-wallpaperimage", ap.WALLPAPER]


def test_apply_reports_failures():
    seen = []

    def runner(argv):
        seen.append(argv)
        return (1 if argv[0] == "b" else 0), ""

    assert ap.apply([["a"], ["c"]], runner)
    assert not ap.apply([["a"], ["b"], ["c"]], runner)
    assert seen[-1] == ["c"]  # sigue con las demás


def test_run_missing_program():
    assert ap.run(["arctiva-no-existe-xyz"]) == (-1, "")


def test_read_state():
    values = {
        ("kdeglobals", "General", "ColorScheme"): "BreezeDark",
        ("kdeglobals", "Colors:View", "DecorationFocus"): "61,134,255",
        ("kdeglobals", "General", "font"): "Noto Sans,13,-1,5,400,0,0,0,0,0,0,0,0,0,0,1",
        ("kwinrc", "NightColor", "Active"): "true",
    }

    def runner(argv):
        key = (argv[2], argv[4], argv[6])
        return (0, values[key] + "\n") if key in values else (0, "\n")

    state = ap.read_state(runner)
    assert state["mode"] == "dark" and state["accent"] == "#3d86ff"
    assert state["nightLight"] and state["textScale"] == 1.3


def test_read_state_defaults():
    state = ap.read_state(lambda argv: (-1, ""))
    assert state["mode"] == "light" and state["accent"] == "" and state["textScale"] == 1.0


def test_prefs(tmp_path):
    env = {"XDG_CONFIG_HOME": str(tmp_path)}
    assert ap.load_prefs(env) == {"centered": True, "floating": False}
    ap.save_pref("floating", True, env)
    ap.save_pref("centered", False, env)
    assert ap.load_prefs(env) == {"centered": False, "floating": True}
    ap.prefs_file(env).write_text("{roto")
    assert ap.load_prefs(env)["centered"] is True
