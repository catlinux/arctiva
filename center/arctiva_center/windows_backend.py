# SPDX-License-Identifier: GPL-3.0-or-later
"""Diálogo para abrir un .exe o .msi (arctiva-center --windows-app <archivo>)."""
import subprocess

from PySide6.QtCore import Property, QObject, QProcess, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from .core import store, windows_app


class WindowsBackend(QObject):
    changed = Signal()
    line = Signal(str)
    done = Signal(int)

    def __init__(self, path, live=False, parent=None):
        super().__init__(parent)
        self._path = windows_app.check_file(path) or ""
        self._live = live
        self._proc = None
        self._installed = self._read()

    @staticmethod
    def _read():
        try:
            out = subprocess.run(store.flatpak_list_argv(), capture_output=True, text=True, timeout=30)
            return windows_app.bottles_installed(store.parse_flatpak_list(out.stdout)) if out.returncode == 0 else False
        except (OSError, subprocess.SubprocessError):
            return False

    @Property(str, constant=True)
    def fileName(self):
        return windows_app.display_name(self._path)

    @Property(bool, constant=True)
    def valid(self):
        return bool(self._path)

    @Property(bool, constant=True)
    def live(self):
        return self._live

    @Property(bool, notify=changed)
    def bottlesInstalled(self):
        return self._installed

    @Property(bool, notify=changed)
    def busy(self):
        return self._proc is not None

    @Property("QVariantList", constant=True)
    def links(self):
        return [{"name": n, "url": u} for n, u in windows_app.LINKS]

    @Slot(str)
    def openLink(self, url):
        if url in {u for _, u in windows_app.LINKS}:
            QDesktopServices.openUrl(QUrl(url))

    @Slot(result=bool)
    def openWithBottles(self):
        if not self._path or not self._installed:
            return False
        argv = windows_app.bottles_argv(self._path)
        return QProcess.startDetached(argv[0], argv[1:])

    @Slot()
    def installBottles(self):
        if self._proc is not None or self._live:
            return
        argv = store.flatpak_install_argv(windows_app.BOTTLES)
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: [
            self.line.emit(l) for l in bytes(proc.readAllStandardOutput()).decode("utf-8", "replace").splitlines() if l])
        proc.finished.connect(lambda code, status: self._finished(code if status == QProcess.ExitStatus.NormalExit else -1))
        proc.errorOccurred.connect(lambda e: self._finished(69) if e == QProcess.ProcessError.FailedToStart else None)
        self._proc = proc
        self.changed.emit()
        self.line.emit("$ " + " ".join(argv))
        proc.start(argv[0], argv[1:])

    def _finished(self, code):
        proc, self._proc = self._proc, None
        if proc is None:
            return
        proc.deleteLater()
        self._installed = self._read()
        self.changed.emit()
        self.done.emit(code)
