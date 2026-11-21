# SPDX-License-Identifier: GPL-3.0-or-later
from PySide6.QtCore import Property, QObject, Signal

from . import __version__
from .core import welcome


class WelcomeBackend(QObject):
    changed = Signal()

    @Property(str, constant=True)
    def version(self):
        return __version__

    def _get_show(self):
        return not welcome.done_file().exists()

    def _set_show(self, show):
        welcome.set_show_at_login(show)
        self.changed.emit()

    showAtLogin = Property(bool, _get_show, _set_show, notify=changed)
