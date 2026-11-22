// SPDX-License-Identifier: GPL-3.0-or-later
// Progreso de una instalación larga: barra, paso actual y tiempo transcurrido. pacman da
// «(n/m)» en cada paquete y la barra es real; Flatpak no da porcentaje con --noninteractive,
// así que la barra queda indeterminada y se cuentan los componentes ya tratados.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

ColumnLayout {
    id: root

    property bool active: false
    property real fraction: -1          // < 0: sin porcentaje
    property string current: ""
    property int steps: 0
    property int elapsed: 0
    property real startedAt: 0

    visible: active
    spacing: Kirigami.Units.smallSpacing

    function reset() {
        fraction = -1
        current = ""
        steps = 0
        elapsed = 0
        startedAt = Date.now()
    }

    // Una línea de la salida de pacman o de Flatpak.
    function feed(text) {
        var pacman = /^\((\d+)\/(\d+)\)\s*(.*)$/.exec(text)
        if (pacman) {
            fraction = Number(pacman[1]) / Number(pacman[2])
            current = pacman[3]
            return
        }
        if (/^(Instalando|Installing|Instal·lant|Actualizando|Updating|Actualitzant|Desinstalando|Uninstalling|Desinstal·lant)\s/.test(text)) {
            steps += 1
            current = text
            return
        }
        if (/^:: /.test(text))
            current = text.substring(3)
    }

    function elapsedText() {
        var minutes = Math.floor(elapsed / 60)
        var seconds = elapsed % 60
        return minutes > 0 ? qsTr("%1 min %2 s").arg(minutes).arg(seconds) : qsTr("%1 s").arg(seconds)
    }

    Timer {
        running: root.active
        interval: 1000
        repeat: true
        onTriggered: root.elapsed = Math.floor((Date.now() - root.startedAt) / 1000)
    }

    QQC2.ProgressBar {
        Layout.fillWidth: true
        indeterminate: root.fraction < 0
        from: 0
        to: 1
        value: root.fraction < 0 ? 0 : root.fraction
    }

    QQC2.Label {
        Layout.fillWidth: true
        elide: Text.ElideMiddle
        text: root.current !== "" ? root.current : qsTr("Preparing…")
    }

    QQC2.Label {
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
        color: Kirigami.Theme.disabledTextColor
        text: (root.fraction >= 0
                   ? qsTr("%1% done").arg(Math.round(root.fraction * 100))
                   : root.steps > 0 ? qsTr("Components processed: %1").arg(root.steps)
                                    : qsTr("Downloading and installing…"))
              + " · " + qsTr("Time elapsed: %1").arg(root.elapsedText())
              + "\n" + qsTr("This can take several minutes. Do not turn off or suspend the computer until it finishes.")
    }
}
