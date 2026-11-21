// SPDX-License-Identifier: GPL-3.0-or-later
// Bienvenida (decisión 9): primeros pasos con Arctiva y acceso a cada módulo.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    Component.onCompleted: driversBackend.refresh()

    component Step: Kirigami.AbstractCard {
        id: step
        property string stepIcon
        property string stepTitle
        property string stepText
        property string stepButton
        property int module: -1
        Layout.fillWidth: true
        contentItem: RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                source: step.stepIcon
                Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                Layout.alignment: Qt.AlignTop
            }
            ColumnLayout {
                Layout.fillWidth: true
                Kirigami.Heading {
                    level: 3
                    text: step.stepTitle
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: step.stepText
                }
            }
            QQC2.Button {
                visible: step.module >= 0
                text: step.stepButton
                onClicked: applicationWindow().show(step.module)
            }
        }
    }


    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing * 2

        RowLayout {
            spacing: Kirigami.Units.largeSpacing * 2
            Kirigami.Icon {
                source: "arctiva"
                Layout.preferredWidth: Kirigami.Units.iconSizes.enormous
                Layout.preferredHeight: Kirigami.Units.iconSizes.enormous
            }
            ColumnLayout {
                Kirigami.Heading {
                    level: 1
                    text: qsTr("Welcome to Arctiva")
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("These are the first steps to leave your system ready. You can come back to them at any time from Arctiva Center.")
                }
                QQC2.Label {
                    opacity: 0.7
                    text: qsTr("Arctiva Center %1").arg(welcomeBackend.version)
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: you can look around, but installing and updating only work once Arctiva is installed.")
        }

        Step {
            stepIcon: driversBackend.missingCount > 0 ? "dialog-warning" : "video-display"
            stepTitle: qsTr("Graphics drivers")
            stepText: driversBackend.checking ? qsTr("Checking your graphics card…")
                : driversBackend.missingCount > 0
                    ? qsTr("Some drivers for your graphics card are missing, probably because Arctiva was installed without an internet connection.")
                    : qsTr("Your graphics card is ready.")
            stepButton: qsTr("Open Drivers")
            module: 2
        }

        Step {
            stepIcon: "system-software-update"
            stepTitle: qsTr("Updates")
            stepText: qsTr("Keep Arctiva up to date from here. Before updating, Arctiva Center shows the Arch Linux news that need your attention, and it will notify you when there are new updates.")
            stepButton: qsTr("Check now")
            module: 1
        }

        Step {
            stepIcon: "package-x-generic"
            stepTitle: qsTr("Extras")
            stepText: qsTr("Add Gaming, Office or a second kernel whenever you want, with a switch.")
            stepButton: qsTr("Open Extras")
            module: 3
        }

        Step {
            stepIcon: "document-revert"
            stepTitle: qsTr("Snapshots: going back")
            stepText: qsTr("Before and after every installation or update, Arctiva takes a snapshot of the system. If something stops working after an update, restart and choose 'Arctiva snapshots' in the start menu (GRUB) to start the computer as it was before. Changes made while started from a snapshot are temporary.")
        }

        QQC2.CheckBox {
            text: qsTr("Show this welcome when logging in")
            checked: welcomeBackend.showAtLogin
            onToggled: welcomeBackend.showAtLogin = checked
        }
    }
}
