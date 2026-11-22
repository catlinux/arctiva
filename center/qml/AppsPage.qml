// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Aplicaciones» (fase 6): buscador, categorías, destacadas y resultados.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    readonly property var backend: appsBackend
    readonly property var aur: aurBackend
    readonly property bool filtering: backend.query !== "" || backend.category !== ""

    function categoryName(id) {
        switch (id) {
        case "AudioVideo": return qsTr("Audio and video")
        case "Development": return qsTr("Development")
        case "Education": return qsTr("Education")
        case "Game": return qsTr("Games")
        case "Graphics": return qsTr("Graphics")
        case "Network": return qsTr("Internet")
        case "Office": return qsTr("Office")
        case "Science": return qsTr("Science")
        case "System": return qsTr("System")
        case "Utility": return qsTr("Utilities")
        default: return id
        }
    }

    Component.onCompleted: backend.load()

    Connections {
        target: backend
        function onUpdatesNeeded() { banner.visible = true }
    }

    Kirigami.Dialog {
        id: aurDialog
        title: qsTr("Turn on the AUR?")
        standardButtons: Kirigami.Dialog.NoButton
        customFooterActions: [
            Kirigami.Action {
                text: qsTr("Turn on")
                icon.name: "dialog-warning"
                enabled: understood.checked
                onTriggered: {
                    aur.setEnabled(true)
                    aurDialog.close()
                }
            },
            Kirigami.Action {
                text: qsTr("Cancel")
                icon.name: "dialog-cancel"
                onTriggered: aurDialog.close()
            }
        ]
        onClosed: understood.checked = false
        ColumnLayout {
            spacing: Kirigami.Units.largeSpacing
            QQC2.Label {
                Layout.preferredWidth: Kirigami.Units.gridUnit * 28
                wrapMode: Text.WordWrap
                text: qsTr("The AUR is a collection of recipes written by the community. Nobody at Arctiva or Arch Linux reviews them, they are built on your computer and they can run anything. Before every installation you will be shown the PKGBUILD so you can read it. An update of the system never touches them: you update them yourself, after reading what changed.")
            }
            QQC2.CheckBox {
                id: understood
                text: qsTr("I understand the risk")
            }
        }
    }

    component AppCard: Kirigami.AbstractCard {
        id: card
        required property var modelData
        Layout.fillWidth: true
        showClickFeedback: true
        onClicked: applicationWindow().pageStack.layers.push(Qt.resolvedUrl("AppDetailPage.qml"), { appId: card.modelData.id })
        contentItem: RowLayout {
            spacing: Kirigami.Units.largeSpacing
            Kirigami.Icon {
                source: card.modelData.icon
                Layout.preferredWidth: Kirigami.Units.iconSizes.large
                Layout.preferredHeight: Kirigami.Units.iconSizes.large
                Layout.alignment: Qt.AlignTop
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0
                Kirigami.Heading {
                    level: 4
                    text: card.modelData.name
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                QQC2.Label {
                    Layout.fillWidth: true
                    text: card.modelData.summary
                    elide: Text.ElideRight
                    maximumLineCount: 2
                    wrapMode: Text.WordWrap
                    color: Kirigami.Theme.disabledTextColor
                }
                RowLayout {
                    spacing: Kirigami.Units.smallSpacing
                    Repeater {
                        model: card.modelData.sources
                        delegate: Kirigami.Chip {
                            required property string modelData
                            text: modelData
                            checkable: false
                            closable: false
                            enabled: false
                        }
                    }
                    Kirigami.Icon {
                        visible: card.modelData.installed
                        source: "emblem-ok-symbolic"
                        Layout.preferredWidth: Kirigami.Units.iconSizes.small
                        Layout.preferredHeight: Kirigami.Units.iconSizes.small
                    }
                    QQC2.Label {
                        visible: card.modelData.installed
                        text: qsTr("Installed")
                    }
                }
            }
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: you can browse the applications, but installing only works once Arctiva is installed.")
        }

        Kirigami.InlineMessage {
            id: banner
            Layout.fillWidth: true
            visible: false
            type: Kirigami.MessageType.Warning
            showCloseButton: true
            text: qsTr("Your system has updates. To avoid a partial update, update first and then install.")
            actions: [
                Kirigami.Action {
                    text: qsTr("Update the system first")
                    icon.name: "system-software-update"
                    onTriggered: {
                        banner.visible = false
                        applicationWindow().show(2)
                    }
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.pending.id !== undefined && !banner.visible && !backend.busy
            type: Kirigami.MessageType.Information
            text: qsTr("Pending installation: %1").arg(backend.pending.name || "")
            actions: [
                Kirigami.Action {
                    text: qsTr("Install now")
                    icon.name: "run-build-install"
                    onTriggered: backend.continuePending()
                },
                Kirigami.Action {
                    text: qsTr("Cancel")
                    icon.name: "dialog-cancel"
                    onTriggered: backend.discardPending()
                }
            ]
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.error !== ""
            type: Kirigami.MessageType.Error
            text: qsTr("The catalogue could not be loaded: %1").arg(backend.error)
        }

        RowLayout {
            Layout.fillWidth: true
            Kirigami.SearchField {
                id: search
                Layout.fillWidth: true
                placeholderText: qsTr("Search applications…")
                enabled: backend.loaded
                onAccepted: {
                    backend.search(text)
                    aur.search(text)
                }
                onTextChanged: if (text === "" && backend.query !== "") {
                    backend.clearFilter()
                    aur.search("")
                }
            }
            QQC2.Button {
                visible: page.filtering
                text: qsTr("Back to start")
                icon.name: "go-home"
                onClicked: {
                    search.text = ""
                    backend.clearFilter()
                    aur.search("")
                }
            }
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: backend.loading
            spacing: Kirigami.Units.largeSpacing
            QQC2.BusyIndicator { running: backend.loading }
            QQC2.Label { text: qsTr("Loading the catalogue… the first time it can take a while.") }
        }

        Flow {
            Layout.fillWidth: true
            spacing: Kirigami.Units.smallSpacing
            visible: backend.loaded
            Repeater {
                model: backend.categories
                delegate: QQC2.Button {
                    required property var modelData
                    text: page.categoryName(modelData.id) + " (" + modelData.count + ")"
                    checkable: true
                    checked: backend.category === modelData.id
                    onClicked: {
                        search.text = ""
                        backend.selectCategory(modelData.id)
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            visible: backend.loaded
            text: backend.query !== "" ? qsTr("Results for “%1”").arg(backend.query)
                : backend.category !== "" ? page.categoryName(backend.category)
                : qsTr("Featured")
        }

        QQC2.Label {
            visible: backend.loaded && page.filtering && backend.results.length === 0
            text: qsTr("Nothing found. Try another word or a category.")
        }

        Kirigami.CardsLayout {
            Layout.fillWidth: true
            maximumColumns: 2
            Repeater {
                model: page.filtering ? backend.results : backend.featured
                delegate: AppCard {}
            }
        }

        Kirigami.Heading {
            level: 2
            visible: aur.enabled && aur.query !== ""
            text: qsTr("From the AUR (community, not reviewed)")
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: aur.enabled && aur.busy
            QQC2.BusyIndicator { running: parent.visible }
            QQC2.Label { text: qsTr("Searching the AUR…") }
        }

        QQC2.Label {
            visible: aur.enabled && aur.query !== "" && !aur.busy && aur.results.length === 0 && aur.error === ""
            text: qsTr("Nothing found in the AUR.")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: aur.enabled && aur.error !== ""
            type: Kirigami.MessageType.Error
            text: aur.error
        }

        Repeater {
            model: aur.enabled ? aur.results : []
            delegate: Kirigami.AbstractCard {
                id: aurCard
                required property var modelData
                Layout.fillWidth: true
                showClickFeedback: true
                onClicked: applicationWindow().pageStack.layers.push(Qt.resolvedUrl("AurReviewPage.qml"), { pkgName: aurCard.modelData.name })
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Kirigami.Chip {
                        text: "AUR"
                        checkable: false
                        closable: false
                        enabled: false
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Kirigami.Heading {
                            level: 4
                            text: aurCard.modelData.name + " " + aurCard.modelData.version
                        }
                        QQC2.Label {
                            Layout.fillWidth: true
                            text: aurCard.modelData.description
                            elide: Text.ElideRight
                            color: Kirigami.Theme.disabledTextColor
                        }
                    }
                    QQC2.Label {
                        text: qsTr("%1 votes").arg(aurCard.modelData.votes)
                        color: Kirigami.Theme.disabledTextColor
                    }
                }
            }
        }

        Kirigami.Separator { Layout.fillWidth: true }

        Kirigami.Heading {
            level: 3
            text: qsTr("AUR")
        }

        QQC2.Switch {
            text: qsTr("Show packages from the AUR (community, not reviewed)")
            checked: aur.enabled
            onToggled: {
                checked = Qt.binding(() => aur.enabled)
                if (aur.enabled)
                    aur.setEnabled(false)
                else
                    aurDialog.open()
            }
        }

        RowLayout {
            visible: aur.enabled
            QQC2.Button {
                text: qsTr("Check for AUR updates")
                icon.name: "view-refresh"
                enabled: !aur.busy
                onClicked: aur.checkUpdates()
            }
        }

        Repeater {
            model: aur.enabled ? aur.updates : []
            delegate: Kirigami.AbstractCard {
                id: upCard
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: upCard.modelData.name + ": " + upCard.modelData.old + " → " + upCard.modelData.new
                    }
                    QQC2.Button {
                        text: qsTr("Review and update")
                        icon.name: "document-edit"
                        onClicked: applicationWindow().pageStack.layers.push(Qt.resolvedUrl("AurReviewPage.qml"), { pkgName: upCard.modelData.name, isUpdate: true })
                    }
                }
            }
        }
    }
}
