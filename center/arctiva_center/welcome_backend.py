# SPDX-License-Identifier: GPL-3.0-or-later
import subprocess

from PySide6.QtCore import Property, QObject, Signal, Slot

from . import __version__
from .core import snapshots, welcome


class WelcomeBackend(QObject):
    changed = Signal()

    @Property(str, constant=True)
    def version(self):
        return __version__

    @Slot(result="QVariantMap")
    def snapshotInfo(self):
        return {"count": snapshots.count(), "free": snapshots.free_bytes()}

    @Slot()
    def launchInstaller(self):
        """Abre «Instalar Arctiva» (solo en la live) sin atar el proceso a esta ventana."""
        subprocess.Popen(["arctiva-installer"], start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    def _get_show(self):
        return not welcome.done_file().exists()

    def _set_show(self, show):
        welcome.set_show_at_login(show)
        self.changed.emit()

    showAtLogin = Property(bool, _get_show, _set_show, notify=changed)
