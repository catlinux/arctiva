// SPDX-License-Identifier: GPL-3.0-or-later
// Diálogo al abrir un programa de Windows (D-12): qué va a pasar y cómo abrirlo con Bottles.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    title: qsTr("Open a Windows program")
    width: Kirigami.Units.gridUnit * 36
    height: Kirigami.Units.gridUnit * 30
    property int lastCode: -2

    Connections {
        target: windowsBackend
        function onLine(text) { log.append(text) }
        function onDone(code) { root.lastCode = code }
    }

    pageStack.initialPage: Kirigami.ScrollablePage {
        title: windowsBackend.fileName

        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: !windowsBackend.valid
                type: Kirigami.MessageType.Error
                text: qsTr("This file cannot be opened: it does not exist or it is not a Windows program.")
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: windowsBackend.live
                type: Kirigami.MessageType.Information
                text: qsTr("This is the live session: installing Bottles only works once Arctiva is installed.")
            }

            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: "application-x-executable"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.huge
                    Layout.preferredHeight: Kirigami.Units.iconSizes.huge
                    Layout.alignment: Qt.AlignTop
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Kirigami.Heading {
                        level: 2
                        text: windowsBackend.fileName
                        wrapMode: Text.WrapAnywhere
                        Layout.fillWidth: true
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("This is a program made for Windows. Arctiva can run many of them with Bottles, which keeps each program in its own separate “bottle”, so it does not touch your files or the system.")
                    }
                }
            }

            Kirigami.Heading {
                level: 3
                text: qsTr("What to expect")
            }
            QQC2.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                text: qsTr("Many programs and games work, some need a little tuning, and some do not work at all: games with anti-cheat, for example, usually refuse to run. Only open programs you trust.")
            }

            RowLayout {
                visible: windowsBackend.valid
                spacing: Kirigami.Units.largeSpacing
                QQC2.Button {
                    visible: windowsBackend.bottlesInstalled
                    text: qsTr("Open with Bottles")
                    icon.name: "system-run"
                    highlighted: true
                    onClicked: if (windowsBackend.openWithBottles()) Qt.quit()
                }
                QQC2.Button {
                    visible: !windowsBackend.bottlesInstalled
                    text: qsTr("Install Bottles")
                    icon.name: "run-build-install"
                    highlighted: true
                    enabled: !windowsBackend.live && !windowsBackend.busy
                    onClicked: {
                        log.clear()
                        root.lastCode = -2
                        windowsBackend.installBottles()
                    }
                }
                QQC2.BusyIndicator {
                    visible: windowsBackend.busy
                    running: visible
                }
                QQC2.Button {
                    text: qsTr("Cancel")
                    icon.name: "dialog-cancel"
                    onClicked: Qt.quit()
                }
            }

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: root.lastCode !== -2
                type: root.lastCode === 0 ? Kirigami.MessageType.Positive : Kirigami.MessageType.Error
                text: root.lastCode === 0 ? qsTr("Bottles is installed. Now you can open the program.")
                    : qsTr("Bottles could not be installed (error code %1). The log below has the details.").arg(root.lastCode)
            }

            LogView {
                id: log
                Layout.fillWidth: true
                Layout.preferredHeight: Kirigami.Units.gridUnit * 8
                visible: windowsBackend.busy || root.lastCode !== -2
            }

            Kirigami.Heading {
                level: 3
                text: qsTr("Check if it works first")
            }
            Flow {
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing
                Repeater {
                    model: windowsBackend.links
                    delegate: QQC2.Button {
                        required property var modelData
                        text: modelData.name
                        icon.name: "internet-web-browser"
                        onClicked: windowsBackend.openLink(modelData.url)
                    }
                }
            }
        }
    }
}
