# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys

from .core import i18n, paths


def run():
    from PySide6.QtCore import QLocale, QTranslator, QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication

    from .backend import GamesBackend

    where = paths.resolve()
    if not os.environ.get("QT_QUICK_CONTROLS_STYLE"):
        QQuickStyle.setStyle("org.kde.desktop")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("arctiva-games")
    app.setApplicationDisplayName("Arctiva Games")
    app.setDesktopFileName("arctiva-games")
    app.setWindowIcon(QIcon.fromTheme("arctiva-games", QIcon.fromTheme("applications-games")))

    translator = QTranslator()
    for name in i18n.catalog_candidates(QLocale().uiLanguages()):
        if translator.load(str(where.translations / (name + ".qm"))):
            app.installTranslator(translator)
            break

    # En la sesión live solo se explora (ARCTIVA_GAMES_ALLOW_LIVE=1, para pruebas).
    live = paths.is_live() and os.environ.get("ARCTIVA_GAMES_ALLOW_LIVE") != "1"
    from .core import games_protondl
    backend = GamesBackend(where.data, live, app, proton=games_protondl.ensure)
    backend.ensureProton()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("isLive", live)
    engine.rootContext().setContextProperty("gamesBackend", backend)
    engine.load(QUrl.fromLocalFile(str(where.qml / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
