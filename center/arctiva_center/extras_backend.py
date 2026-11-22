# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Extras»: catálogo con su estado; instalar y quitar va por el ayudante."""
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, QProcess, Signal, Slot

from .core import catalog, gpu, store

# Páginas de Configuración del sistema que se pueden abrir desde el módulo.
SETTINGS_PAGES = {"kcm_printer_manager", "kcm_firewall"}


class ExtrasBackend(QObject):
    changed = Signal()
    flatpakLine = Signal(str)
    flatpakFinished = Signal(int)

    def __init__(self, data_dir, parent=None):
        super().__init__(parent)
        try:
            self._catalog = catalog.load(Path(data_dir) / "extras.toml", QLocale().uiLanguages())
        except (OSError, ValueError, KeyError):
            self._catalog = []
        self._installed = set()
        self._flatpaks = set()
        self._checking = False
        self._queue = []                    # órdenes de flatpak pendientes del extra en marcha
        self._flatpak_proc = None

    @Property(bool, notify=changed)
    def checking(self):
        return self._checking

    @Property(bool, notify=changed)
    def flatpakBusy(self):
        return self._flatpak_proc is not None

    @Property(list, notify=changed)
    def extras(self):
        return [{"id": e.id, "name": e.name, "description": e.description, "icon": e.icon,
                 "flatpak": bool(e.flatpaks), "installed": e.installed(self._installed, self._flatpaks)}
                for e in self._catalog]

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
        # Después, las aplicaciones de Flatpak (los extras de Windows y de juegos de Flathub).
        flat = QProcess(self)
        flat.finished.connect(lambda c, _s, p=flat: self._flatpak_listed(p, c))
        flat.errorOccurred.connect(lambda e, p=flat: self._flatpak_listed(p, -1)
                                   if e == QProcess.ProcessError.FailedToStart else None)
        argv = store.flatpak_list_argv()
        flat.start(argv[0], argv[1:])

    def _flatpak_listed(self, proc, code):
        if proc.property("done"):
            return
        proc.setProperty("done", True)
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace") if code == 0 else ""
        proc.deleteLater()
        self._flatpaks = store.parse_flatpak_list(out)
        self._checking = False
        self.changed.emit()

    @Slot(str, bool)
    def runFlatpak(self, extra_id, install):
        """Instala o quita las aplicaciones de Flatpak de un extra, una tras otra y sin el ayudante."""
        extra = next((e for e in self._catalog if e.id == extra_id), None)
        if extra is None or not extra.flatpaks or self._flatpak_proc is not None:
            self.flatpakFinished.emit(64)
            return
        build = store.flatpak_install_argv if install else store.flatpak_uninstall_argv
        self._queue = [build(ref) for ref in extra.flatpaks]
        self._next_flatpak()

    def _next_flatpak(self):
        if not self._queue:
            self._flatpak_proc = None
            self.changed.emit()
            self.flatpakFinished.emit(0)
            return
        argv = self._queue.pop(0)
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: [
            self.flatpakLine.emit(l) for l in bytes(proc.readAllStandardOutput()).decode("utf-8", "replace").splitlines() if l])
        proc.finished.connect(lambda code, status: self._flatpak_step_done(
            proc, code if status == QProcess.ExitStatus.NormalExit else -1))
        proc.errorOccurred.connect(lambda e: self._flatpak_step_done(proc, 69)
                                   if e == QProcess.ProcessError.FailedToStart else None)
        self._flatpak_proc = proc
        self.changed.emit()
        self.flatpakLine.emit("$ " + " ".join(argv))
        proc.start(argv[0], argv[1:])

    def _flatpak_step_done(self, proc, code):
        if proc is not self._flatpak_proc:
            return
        proc.deleteLater()
        if code != 0:
            self._queue = []
            self._flatpak_proc = None
            self.changed.emit()
            self.flatpakFinished.emit(code)
            return
        self._next_flatpak()

    @Slot(str)
    def openSettings(self, page):
        if page in SETTINGS_PAGES:
            QProcess.startDetached("systemsettings", [page])
