// SPDX-License-Identifier: GPL-3.0-or-later
// Detalle de una aplicación: una fila por fuente (Arch, Flathub), con su distintivo, y el registro.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property string appId
    property var app: ({})
    property string workingKind: ""
    property string workingAction: ""
    property int lastCode: -2
    property bool needsUpdate: false
    readonly property var backend: appsBackend

    title: app.name || ""

    function reload() { app = backend.detail(appId) }

    Component.onCompleted: reload()

    Connections {
        target: backend
        function onChanged() { if (!backend.busy) page.reload() }
        function onLog(text) { if (page.workingKind !== "") log.append(text) }
        // Hay actualizaciones pendientes: no se instala hasta actualizar el sistema (D-07).
        function onUpdatesNeeded(id) {
            if (id === page.appId) {
                page.workingKind = ""
                page.needsUpdate = true
            }
        }
        function onFinished(code, id, action) {
            if (id !== page.appId)
                return
            page.workingKind = ""
            page.lastCode = code
            page.reload()
        }
    }

    function run(row) {
        log.clear()
        lastCode = -2
        needsUpdate = false
        workingKind = row.kind
        workingAction = row.installed ? "remove" : "install"
        if (row.installed)
            backend.remove(appId, row.kind)
        else
            backend.install(appId, row.kind)
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        RowLayout {
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon {
                source: page.app.icon || "package-x-generic"
                Layout.preferredWidth: Kirigami.Units.iconSizes.huge
                Layout.preferredHeight: Kirigami.Units.iconSizes.huge
                Layout.alignment: Qt.AlignTop
            }
            ColumnLayout {
                Layout.fillWidth: true
                Kirigami.Heading {
                    level: 1
                    text: page.app.name || ""
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: page.app.summary || ""
                }
                RowLayout {
                    visible: (page.app.license || "") !== "" || (page.app.homepage || "") !== ""
                    QQC2.Label {
                        visible: (page.app.license || "") !== ""
                        text: qsTr("License: %1").arg(page.app.license)
                        color: Kirigami.Theme.disabledTextColor
                    }
                    Kirigami.UrlButton {
                        visible: (page.app.homepage || "") !== ""
                        url: page.app.homepage || ""
                        text: qsTr("Website")
                    }
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: installing only works once Arctiva is installed.")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.needsUpdate
            type: Kirigami.MessageType.Warning
            text: qsTr("Your system has updates. To avoid a partial update, update first and then install.")
            actions: [
                Kirigami.Action {
                    text: qsTr("Update the system first")
                    icon.name: "system-software-update"
                    onTriggered: {
                        page.needsUpdate = false
                        applicationWindow().pageStack.layers.pop()
                        applicationWindow().show(2)
                    }
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.workingKind !== "" || page.lastCode !== -2
            type: page.workingKind !== "" ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: page.workingKind !== ""
                ? (page.workingAction === "remove" ? qsTr("Removing…") : qsTr("Installing…"))
                : page.lastCode === 0
                    ? (page.workingAction === "remove" ? qsTr("The application has been removed.") : qsTr("The application has been installed."))
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : page.lastCode === 64 ? qsTr("This operation is not allowed: it would touch parts of the system that must stay.")
                : qsTr("The operation failed (error code %1). The log below has the details.").arg(page.lastCode)
        }

        Kirigami.Heading {
            level: 3
            text: qsTr("Where to get it")
        }

        Repeater {
            model: page.app.rows || []
            delegate: Kirigami.AbstractCard {
                id: rowCard
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Chip {
                        text: rowCard.modelData.label
                        checkable: false
                        closable: false
                        enabled: false
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        QQC2.Label {
                            text: [rowCard.modelData.version, rowCard.modelData.size].filter(s => s !== "").join(" · ")
                            visible: text !== ""
                        }
                        QQC2.Label {
                            visible: rowCard.modelData.recommended
                            text: qsTr("Recommended")
                            font.bold: true
                            color: Kirigami.Theme.positiveTextColor
                        }
                        QQC2.Label {
                            visible: rowCard.modelData.installed
                            text: qsTr("Installed")
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                    QQC2.BusyIndicator {
                        visible: page.workingKind === rowCard.modelData.kind
                        running: visible
                    }
                    QQC2.Button {
                        visible: rowCard.modelData.kind === "flathub" && rowCard.modelData.installed
                        text: qsTr("Permissions")
                        icon.name: "preferences-system-permissions"
                        onClicked: backend.openPermissions()
                    }
                    QQC2.Button {
                        text: rowCard.modelData.installed ? qsTr("Remove") : qsTr("Install")
                        icon.name: rowCard.modelData.installed ? "edit-delete" : "run-build-install"
                        highlighted: !rowCard.modelData.installed && rowCard.modelData.recommended
                        enabled: !isLive && !backend.busy
                        onClicked: page.run(rowCard.modelData)
                    }
                }
            }
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: page.app.description || ""
            visible: text !== ""
        }

        Kirigami.Heading {
            level: 3
            visible: (page.app.screenshots || []).length > 0
            text: qsTr("Screenshots")
        }

        Flow {
            Layout.fillWidth: true
            spacing: Kirigami.Units.largeSpacing
            visible: (page.app.screenshots || []).length > 0
            Repeater {
                model: (page.app.screenshots || []).slice(0, 4)
                delegate: Image {
                    required property string modelData
                    source: modelData
                    asynchronous: true
                    fillMode: Image.PreserveAspectFit
                    width: Kirigami.Units.gridUnit * 12
                    height: Kirigami.Units.gridUnit * 8
                    // Si no carga (sin conexión), un texto en su lugar.
                    QQC2.Label {
                        anchors.centerIn: parent
                        visible: parent.status === Image.Error
                        text: qsTr("Screenshot not available")
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }

        LogView {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 10
            visible: page.workingKind !== "" || page.lastCode !== -2
        }
    }
}
