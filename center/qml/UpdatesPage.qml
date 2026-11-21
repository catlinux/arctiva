// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Actualizaciones» (D-08): noticias que bloquean, paquetes delicados, registro real,
// errores explicados, Flatpak, .pacnew y aviso de reinicio.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property int lastCode: -2
    property string operation: ""
    property bool showLog: false
    readonly property bool busy: helper.running || updatesBackend.checking

    function runHelper(op, args) {
        page.operation = op
        if (op === "update") {
            page.flickable.contentY = 0
            log.clear()
            page.lastCode = -2
            page.showLog = true
            updatesBackend.updateStarted()
        }
        helper.run(op, args)
    }

    function resolvePacnew(op, path) {
        page.operation = "pacnew"
        helper.run(op, [path])
    }

    actions: [
        Kirigami.Action {
            text: qsTr("Check now")
            icon.name: "view-refresh"
            enabled: !page.busy
            onTriggered: updatesBackend.check()
        },
        Kirigami.Action {
            text: qsTr("Update")
            icon.name: "system-software-update"
            enabled: !isLive && !page.busy && !updatesBackend.blocked && updatesBackend.updates.length > 0
            onTriggered: page.runHelper("update", [])
        }
    ]

    Component.onCompleted: updatesBackend.check()

    Connections {
        target: helper
        function onLine(text) { log.append(text) }
        function onFinished(code) {
            if (page.operation === "update") {
                page.lastCode = code
                updatesBackend.updateFinished(code, log.text)
                if (code === 0)
                    updatesBackend.updateFlatpak()
            } else if (page.operation === "pacnew") {
                updatesBackend.refreshPacnew()
            }
            page.operation = ""
        }
    }

    Connections {
        target: updatesBackend
        function onFlatpakLine(text) { log.append(text) }
        // Tras Flatpak se vuelve a comprobar: la lista y las noticias ya no son las de antes.
        function onFlatpakFinished(code) { updatesBackend.check() }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: installing and updating only work once Arctiva is installed.")
        }

        // Resultado de la última actualización y, si falló, qué significa.
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: helper.running && page.operation === "update" || page.lastCode !== -2
            type: helper.running ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: helper.running ? qsTr("Updating…")
                : page.lastCode === 0 ? qsTr("The system is up to date.")
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : updatesBackend.explanation.message !== undefined ? updatesBackend.explanation.message
                : qsTr("The update failed (error code %1). The log below has the details.").arg(page.lastCode)
            actions: [
                Kirigami.Action {
                    visible: !helper.running && updatesBackend.explanation.action === "keyring-first"
                    text: qsTr("Update the keyring first")
                    onTriggered: page.runHelper("update", ["--keyring-first"])
                },
                Kirigami.Action {
                    visible: !helper.running && updatesBackend.explanation.action === "retry"
                    text: qsTr("Try again")
                    onTriggered: page.runHelper("update", [])
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: updatesBackend.rebootRecommended
            type: Kirigami.MessageType.Warning
            text: qsTr("The kernel, the graphics drivers or core system libraries were updated. Restart to start using them.")
            actions: Kirigami.Action {
                text: qsTr("Restart now")
                icon.name: "system-reboot"
                enabled: !page.busy
                onTriggered: updatesBackend.reboot()
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: updatesBackend.checkError !== ""
            type: Kirigami.MessageType.Error
            text: qsTr("Could not check for updates: %1").arg(updatesBackend.checkError)
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: updatesBackend.newsError !== ""
            type: Kirigami.MessageType.Warning
            text: qsTr("Could not load the Arch Linux news (%1). You can update anyway, but read them at archlinux.org when you can.").arg(updatesBackend.newsError)
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: updatesBackend.blocked
            type: Kirigami.MessageType.Warning
            text: qsTr("A news item requires manual intervention. Read it and follow its instructions before updating.")
        }

        // Noticias publicadas desde la última actualización completa.
        Kirigami.Heading {
            level: 2
            visible: updatesBackend.news.length > 0
            text: qsTr("Arch Linux news")
        }

        Repeater {
            model: updatesBackend.news
            delegate: Kirigami.AbstractCard {
                required property var modelData
                Layout.fillWidth: true
                contentItem: ColumnLayout {
                    Kirigami.Heading {
                        level: 4
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: modelData.title
                    }
                    QQC2.Label {
                        opacity: 0.7
                        text: modelData.date
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        maximumLineCount: 6
                        elide: Text.ElideRight
                        text: modelData.text
                    }
                    RowLayout {
                        QQC2.Button {
                            text: qsTr("Read on archlinux.org")
                            icon.name: "internet-services"
                            onClicked: Qt.openUrlExternally(modelData.link)
                        }
                        QQC2.Button {
                            visible: modelData.manual && !modelData.read
                            text: qsTr("I have read it")
                            icon.name: "dialog-ok"
                            onClicked: updatesBackend.markRead(modelData.guid)
                        }
                        Kirigami.Chip {
                            visible: modelData.manual
                            checkable: false
                            closable: false
                            icon.name: modelData.read ? "dialog-ok" : "dialog-warning"
                            text: qsTr("Manual intervention")
                        }
                    }
                }
            }
        }

        // Lista de actualizaciones.
        Kirigami.Heading {
            level: 2
            text: updatesBackend.checking ? qsTr("Checking for updates…")
                : updatesBackend.updates.length === 0 ? qsTr("No updates available")
                // Sin numerus de Qt: el inglés no tiene catálogo y mostraría el texto fuente.
                : updatesBackend.updates.length === 1 ? qsTr("1 update available")
                : qsTr("%1 updates available").arg(updatesBackend.updates.length)
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            visible: updatesBackend.updates.some(u => u.delicate)
            text: qsTr("Packages marked as sensitive affect starting the system or the desktop. A snapshot is taken before updating: if something goes wrong, you can boot it from the GRUB menu.")
        }

        Repeater {
            model: updatesBackend.updates
            delegate: RowLayout {
                required property var modelData
                Layout.fillWidth: true
                Kirigami.Icon {
                    source: modelData.delicate ? "dialog-warning" : "package-x-generic"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.small
                    Layout.preferredHeight: Kirigami.Units.iconSizes.small
                }
                QQC2.Label {
                    text: modelData.name
                    font.bold: modelData.delicate
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    opacity: 0.7
                    elide: Text.ElideRight
                    text: modelData.old + " → " + modelData.new
                }
                QQC2.Label {
                    visible: modelData.delicate
                    text: qsTr("sensitive")
                    color: Kirigami.Theme.neutralTextColor
                }
            }
        }

        // Archivos de configuración nuevos que dejó la actualización.
        Kirigami.Heading {
            level: 2
            visible: updatesBackend.pacnewFiles.length > 0
            text: qsTr("New configuration files")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            visible: updatesBackend.pacnewFiles.length > 0
            text: qsTr("An update brought a new version of these files, but yours were kept because they had been changed. Compare them and choose which one to keep; when the new one is used, yours is saved with the .pacsave extension.")
        }

        Repeater {
            model: updatesBackend.pacnewFiles
            delegate: ColumnLayout {
                required property var modelData
                Layout.fillWidth: true
                QQC2.Label {
                    font.bold: true
                    text: modelData.path
                }
                LogView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Math.min(implicitHeight, Kirigami.Units.gridUnit * 12)
                    text: modelData.diff !== "" ? modelData.diff
                        : qsTr("The differences cannot be shown (the file cannot be read without administrator rights or is not text).")
                }
                RowLayout {
                    QQC2.Button {
                        text: qsTr("Keep mine")
                        enabled: !page.busy
                        onClicked: page.resolvePacnew("pacnew-keep", modelData.path)
                    }
                    QQC2.Button {
                        text: qsTr("Use the new one")
                        enabled: !page.busy
                        onClicked: page.resolvePacnew("pacnew-use", modelData.path)
                    }
                }
            }
        }

        // Registro real de pacman y Flatpak.
        QQC2.Button {
            text: page.showLog ? qsTr("Hide log") : qsTr("Show log")
            icon.name: "view-list-text"
            visible: log.text !== ""
            onClicked: page.showLog = !page.showLog
        }

        LogView {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 16
            visible: page.showLog
        }
    }
}
