// SPDX-License-Identifier: GPL-3.0-or-later
// Revisión de un paquete del AUR (D-07): hay que leer el PKGBUILD antes de instalar.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property string pkgName
    property bool isUpdate: false
    property bool working: false
    property int lastCode: -2
    readonly property var backend: aurBackend
    readonly property var data: backend.review
    readonly property var packages: data.packages || []

    title: pkgName

    function warningText(key) {
        switch (key) {
        case "orphan": return qsTr("It has no maintainer: nobody is looking after it.")
        case "new": return qsTr("It was published less than 30 days ago.")
        case "out-of-date": return qsTr("It is flagged as out of date.")
        case "few-votes": return qsTr("It has fewer than 10 votes: few people use it.")
        default: return key
        }
    }

    function dateText(seconds) {
        return seconds > 0 ? new Date(seconds * 1000).toLocaleDateString(Qt.locale(), Locale.ShortFormat) : "—"
    }

    Component.onCompleted: backend.prepare(pkgName, isUpdate)

    Connections {
        target: backend
        function onLog(text) { if (page.working) log.append(text) }
        function onFinished(code) {
            page.working = false
            page.lastCode = code
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: true
            type: Kirigami.MessageType.Warning
            text: qsTr("AUR packages are made by the community and nobody at Arctiva or Arch Linux has reviewed them. They are built on your computer and can run anything. Read the PKGBUILD before installing.")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.error !== ""
            type: Kirigami.MessageType.Error
            text: backend.error
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: backend.busy && !page.working
            QQC2.BusyIndicator { running: parent.visible }
            QQC2.Label { text: qsTr("Downloading and preparing the package for review…") }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: (data.unresolved || []).length > 0
            type: Kirigami.MessageType.Error
            text: qsTr("These dependencies could not be found, so it cannot be installed: %1").arg((data.unresolved || []).join(", "))
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            visible: (data.repoDeps || []).length > 0
            text: qsTr("It will also install from the Arch repositories: %1").arg((data.repoDeps || []).join(", "))
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            visible: packages.length > 1
            font.bold: true
            text: qsTr("It needs %1 packages from the AUR, built in this order (each one is shown below): %2")
                .arg(packages.length).arg(packages.map(p => p.name).join(" → "))
        }

        Repeater {
            model: page.packages
            delegate: ColumnLayout {
                id: entry
                required property var modelData
                Layout.fillWidth: true
                spacing: Kirigami.Units.smallSpacing

                Kirigami.Separator { Layout.fillWidth: true }
                Kirigami.Heading {
                    level: 2
                    text: entry.modelData.name + " " + entry.modelData.version
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    text: entry.modelData.description
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    wrapMode: Text.WordWrap
                    color: Kirigami.Theme.disabledTextColor
                    text: qsTr("Maintainer: %1 · Votes: %2 · Popularity: %3 · First published: %4 · Last updated: %5")
                        .arg(entry.modelData.maintainer || qsTr("none"))
                        .arg(entry.modelData.votes).arg(entry.modelData.popularity)
                        .arg(page.dateText(entry.modelData.firstSubmitted)).arg(page.dateText(entry.modelData.lastModified))
                }
                Repeater {
                    model: entry.modelData.warnings
                    delegate: Kirigami.InlineMessage {
                        required property string modelData
                        Layout.fillWidth: true
                        visible: true
                        type: Kirigami.MessageType.Error
                        text: page.warningText(modelData)
                    }
                }
                Kirigami.Heading {
                    level: 4
                    visible: entry.modelData.diff !== ""
                    text: qsTr("Changes since the version you have")
                }
                LogView {
                    Layout.fillWidth: true
                    Layout.preferredHeight: Kirigami.Units.gridUnit * 10
                    visible: entry.modelData.diff !== ""
                    Component.onCompleted: text = entry.modelData.diff
                }
                Repeater {
                    model: entry.modelData.files
                    delegate: ColumnLayout {
                        id: fileBlock
                        required property var modelData
                        Layout.fillWidth: true
                        Kirigami.Heading {
                            level: 4
                            text: fileBlock.modelData.name
                        }
                        LogView {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Kirigami.Units.gridUnit * 16
                            Component.onCompleted: text = fileBlock.modelData.text
                        }
                    }
                }
            }
        }

        QQC2.CheckBox {
            id: reviewed
            visible: page.packages.length > 0
            enabled: !page.working
            text: page.isUpdate ? qsTr("I have reviewed the changes and the PKGBUILD") : qsTr("I have reviewed the PKGBUILD")
        }

        RowLayout {
            visible: page.packages.length > 0
            QQC2.Button {
                text: page.isUpdate ? qsTr("Update") : qsTr("Install")
                icon.name: "run-build-install"
                highlighted: true
                enabled: reviewed.checked && !isLive && !page.working && !backend.busy && (data.unresolved || []).length === 0
                onClicked: {
                    log.clear()
                    page.lastCode = -2
                    page.working = true
                    backend.install()
                }
            }
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: page.working || page.lastCode !== -2
            type: page.working ? Kirigami.MessageType.Information
                : page.lastCode === 0 ? Kirigami.MessageType.Positive : Kirigami.MessageType.Error
            text: page.working ? qsTr("Building and installing… this can take a few minutes.")
                : page.lastCode === 0 ? qsTr("Installed.")
                : (page.lastCode === 126 || page.lastCode === 127) ? qsTr("Authorization cancelled")
                : qsTr("It failed (error code %1). The log below has the details.").arg(page.lastCode)
        }

        LogView {
            id: log
            Layout.fillWidth: true
            Layout.preferredHeight: Kirigami.Units.gridUnit * 12
            visible: page.working || page.lastCode !== -2
        }
    }
}
