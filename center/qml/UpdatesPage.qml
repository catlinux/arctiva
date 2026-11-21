// SPDX-License-Identifier: GPL-3.0-or-later
// Provisional: solo lanza «update» y muestra el registro. El módulo completo (lista, noticias,
// paquetes delicados, .pacnew) lo sustituye.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.Page {
    id: page

    property int lastCode: -2

    actions: [
        Kirigami.Action {
            text: qsTr("Update the system")
            icon.name: "system-software-update"
            enabled: !helper.running
            onTriggered: {
                log.clear()
                page.lastCode = -2
                helper.run("update", [])
            }
        }
    ]

    Connections {
        target: helper
        function onLine(text) { log.append(text) }
        function onFinished(code) { page.lastCode = code }
    }

    ColumnLayout {
        anchors.fill: parent

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: helper.running || page.lastCode !== -2
            type: helper.running ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: helper.running ? qsTr("Updating…")
                : page.lastCode === 0 ? qsTr("Finished successfully")
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : qsTr("Finished with error code %1").arg(page.lastCode)
        }

        QQC2.ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            QQC2.TextArea {
                id: log
                readOnly: true
                wrapMode: TextEdit.WrapAnywhere
                font.family: "monospace"
            }
        }
    }
}
