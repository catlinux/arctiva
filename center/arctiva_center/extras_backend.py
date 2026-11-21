# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Extras»: catálogo con su estado; instalar y quitar va por el ayudante."""
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, QProcess, Signal, Slot

from .core import catalog, gpu

# Páginas de Configuración del sistema que se pueden abrir desde el módulo.
SETTINGS_PAGES = {"kcm_printer_manager", "kcm_firewall"}


class ExtrasBackend(QObject):
    changed = Signal()

    def __init__(self, data_dir, parent=None):
        super().__init__(parent)
        try:
            self._catalog = catalog.load(Path(data_dir) / "extras.toml", QLocale().uiLanguages())
        except (OSError, ValueError, KeyError):
            self._catalog = []
        self._installed = set()
        self._checking = False

    @Property(bool, notify=changed)
    def checking(self):
        return self._checking

    @Property(list, notify=changed)
    def extras(self):
        return [{"id": e.id, "name": e.name, "description": e.description, "icon": e.icon,
                 "installed": e.installed(self._installed)} for e in self._catalog]

    @Slot()
    def refresh(self):
        if self._checking:
            return
        self._checking = True
        self.changed.emit()
        proc = QProcess(self)
        proc.finished.connect(lambda code, _s, p=proc: self._done(p, code))
        proc.start("pacman", ["-Qq"])

    def _done(self, proc, code):
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        proc.deleteLater()
        self._installed = gpu.parse_installed(out) if code == 0 else set()
        self._checking = False
        self.changed.emit()

    @Slot(str)
    def openSettings(self, page):
        if page in SETTINGS_PAGES:
            QProcess.startDetached("systemsettings", [page])
