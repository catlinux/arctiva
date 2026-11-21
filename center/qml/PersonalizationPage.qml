// SPDX-License-Identifier: GPL-3.0-or-later
// Personalización (decisión 2 de la fase 5): lo básico en una página, como en Windows.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    readonly property var backend: personalizationBackend

    function textScaleLabel(s) {
        return s < 1 ? qsTr("Small") : s === 1 ? qsTr("Normal") : s < 1.2 ? qsTr("Large") : qsTr("Very large")
    }

    component Section: Kirigami.AbstractCard {
        id: card
        property string heading
        default property alias content: body.data
        Layout.fillWidth: true
        contentItem: ColumnLayout {
            spacing: Kirigami.Units.smallSpacing
            Kirigami.Heading {
                level: 3
                text: card.heading
            }
            ColumnLayout {
                id: body
                spacing: Kirigami.Units.smallSpacing
                Layout.fillWidth: true
            }
        }
    }

    Connections {
        target: page.backend
        function onFailed() {
            message.visible = true
        }
    }

    FileDialog {
        id: chooser
        title: qsTr("Choose a wallpaper")
        nameFilters: [qsTr("Images (*.png *.jpg *.jpeg *.webp *.svg)")]
        onAccepted: page.backend.setWallpaper(selectedFile.toString())
    }

    Kirigami.PromptDialog {
        id: restoreDialog
        title: qsTr("Restore the Arctiva look")
        subtitle: qsTr("The theme, the taskbar, the wallpaper, the accent colour and the text size go back to how they were when Arctiva was installed. Your files and programs are not touched.")
        standardButtons: Kirigami.Dialog.Cancel
        customFooterActions: [
            Kirigami.Action {
                text: qsTr("Restore")
                icon.name: "edit-undo"
                onTriggered: {
                    page.backend.restore()
                    restoreDialog.close()
                }
            }
        ]
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            id: message
            Layout.fillWidth: true
            type: Kirigami.MessageType.Warning
            showCloseButton: true
            text: qsTr("Some changes could not be applied. This page works inside the Arctiva desktop session.")
        }

        Section {
            heading: qsTr("Appearance")
            RowLayout {
                spacing: Kirigami.Units.largeSpacing
                QQC2.RadioButton {
                    text: qsTr("Light")
                    checked: page.backend.mode === "light"
                    onClicked: page.backend.setMode("light")
                }
                QQC2.RadioButton {
                    text: qsTr("Dark")
                    checked: page.backend.mode === "dark"
                    onClicked: page.backend.setMode("dark")
                }
                QQC2.RadioButton {
                    text: qsTr("Automatic")
                    checked: page.backend.mode === "auto"
                    onClicked: page.backend.setMode("auto")
                }
            }
            QQC2.Label {
                text: qsTr("Accent colour")
                font.bold: true
            }
            RowLayout {
                spacing: Kirigami.Units.smallSpacing
                Repeater {
                    model: page.backend.accents
                    delegate: QQC2.AbstractButton {
                        id: swatch
                        required property var modelData
                        implicitWidth: Kirigami.Units.iconSizes.medium
                        implicitHeight: implicitWidth
                        // No es checkable: un clic rompería el enlace con el acento real.
                        readonly property bool selected: page.backend.accent.toLowerCase() === modelData.color
                        onClicked: page.backend.setAccent(modelData.color)
                        QQC2.ToolTip.text: modelData.name
                        QQC2.ToolTip.visible: hovered
                        contentItem: Item {}
                        background: Rectangle {
                            radius: width / 2
                            color: swatch.modelData.color
                            border.width: swatch.selected ? 3 : 0
                            border.color: Kirigami.Theme.textColor
                        }
                    }
                }
            }
        }

        Section {
            heading: qsTr("Wallpaper")
            RowLayout {
                QQC2.Button {
                    text: qsTr("Arctiva wallpaper")
                    icon.name: "preferences-desktop-wallpaper"
                    onClicked: page.backend.setArctivaWallpaper()
                }
                QQC2.Button {
                    text: qsTr("Choose image…")
                    icon.name: "document-open"
                    onClicked: chooser.open()
                }
            }
        }

        Section {
            heading: qsTr("Taskbar")
            QQC2.Switch {
                text: qsTr("Centre the applications")
                checked: page.backend.centered
                onToggled: page.backend.setCentered(checked)
            }
            QQC2.Switch {
                text: qsTr("Floating bar")
                checked: page.backend.floating
                onToggled: page.backend.setFloating(checked)
            }
            QQC2.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                color: Kirigami.Theme.disabledTextColor
                text: qsTr("To move or add things on the bar, right-click it and choose Enter Edit Mode.")
            }
        }

        Section {
            heading: qsTr("Screen")
            RowLayout {
                QQC2.Label { text: qsTr("Text size") }
                QQC2.ComboBox {
                    model: page.backend.textScales.map(page.textScaleLabel)
                    currentIndex: page.backend.textScales.indexOf(page.backend.textScale)
                    onActivated: (i) => page.backend.setTextScale(page.backend.textScales[i])
                }
            }
            RowLayout {
                QQC2.Label { text: qsTr("Display scale") }
                QQC2.ComboBox {
                    model: page.backend.screenScales.map(s => Math.round(s * 100) + " %")
                    currentIndex: page.backend.screenScales.indexOf(page.backend.screenScale)
                    onActivated: (i) => page.backend.setScreenScale(page.backend.screenScales[i])
                }
            }
            QQC2.Switch {
                text: qsTr("Night light")
                checked: page.backend.nightLight
                onToggled: page.backend.setNightLight(checked)
            }
        }

        RowLayout {
            spacing: Kirigami.Units.largeSpacing
            QQC2.Button {
                text: qsTr("Restore the Arctiva look")
                icon.name: "edit-undo"
                onClicked: restoreDialog.open()
            }
            QQC2.Button {
                text: qsTr("Advanced settings")
                icon.name: "preferences-system"
                onClicked: page.backend.openAdvanced()
            }
        }
    }
}
