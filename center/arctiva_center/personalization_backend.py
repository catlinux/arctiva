# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Personalización»: llama a core/appearance.py con las órdenes de Plasma."""
import subprocess

from PySide6.QtCore import Property, QObject, Signal, Slot

from .core import appearance


class PersonalizationBackend(QObject):
    changed = Signal()
    failed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state = {"mode": "light", "accent": "", "nightLight": False, "textScale": 1.0, "fonts": {}}
        self._screen_scale = 1.0
        self.refresh()

    def _apply(self, commands, what):
        if not appearance.apply(commands):
            self.failed.emit(what)
        self.refresh()

    @Slot()
    def refresh(self):
        self._state = appearance.read_state()
        self._state.update(appearance.load_prefs())
        _, out = appearance.run(["kscreen-doctor", "-j"])
        self._screen_scale = appearance.parse_scale(out)
        self.changed.emit()

    @Property(str, notify=changed)
    def mode(self):
        return self._state["mode"]

    @Property(str, notify=changed)
    def accent(self):
        return self._state["accent"]

    @Property(bool, notify=changed)
    def nightLight(self):
        return self._state["nightLight"]

    @Property(float, notify=changed)
    def textScale(self):
        return self._state["textScale"]

    @Property(float, notify=changed)
    def screenScale(self):
        return self._screen_scale

    @Property(bool, notify=changed)
    def centered(self):
        return self._state.get("centered", True)

    @Property(bool, notify=changed)
    def floating(self):
        return self._state.get("floating", False)

    @Property("QVariantList", constant=True)
    def accents(self):
        return [{"name": n, "color": c} for n, c in appearance.ACCENTS.items()]

    @Property("QVariantList", constant=True)
    def textScales(self):
        return list(appearance.TEXT_SCALES)

    @Property("QVariantList", constant=True)
    def screenScales(self):
        return list(appearance.SCREEN_SCALES)

    @Slot(str)
    def setMode(self, mode):
        self._apply(appearance.mode_commands(mode, self._state["accent"] or None), "mode")

    @Slot(str)
    def setAccent(self, color):
        self._apply(appearance.accent_commands(color), "accent")

    @Slot()
    def setArctivaWallpaper(self):
        self._apply(appearance.wallpaper_commands(), "wallpaper")

    @Slot(str)
    def setWallpaper(self, path):
        self._apply(appearance.wallpaper_commands(path.removeprefix("file://")), "wallpaper")

    @Slot(bool)
    def setCentered(self, centered):
        appearance.save_pref("centered", centered)
        self._apply(appearance.alignment_commands(centered), "alignment")

    @Slot(bool)
    def setFloating(self, floating):
        appearance.save_pref("floating", floating)
        self._apply(appearance.floating_commands(floating), "floating")

    @Slot(float)
    def setTextScale(self, scale):
        self._apply(appearance.text_commands(scale, self._state.get("fonts")), "text")

    @Slot(float)
    def setScreenScale(self, scale):
        _, out = appearance.run(["kscreen-doctor", "-j"])
        self._apply(appearance.screen_commands(scale, appearance.parse_outputs(out)), "scale")

    @Slot(bool)
    def setNightLight(self, active):
        self._apply(appearance.night_light_commands(active), "nightlight")

    @Slot()
    def restore(self):
        appearance.prefs_file().unlink(missing_ok=True)
        self._apply(appearance.restore_commands(), "restore")

    @Slot()
    def openAdvanced(self):
        subprocess.Popen(["systemsettings"], start_new_session=True)
