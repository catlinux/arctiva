# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Controladores» (D-10): qué gráficas hay y qué controladores faltan."""
from PySide6.QtCore import Property, QObject, QProcess, Signal, Slot

from .core import gpu


class DriversBackend(QObject):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checking = False
        self._report = gpu.GpuReport()
        self._missing = []
        self._kms_missing = False
        self._error = ""
        self._installed = set()

    @Property(bool, notify=changed)
    def checking(self):
        return self._checking

    @Property(list, notify=changed)
    def gpus(self):
        return self._report.gpus

    @Property(list, notify=changed)
    def packages(self):
        return [{"name": p, "installed": p not in self._missing} for p in self._report.packages]

    @Property(int, notify=changed)
    def missingCount(self):
        return len(self._missing) + (1 if self._kms_missing else 0)

    @Property(str, notify=changed)
    def warning(self):
        return self._report.warning

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Slot()
    def refresh(self):
        if self._checking:
            return
        self._checking = True
        self._error = ""
        self.changed.emit()
        # Primero lo instalado (pacman -Qq) y después arctiva-gpu sobre el sistema en marcha.
        self._run("pacman", ["-Qq"], self._installed_done)

    def _run(self, program, args, done):
        proc = QProcess(self)
        proc.finished.connect(lambda code, _s, p=proc: done(p, code))
        # Si el programa no arranca, Qt no emite finished.
        proc.errorOccurred.connect(lambda e, p=proc: done(p, -1)
                                   if e == QProcess.ProcessError.FailedToStart else None)
        proc.start(program, args)

    def _installed_done(self, proc, code):
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        proc.deleteLater()
        self._installed = gpu.parse_installed(out) if code == 0 else set()
        self._run("arctiva-gpu", ["--root", "/"], self._gpu_done)

    def _gpu_done(self, proc, code):
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        err = bytes(proc.readAllStandardError()).decode("utf-8", "replace").strip()
        proc.deleteLater()
        if code == 0:
            self._report = gpu.parse(out)
            self._missing, self._kms_missing = gpu.missing(self._report, self._installed)
        else:
            self._report = gpu.GpuReport()
            self._missing, self._kms_missing = [], False
            self._error = err or f"arctiva-gpu: {code}"
        self._checking = False
        self.changed.emit()
