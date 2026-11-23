// SPDX-License-Identifier: GPL-3.0-or-later
// Detalle de la cola de instalaciones: estado de cada elemento y registro del que se elija.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.OverlaySheet {
    id: sheet

    property string selectedId: ""
    readonly property var items: appsBackend.queue

    title: qsTr("Installation queue")

    function stateText(item) {
        switch (item.state) {
        case "running": return item.action === "remove" ? qsTr("Removing…") : qsTr("Installing…")
        case "queued": return qsTr("Waiting")
        case "done": return item.action === "remove" ? qsTr("Removed") : qsTr("Installed")
        case "blocked": return qsTr("Update the system first")
        default: return (item.code === 126 || item.code === 127) ? qsTr("Authorization cancelled")
                                                                  : qsTr("Failed (code %1)").arg(item.code)
        }
    }

    function stateIcon(item) {
        switch (item.state) {
        case "running": return "view-refresh"
        case "queued": return "chronometer"
        case "done": return "dialog-ok-apply"
        case "blocked": return "system-software-update"
        default: return "dialog-error"
        }
    }

    function refreshLog() {
        log.text = selectedId !== "" ? (appsBackend.itemInfo(selectedId).log || "") : ""
    }

    onSelectedIdChanged: refreshLog()
    onOpened: {
        if (selectedId === "" && items.length > 0)
            selectedId = items[0].id
        refreshLog()
    }

    Connections {
        target: appsBackend
        function onLogFor(id, text) { if (id === sheet.selectedId) log.append(text) }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing
        implicitWidth: Kirigami.Units.gridUnit * 30

        Repeater {
            model: sheet.items
            delegate: QQC2.ItemDelegate {
                id: row
                required property var modelData
                Layout.fillWidth: true
                highlighted: modelData.id === sheet.selectedId
                onClicked: sheet.selectedId = modelData.id
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: sheet.stateIcon(row.modelData)
                        Layout.preferredHeight: Kirigami.Units.iconSizes.smallMedium
                        Layout.preferredWidth: Kirigami.Units.iconSizes.smallMedium
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        QQC2.Label {
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            text: row.modelData.name
                            font.bold: row.modelData.state === "running"
                        }
                        QQC2.Label {
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Kirigami.Theme.disabledTextColor
                            text: sheet.stateText(row.modelData)
                                  + (row.modelData.state === "running" && row.modelData.step !== "" ? " · " + row.modelData.step : "")
                        }
                        QQC2.ProgressBar {
                            visible: row.modelData.state === "running"
                            Layout.fillWidth: true
                            indeterminate: row.modelData.fraction < 0
                            from: 0
                            to: 1
                            value: row.modelData.fraction < 0 ? 0 : row.modelData.fraction
                        }
                    }
                    QQC2.Button {
                        visible: row.modelData.state === "queued" || row.modelData.state === "blocked"
                        icon.name: "dialog-cancel"
                        text: qsTr("Cancel")
                        onClicked: appsBackend.cancelQueued(row.modelData.id, row.modelData.kind)
                    }
                }
            }
        }

        LogView {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 10
            visible: sheet.selectedId !== ""
        }

        RowLayout {
            Layout.fillWidth: true
            Item { Layout.fillWidth: true }
            QQC2.Button {
                text: qsTr("Clear finished")
                icon.name: "edit-clear-all"
                onClicked: appsBackend.clearFinished()
            }
        }
    }
}
