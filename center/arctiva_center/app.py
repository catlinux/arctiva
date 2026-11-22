# SPDX-License-Identifier: GPL-3.0-or-later
import os
import sys

from .core import i18n, paths, welcome
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
    from .welcome_backend import WelcomeBackend
    from .personalization_backend import PersonalizationBackend
    from .extras_backend import ExtrasBackend
    from .updates_backend import UpdatesBackend
    from .apps_backend import AppsBackend
    from .aur_backend import AurBackend

    # En la live no se instala ni se actualiza nada (ARCTIVA_CENTER_ALLOW_LIVE=1, para pruebas).
    live = welcome.is_live() and os.environ.get("ARCTIVA_CENTER_ALLOW_LIVE") != "1"
    helper = HelperProcess(live, app)
    welcome_backend = WelcomeBackend(app)
    updates_backend = UpdatesBackend(where.data, app)
    drivers_backend = DriversBackend(app)
    extras_backend = ExtrasBackend(where.data, app)
    personalization_backend = PersonalizationBackend(app)
    apps_backend = AppsBackend(where.data, helper, live, app)
    aur_backend = AurBackend(helper, live, app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("initialModule", MODULES.index(module))
    engine.rootContext().setContextProperty("helper", helper)
    engine.rootContext().setContextProperty("isLive", live)
    engine.rootContext().setContextProperty("welcomeBackend", welcome_backend)
    engine.rootContext().setContextProperty("updatesBackend", updates_backend)
    engine.rootContext().setContextProperty("driversBackend", drivers_backend)
    engine.rootContext().setContextProperty("extrasBackend", extras_backend)
    engine.rootContext().setContextProperty("personalizationBackend", personalization_backend)
    engine.rootContext().setContextProperty("appsBackend", apps_backend)
    engine.rootContext().setContextProperty("aurBackend", aur_backend)
    engine.load(QUrl.fromLocalFile(str(where.qml / "Main.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()


def run_windows_app(path):
    """Ventana pequeña para abrir un .exe o .msi (D-12); no carga el resto de módulos."""
    from PySide6.QtCore import QLocale, QTranslator, QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication

    from .windows_backend import WindowsBackend

    where = paths.resolve()
    if not os.environ.get("QT_QUICK_CONTROLS_STYLE"):
        QQuickStyle.setStyle("org.kde.desktop")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("arctiva-center")
    app.setApplicationDisplayName("Arctiva")
    app.setDesktopFileName("arctiva-windows-app")
    app.setWindowIcon(QIcon.fromTheme("arctiva"))
    translator = QTranslator()
    for name in i18n.catalog_candidates(QLocale().uiLanguages()):
        if translator.load(str(where.translations / (name + ".qm"))):
            app.installTranslator(translator)
            break
    backend = WindowsBackend(path, welcome.is_live() and os.environ.get("ARCTIVA_CENTER_ALLOW_LIVE") != "1", app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("windowsBackend", backend)
    engine.load(QUrl.fromLocalFile(str(where.qml / "WindowsAppDialog.qml")))
    if not engine.rootObjects():
        return 1
    return app.exec()
