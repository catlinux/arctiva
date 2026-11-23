// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Actualizaciones» (D-08): noticias que bloquean, paquetes delicados, registro real,
// errores explicados, .pacnew y aviso de reinicio. Una sola actualización recorre pacman, Flatpak y,
// si está activado, el AUR (cuya revisión se pide antes de empezar).
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property int lastCode: -2
    property string operation: ""
    property bool showLog: false
    property bool working: false
    property string stage: ""
    property int aurCode: -2
    property bool awaitingReview: false
    readonly property bool busy: helper.running || updatesBackend.checking || working || aurBackend.busy
    readonly property bool flatpakIncluded: updatesBackend.includeFlatpak
    readonly property bool aurIncluded: aurBackend.enabled && updatesBackend.includeAur
    readonly property var allUpdates: updatesBackend.updates
        .map(u => Object.assign({ source: "" }, u))
        .concat(flatpakIncluded ? updatesBackend.flatpakUpdates.map(u => ({ name: u.name, old: "", new: u.new, delicate: false, source: "Flatpak" })) : [])
        .concat(aurIncluded ? aurBackend.updates.map(u => ({ name: u.name, old: u.old, new: u.new, delicate: false, source: "AUR" })) : [])

    function checkAll() {
        updatesBackend.check()
        if (aurIncluded)
            aurBackend.checkUpdates()
    }

    function runHelper(op, args) {
        page.operation = op
        if (op === "update") {
            page.flickable.contentY = 0
            log.clear()
            page.lastCode = -2
            page.aurCode = -2
            page.showLog = true
            page.working = true
            updatesBackend.updateStarted()
        }
        helper.run(op, args)
    }

    // El AUR se revisa antes de tocar nada: así el resto va sin interrupciones y lo que se
    // construye es exactamente lo que se ha leído.
    function beginUpdate() {
        if (aurIncluded && aurBackend.updates.length > 0 && !aurBackend.approved) {
            awaitingReview = true
            applicationWindow().pageStack.layers.push(Qt.resolvedUrl("AurReviewPage.qml"), { batch: true, isUpdate: true })
        } else {
            startUpdate()
        }
    }

    function startUpdate() {
        awaitingReview = false
        if (updatesBackend.updates.length > 0) {
            runHelper("update", [])
            return
        }
        page.flickable.contentY = 0
        log.clear()
        page.lastCode = 0
        page.aurCode = -2
        page.showLog = true
        page.working = true
        updatesBackend.updateStarted()
        afterSystem()
    }

    function afterSystem() {
        if (flatpakIncluded) {
            stage = "flatpak"
            updatesBackend.updateFlatpak()
        } else {
            runAur()
        }
    }

    function runAur() {
        if (aurBackend.approved) {
            stage = "aur"
            if (!aurBackend.install()) {
                aurCode = 75
                finishAll()
            }
        } else {
            finishAll()
        }
    }

    function finishAll() {
        stage = ""
        working = false
        checkAll()
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
            onTriggered: page.checkAll()
        },
        Kirigami.Action {
            text: qsTr("Update")
            icon.name: "system-software-update"
            enabled: !isLive && !page.busy && !updatesBackend.blocked && page.allUpdates.length > 0
            onTriggered: page.beginUpdate()
        }
    ]

    Component.onCompleted: page.checkAll()

    Connections {
        target: helper
        function onLine(text) { log.append(text) }
        function onFinished(code) {
            if (page.operation === "update") {
                page.lastCode = code
                updatesBackend.updateFinished(code, log.text)
                if (code === 0)
                    page.afterSystem()
                else
                    page.working = false
            } else if (page.operation === "pacnew") {
                updatesBackend.refreshPacnew()
            }
            page.operation = ""
        }
    }

    Connections {
        target: updatesBackend
        function onFlatpakLine(text) { log.append(text) }
        // Tras Flatpak sigue el AUR y al final se vuelve a comprobar: lista y noticias ya no son las de antes.
        function onFlatpakFinished(code) {
            if (page.stage === "flatpak")
                page.runAur()
        }
    }

    Connections {
        target: aurBackend
        function onLog(text) { if (page.stage === "aur") log.append(text) }
        function onFinished(code) {
            if (page.stage !== "aur")
                return
            page.aurCode = code
            page.finishAll()
        }
        function onApprovedChanged() {
            if (aurBackend.approved && page.awaitingReview)
                page.startUpdate()
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

        // Resultado de la última actualización y, si falló, qué significa.
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.working || page.lastCode !== -2
            type: page.working ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive
                : Kirigami.MessageType.Error
            text: page.working ? qsTr("Updating…")
                : page.lastCode === 0 ? qsTr("The system is up to date.")
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : updatesBackend.explanation.message !== undefined ? updatesBackend.explanation.message
                : qsTr("The update failed (error code %1). The log below has the details.").arg(page.lastCode)
            actions: [
                Kirigami.Action {
                    visible: !page.working && updatesBackend.explanation.action === "keyring-first"
                    text: qsTr("Update the keyring first")
                    onTriggered: page.runHelper("update", ["--keyring-first"])
                },
                Kirigami.Action {
                    visible: !page.working && updatesBackend.explanation.action === "retry"
                    text: qsTr("Try again")
                    onTriggered: page.runHelper("update", [])
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.aurCode !== -2 && !page.working
            type: page.aurCode === 0 ? Kirigami.MessageType.Positive : Kirigami.MessageType.Error
            text: page.aurCode === 0 ? qsTr("The AUR packages were updated.")
                : (page.aurCode === 126 || page.aurCode === 127) ? qsTr("Authorization cancelled")
                : qsTr("The AUR update failed (error code %1). The log below has the details.").arg(page.aurCode)
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
                : page.allUpdates.length === 0 ? qsTr("No updates available")
                // Sin numerus de Qt: el inglés no tiene catálogo y mostraría el texto fuente.
                : page.allUpdates.length === 1 ? qsTr("1 update available")
                : qsTr("%1 updates available").arg(page.allUpdates.length)
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            visible: updatesBackend.updates.some(u => u.delicate)
            text: qsTr("Packages marked as sensitive affect starting the system or the desktop. A snapshot is taken before updating: if something goes wrong, you can boot it from the GRUB menu.")
        }

        Repeater {
            model: page.allUpdates
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
                    text: modelData.old !== "" ? modelData.old + " → " + modelData.new : modelData.new
                }
                QQC2.Label {
                    visible: modelData.source !== ""
                    text: modelData.source
                    color: Kirigami.Theme.disabledTextColor
                }
                QQC2.Label {
                    visible: modelData.delicate
                    text: qsTr("sensitive")
                    color: Kirigami.Theme.neutralTextColor
                }
            }
        }

        // Qué se actualiza junto con el sistema.
        Kirigami.Heading {
            level: 3
            text: qsTr("Update sources")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            opacity: 0.7
            text: qsTr("The Arch repositories are always updated. Choose what else is updated at the same time.")
        }

        QQC2.Switch {
            text: qsTr("Flatpak applications")
            checked: updatesBackend.includeFlatpak
            enabled: !page.busy
            onToggled: updatesBackend.setIncludeFlatpak(checked)
        }

        QQC2.Switch {
            visible: aurBackend.enabled
            text: qsTr("AUR packages (you review their changes before they are built)")
            checked: updatesBackend.includeAur
            enabled: !page.busy
            onToggled: {
                updatesBackend.setIncludeAur(checked)
                if (checked)
                    aurBackend.checkUpdates()
            }
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            opacity: 0.7
            visible: !aurBackend.enabled
            text: qsTr("To update AUR packages here too, turn on the AUR in Applications.")
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
