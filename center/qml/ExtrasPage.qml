// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Extras»: instalar y quitar grupos de programas del catálogo (extras.toml).
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property string working: ""
    property bool removing: false
    property int lastCode: -2
    property string lastName: ""
    readonly property bool busy: helper.running || extrasBackend.checking || extrasBackend.flatpakBusy

    function toggle(extra) {
        // Instalar puede ser una descarga grande: se avisa antes. Quitar no necesita aviso.
        if (extra.installed) {
            start(extra)
        } else {
            confirm.extra = extra
            confirm.open()
        }
    }

    function start(extra) {
        log.clear()
        progress.reset()
        page.lastCode = -2
        page.working = extra.id
        page.lastName = extra.name
        page.removing = extra.installed
        // Los extras de Flathub no pasan por el ayudante: Flatpak tiene sus propias acciones de polkit.
        if (extra.flatpak)
            extrasBackend.runFlatpak(extra.id, !extra.installed)
        else
            helper.run(extra.installed ? "extra-remove" : "extra-install", [extra.id])
    }

    // Claude Desktop es software propietario: Arctiva no lo aloja; se monta en el equipo con la receta
    // del AUR (descarga el paquete oficial de Anthropic) y pasa por la revisión del PKGBUILD.
    readonly property string claudeName: "claude-desktop"
    property bool claudeInstalled: false

    function refreshClaude() { claudeInstalled = aurBackend.isInstalled(claudeName) }

    Component.onCompleted: {
        extrasBackend.refresh()
        refreshClaude()
    }

    Connections {
        target: aurBackend
        function onFinished(code) { page.refreshClaude() }
    }

    Kirigami.PromptDialog {
        id: confirm
        property var extra: null
        title: qsTr("Install %1?").arg(extra ? extra.name : "")
        subtitle: qsTr("The download can be large and take from a few minutes to over half an hour, depending on your connection. You can keep using the computer, but do not turn it off or suspend it until it finishes.")
        standardButtons: Kirigami.Dialog.Ok | Kirigami.Dialog.Cancel
        onAccepted: page.start(extra)
    }

    Connections {
        target: helper
        function onLine(text) { if (page.working !== "") { log.append(text); progress.feed(text) } }
        function onFinished(code) {
            if (page.working === "")
                return
            // Arctiva Games trae GE-Proton «de serie»: se prepara justo después de instalar el extra.
            if (code === 0 && page.working === "arctiva-games" && !page.removing)
                extrasBackend.prepareGames()
            page.working = ""
            page.lastCode = code
            extrasBackend.refresh()
        }
    }

    Connections {
        target: extrasBackend
        function onFlatpakLine(text) { if (page.working !== "") { log.append(text); progress.feed(text) } }
        function onFlatpakFinished(code) {
            if (page.working === "")
                return
            page.working = ""
            page.lastCode = code
            extrasBackend.refresh()
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: installing and updating only work once Arctiva is installed.")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.working !== "" || page.lastCode !== -2
            type: page.working !== "" ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: page.working !== ""
                ? (page.removing ? qsTr("Removing %1…") : qsTr("Installing %1…")).arg(page.lastName)
                : page.lastCode === 0
                    ? (page.removing ? qsTr("%1 has been removed.") : qsTr("%1 has been installed.")).arg(page.lastName)
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : qsTr("The operation failed (error code %1). The log below has the details; if it mentions dependencies, another program still needs these packages.").arg(page.lastCode)
        }

        InstallProgress {
            id: progress
            Layout.fillWidth: true
            active: page.working !== ""
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Groups of programs that you can add or remove at any time. They need an internet connection.")
        }

        Repeater {
            model: extrasBackend.extras
            delegate: Kirigami.AbstractCard {
                id: card
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Icon {
                        source: card.modelData.icon
                        Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                        Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                        Layout.alignment: Qt.AlignTop
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        Kirigami.Heading {
                            level: 3
                            text: card.modelData.name
                        }
                        QQC2.Label {
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: card.modelData.description
                        }
                    }
                    QQC2.BusyIndicator {
                        visible: page.working === card.modelData.id
                        running: visible
                    }
                    QQC2.Switch {
                        // Muestra el estado real: no cambia hasta que la operación termina.
                        checked: card.modelData.installed
                        enabled: !isLive && !page.busy
                        onToggled: {
                            checked = Qt.binding(() => card.modelData.installed)
                            page.toggle(card.modelData)
                        }
                        QQC2.ToolTip.visible: hovered
                        QQC2.ToolTip.text: card.modelData.installed ? qsTr("Remove") : qsTr("Install")
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("From the AUR")
        }

        Kirigami.AbstractCard {
            Layout.fillWidth: true
            contentItem: RowLayout {
                spacing: Kirigami.Units.largeSpacing
                Kirigami.Icon {
                    source: "internet-chat"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                    Layout.alignment: Qt.AlignTop
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    Kirigami.Heading {
                        level: 3
                        text: "Claude Desktop"
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        text: qsTr("Anthropic's desktop app (proprietary software). Arctiva does not host it: it is downloaded from Anthropic and packaged on your computer from the community's AUR recipe, which you review first.")
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        opacity: 0.7
                        visible: page.claudeInstalled
                        text: qsTr("Installed. Its updates come with the system ones, after you review them.")
                    }
                    QQC2.Label {
                        Layout.fillWidth: true
                        wrapMode: Text.WordWrap
                        opacity: 0.7
                        visible: !aurBackend.enabled && !page.claudeInstalled
                        text: qsTr("Turn on the AUR in Applications first to install it.")
                    }
                }
                QQC2.Button {
                    visible: !page.claudeInstalled
                    text: qsTr("Review and install")
                    icon.name: "document-edit"
                    enabled: !isLive && aurBackend.enabled && !page.busy && !aurBackend.busy
                    onClicked: applicationWindow().pageStack.layers.push(Qt.resolvedUrl("AurReviewPage.qml"), { pkgName: page.claudeName })
                }
            }
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Already included")
        }

        Kirigami.AbstractCard {
            Layout.fillWidth: true
            contentItem: RowLayout {
                Kirigami.Icon {
                    source: "printer"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("Printers: printing support is installed and active. Add your printer from the printer settings.")
                }
                QQC2.Button {
                    text: qsTr("Printer settings")
                    onClicked: extrasBackend.openSettings("kcm_printer_manager")
                }
            }
        }

        Kirigami.AbstractCard {
            Layout.fillWidth: true
            contentItem: RowLayout {
                Kirigami.Icon {
                    source: "security-high"
                    Layout.preferredWidth: Kirigami.Units.iconSizes.medium
                    Layout.preferredHeight: Kirigami.Units.iconSizes.medium
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: qsTr("Firewall: installed but turned off. Turn it on from the firewall settings, especially if you connect to networks you do not trust.")
                }
                QQC2.Button {
                    text: qsTr("Firewall settings")
                    onClicked: extrasBackend.openSettings("kcm_firewall")
                }
            }
        }

        LogView {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 14
            visible: text !== ""
        }
    }
}
