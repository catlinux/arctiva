// SPDX-License-Identifier: GPL-3.0-or-later
// Instalación de un juego: resumen y opciones, lista de pasos, registro en directo y procesos del prefijo.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property bool playing: false
    readonly property var backend: gamesBackend
    readonly property bool failed: backend.steps.some(s => s.state === "failed")
    readonly property bool installing: backend.phase === "installing"
    readonly property bool ready: backend.phase === "ready" && !page.playing
    readonly property int doneCount: backend.steps.filter(s => s.state === "done" || s.state === "skipped").length

    title: page.playing ? qsTr("Playing") : (backend.summary.name || qsTr("Install"))

    function back() {
        backend.cancelPlan()
        applicationWindow().pageStack.layers.pop()
    }

    function stateText(state) {
        switch (state) {
        case "running": return qsTr("In progress")
        case "done": return qsTr("Done")
        case "failed": return qsTr("Failed")
        case "skipped": return qsTr("Skipped")
        default: return qsTr("Pending")
        }
    }

    function stateIcon(state) {
        switch (state) {
        case "running": return "media-playback-start"
        case "done": return "emblem-ok-symbolic"
        case "failed": return "dialog-error"
        case "skipped": return "media-skip-forward"
        default: return "chronometer"
        }
    }

    function list(items) { return items.length > 0 ? items.join("\n") : qsTr("none") }

    Component.onCompleted: backend.startMonitor()
    Component.onDestruction: backend.stopMonitor()

    Connections {
        target: backend
        function onLogLine(text) { log.append(text) }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        // Resumen de seguridad y opciones (antes de empezar).
        ColumnLayout {
            Layout.fillWidth: true
            visible: page.ready
            spacing: Kirigami.Units.largeSpacing

            Kirigami.InlineMessage {
                Layout.fillWidth: true
                visible: backend.warnings.length > 0
                type: Kirigami.MessageType.Warning
                text: qsTr("This installer needs something Arctiva Games does not support yet, so it cannot be installed: %1").arg(backend.warnings.join("; "))
            }

            Kirigami.AbstractCard {
                Layout.fillWidth: true
                header: Kirigami.Heading { level: 3; text: qsTr("Options") }
                contentItem: ColumnLayout {
                    RowLayout {
                        visible: backend.runnerChoices.length > 0
                        QQC2.Label { text: qsTr("Runner") }
                        QQC2.ComboBox {
                            model: backend.runnerChoices
                            currentIndex: backend.runnerChoices.indexOf(backend.runnerName)
                            onActivated: backend.setRunner(currentText)
                        }
                    }
                    QQC2.CheckBox {
                        text: qsTr("Add to the application menu")
                        checked: backend.shortcutMenu
                        onToggled: backend.shortcutMenu = checked
                    }
                    QQC2.CheckBox {
                        text: qsTr("Add to the desktop")
                        checked: backend.shortcutDesktop
                        onToggled: backend.shortcutDesktop = checked
                    }
                    QQC2.CheckBox {
                        text: qsTr("Detailed log")
                        checked: backend.detailed
                        onToggled: backend.detailed = checked
                    }
                }
            }

            Kirigami.AbstractCard {
                Layout.fillWidth: true
                header: Kirigami.Heading { level: 3; text: qsTr("What it will do") }
                contentItem: ColumnLayout {
                    QQC2.Label { text: qsTr("Author: %1").arg(backend.summary.author || qsTr("unknown")) }
                    QQC2.Label {
                        visible: !!backend.summary.credits
                        text: qsTr("Credits: %1").arg(backend.summary.credits)
                    }
                    QQC2.Label { font.bold: true; text: qsTr("It will download") }
                    QQC2.Label { Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; text: page.list(backend.summary.urls || []) }
                    QQC2.Label { font.bold: true; text: qsTr("It will run") }
                    QQC2.Label { Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; text: page.list(backend.summary.executables || []) }
                    QQC2.Label { font.bold: true; text: qsTr("It will change in the Wine registry") }
                    QQC2.Label { Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; text: page.list(backend.summary.registry_keys || []) }
                    QQC2.Label { font.bold: true; text: qsTr("It will install with winetricks") }
                    QQC2.Label { Layout.fillWidth: true; wrapMode: Text.WrapAnywhere; text: page.list(backend.summary.winetricks || []) }
                }
            }

            RowLayout {
                QQC2.Button {
                    text: qsTr("Install")
                    icon.name: "run-install"
                    highlighted: true
                    enabled: !isLive && backend.warnings.length === 0
                    onClicked: backend.install()
                }
                QQC2.Button {
                    text: qsTr("Cancel")
                    onClicked: page.back()
                }
            }
        }

        // Pasos.
        QQC2.ProgressBar {
            Layout.fillWidth: true
            visible: !page.playing && !page.ready && backend.steps.length > 0
            from: 0
            to: Math.max(1, backend.steps.length)
            value: page.doneCount
        }
        Kirigami.Heading {
            level: 2
            visible: !page.playing && !page.ready
            text: qsTr("Steps")
        }
        Repeater {
            model: page.playing ? [] : backend.steps
            delegate: RowLayout {
                id: stepRow
                required property var modelData
                required property int index
                Layout.fillWidth: true
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: page.stateIcon(stepRow.modelData.state)
                    implicitWidth: Kirigami.Units.iconSizes.smallMedium
                    implicitHeight: Kirigami.Units.iconSizes.smallMedium
                    opacity: stepRow.modelData.state === "pending" ? 0.5 : 1
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: stepRow.modelData.description
                    font.bold: stepRow.modelData.state === "running"
                }
                QQC2.Label {
                    text: page.stateText(stepRow.modelData.state)
                    opacity: 0.7
                    font.bold: stepRow.modelData.state === "failed"
                }
            }
        }

        QQC2.BusyIndicator {
            Layout.alignment: Qt.AlignHCenter
            visible: backend.phase === "downloading"
            running: visible
        }
        QQC2.Label {
            visible: backend.phase === "downloading"
            text: qsTr("Downloading the installer files…")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.waiting !== ""
            type: Kirigami.MessageType.Information
            text: backend.waiting
            actions: Kirigami.Action {
                text: qsTr("Continue")
                icon.name: "go-next"
                onTriggered: backend.continueInstall()
            }
        }

        RowLayout {
            visible: page.installing
            QQC2.Button {
                visible: page.failed
                text: qsTr("Retry")
                icon.name: "view-refresh"
                onClicked: backend.retry()
            }
            QQC2.Button {
                visible: page.failed
                text: qsTr("Skip step")
                icon.name: "go-next-skip"
                onClicked: backend.skip()
            }
            QQC2.Button {
                text: qsTr("Stop")
                icon.name: "process-stop"
                onClicked: backend.stopInstall()
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.phase === "done"
            type: Kirigami.MessageType.Positive
            text: qsTr("Installed. You can find it in your installed games.")
            actions: Kirigami.Action {
                text: qsTr("Back to games")
                onTriggered: page.back()
            }
        }
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.phase === "failed"
            type: Kirigami.MessageType.Error
            text: backend.error !== "" ? backend.error : qsTr("The installation stopped. The Wine prefix was kept as it is.")
            actions: Kirigami.Action {
                text: qsTr("Back to games")
                onTriggered: page.back()
            }
        }

        // Procesos del prefijo.
        Kirigami.Heading {
            level: 2
            visible: !page.ready
            text: qsTr("Wine processes")
        }
        QQC2.Label {
            visible: !page.ready && backend.procs.length === 0
            text: qsTr("No Wine processes are running.")
            opacity: 0.7
        }
        Repeater {
            model: page.ready ? [] : backend.procs
            delegate: QQC2.Label {
                required property var modelData
                text: modelData.name + "  (pid " + modelData.pid + ", " + qsTr("%1 s running").arg(modelData.uptime) + ")"
            }
        }

        // Registro.
        Kirigami.Heading {
            level: 2
            visible: !page.ready
            text: qsTr("Log")
        }
        RowLayout {
            visible: !page.ready
            QQC2.CheckBox {
                text: qsTr("Detailed log")
                checked: backend.detailed
                enabled: !page.installing
                onToggled: backend.detailed = checked
            }
            QQC2.Button { text: qsTr("Open log"); icon.name: "document-open"; onClicked: backend.openLog() }
            QQC2.Button { text: qsTr("Copy log"); icon.name: "edit-copy"; onClicked: backend.copyLog() }
            QQC2.Button {
                visible: page.playing
                text: qsTr("Show launcher")
                icon.name: "window-new"
                onClicked: backend.showLauncher()
            }
            QQC2.Button {
                visible: page.playing
                text: qsTr("Close")
                onClicked: applicationWindow().pageStack.layers.pop()
            }
        }
        LogView {
            id: log
            visible: !page.ready
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 14
        }
    }
}
