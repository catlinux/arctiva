# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys

from .core import i18n, paths
from .modules import MODULES


def run(module):
    from PySide6.QtCore import QLocale, QTranslator, QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication

    where = paths.resolve()
    if not os.environ.get("QT_QUICK_CONTROLS_STYLE"):
        QQuickStyle.setStyle("org.kde.desktop")

    app = QApplication(sys.argv[:1])
    app.setApplicationName("arctiva-center")
    app.setApplicationDisplayName("Arctiva Center")
    app.setDesktopFileName("arctiva-center")
    app.setWindowIcon(QIcon.fromTheme("arctiva"))

    translator = QTranslator()
    for name in i18n.catalog_candidates(QLocale().uiLanguages()):
        if translator.load(str(where.translations / (name + ".qm"))):
            app.installTranslator(translator)
            break

    from .helper_process import HelperProcess
    from .drivers_backend import DriversBackend
    from .updates_backend import UpdatesBackend

    helper = HelperProcess(app)
    updates_backend = UpdatesBackend(where.data, app)
    drivers_backend = DriversBackend(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("initialModule", MODULES.index(module))
    engine.rootContext().setContextProperty("helper", helper)
    engine.rootContext().setContextProperty("updatesBackend", updates_backend)
    engine.rootContext().setContextProperty("driversBackend", drivers_backend)
    engine.load(QUrl.fromLocalFile(str(where.qml / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
