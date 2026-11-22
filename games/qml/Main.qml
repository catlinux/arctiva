// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    title: qsTr("Arctiva Games")
    width: Kirigami.Units.gridUnit * 46
    height: Kirigami.Units.gridUnit * 34
    minimumWidth: Kirigami.Units.gridUnit * 28
    minimumHeight: Kirigami.Units.gridUnit * 20

    // Cerrar la ventana cierra el motor y, con él, los lanzadores que hayan quedado abiertos esperando.
    onClosing: (close) => { if (gamesBackend.phase === "installing" || gamesBackend.phase === "downloading") close.accepted = false }

    pageStack.initialPage: Qt.resolvedUrl("GamesPage.qml")
}
