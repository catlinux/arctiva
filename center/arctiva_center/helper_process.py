# SPDX-License-Identifier: GPL-3.0-or-later
"""Puente Qt del ayudante: lanza pkexec con QProcess (sin shell) y emite la salida línea a línea."""
from PySide6.QtCore import Property, QObject, QProcess, Signal, Slot

from .core import helper_client


class HelperProcess(QObject):
    line = Signal(str)
    finished = Signal(int)
    runningChanged = Signal()

    def __init__(self, live=False, parent=None):
        super().__init__(parent)
        self._live = live
        self._process = None
        self._splitter = helper_client.LineSplitter()

    @Property(bool, notify=runningChanged)
    def running(self):
        return self._process is not None

    @Slot(str, list, result=bool)
    def run(self, operation, args):
        # Nunca dos operaciones a la vez: cortar pacman a medias es peor que un fallo.
        if self._process is not None:
            return False
        if self._live:
            self.line.emit("arctiva-center: no disponible en la sesión live")
            self.finished.emit(helper_client.EX_UNAVAILABLE)
            return False
        try:
            argv = helper_client.build_argv(operation, [str(a) for a in args])
        except ValueError as e:
            self.line.emit(str(e))
            self.finished.emit(helper_client.EX_USAGE)
            return False
        self._splitter = helper_client.LineSplitter()
        process = QProcess(self)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        process.readyReadStandardOutput.connect(self._read)
        process.finished.connect(self._done)
        process.errorOccurred.connect(self._error)
        self._process = process
        self.runningChanged.emit()
        process.start(argv[0], argv[1:])
        return True

    def _read(self):
        data = bytes(self._process.readAllStandardOutput()).decode("utf-8", "replace")
        for text in self._splitter.feed(data):
            self.line.emit(text)

    def _done(self, code, status):
        self._read()
        for text in self._splitter.flush():
            self.line.emit(text)
        if status != QProcess.ExitStatus.NormalExit:
            code = -1
        self._finish(code)

    def _error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.line.emit("pkexec no se pudo iniciar")
            self._finish(helper_client.PKEXEC_NOT_AUTHORIZED)

    def _finish(self, code):
        process, self._process = self._process, None
        if process is None:
            return
        process.deleteLater()
        self.runningChanged.emit()
        self.finished.emit(code)
