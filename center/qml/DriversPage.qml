// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Controladores» (D-10): gráficas detectadas, controladores necesarios e instalación.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property int lastCode: -2
    property bool mine: false
    readonly property bool busy: helper.running || driversBackend.checking

    function familyName(f) {
        switch (f) {
        case "nvidia": return qsTr("NVIDIA (GTX 16, RTX 20 or newer)")
        case "nvidia-legacy": return qsTr("NVIDIA (GTX 10, GTX 900 or older)")
        case "amd": return qsTr("AMD Radeon")
        case "intel": return qsTr("Intel")
        case "virtual": return qsTr("Virtual machine graphics")
        default: return qsTr("Other graphics card")
        }
    }

    actions: [
        Kirigami.Action {
            text: qsTr("Check again")
            icon.name: "view-refresh"
            enabled: !page.busy
            onTriggered: driversBackend.refresh()
        },
        Kirigami.Action {
            text: qsTr("Install drivers")
            icon.name: "run-install"
            enabled: !page.busy && driversBackend.missingCount > 0
            onTriggered: {
                log.clear()
                page.lastCode = -2
                page.mine = true
                helper.run("drivers-apply", [])
            }
        }
    ]

    Component.onCompleted: driversBackend.refresh()

    Connections {
        target: helper
        function onLine(text) { if (page.mine) log.append(text) }
        function onFinished(code) {
            if (!page.mine)
                return
            page.mine = false
            page.lastCode = code
            driversBackend.refresh()
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.mine || page.lastCode !== -2
            type: page.mine ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: page.mine ? qsTr("Installing the drivers…")
                : page.lastCode === 0 ? qsTr("The drivers are installed. Restart to start using them.")
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : qsTr("The drivers could not be installed (error code %1). Check your internet connection and the log below.").arg(page.lastCode)
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: driversBackend.error !== ""
            type: Kirigami.MessageType.Error
            text: qsTr("Could not detect the graphics cards: %1").arg(driversBackend.error)
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Graphics cards")
        }

        Repeater {
            model: driversBackend.gpus
            delegate: RowLayout {
                required property string modelData
                Kirigami.Icon {
                    source: "video-display"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
                QQC2.Label { text: page.familyName(modelData) }
            }
        }

        QQC2.Label {
            visible: !driversBackend.checking && driversBackend.gpus.length === 0 && driversBackend.error === ""
            text: qsTr("No graphics card was detected.")
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Drivers")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: driversBackend.checking ? qsTr("Checking…")
                : driversBackend.packages.length === 0
                    ? qsTr("No additional drivers are needed: your graphics work with the drivers included in Arctiva.")
                : driversBackend.missingCount === 0
                    ? qsTr("Everything that is needed is installed.")
                    : qsTr("Some drivers are missing (for example, because Arctiva was installed without an internet connection). Install them with the button above; you will need to restart afterwards.")
        }

        Repeater {
            model: driversBackend.packages
            delegate: RowLayout {
                required property var modelData
                Kirigami.Icon {
                    source: modelData.installed ? "dialog-ok" : "dialog-warning"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
                QQC2.Label { text: modelData.name }
                QQC2.Label {
                    opacity: 0.7
                    text: modelData.installed ? qsTr("installed") : qsTr("missing")
                }
            }
        }

        // NVIDIA anterior a Turing: el controlador propietario que le sirve solo está en el AUR.
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: driversBackend.warning === "nvidia-legacy"
            type: Kirigami.MessageType.Warning
            text: qsTr("Your NVIDIA card is supported only by the old proprietary driver (580xx series), which Arch Linux no longer ships: it is only in the AUR, maintained by the community. Arctiva uses the free nouveau driver instead, which is fine for the desktop and video but slow for games. Advanced users can install the AUR driver at their own risk; Arctiva does not do it automatically because an update could leave the system without graphics.")
            actions: Kirigami.Action {
                text: qsTr("More information")
                icon.name: "internet-services"
                onTriggered: Qt.openUrlExternally("https://wiki.archlinux.org/title/NVIDIA")
            }
        }

        QQC2.TextArea {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 14
            visible: text !== ""
            readOnly: true
            wrapMode: TextEdit.WrapAnywhere
            font.family: "monospace"
        }
    }
}
