// SPDX-License-Identifier: GPL-3.0-or-later
// Módulo «Juegos»: biblioteca, lanzadores con receta propia y buscador de instaladores de lutris.net.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property bool pendingOpen: false
    property string confirmSlug: ""
    readonly property var backend: gamesBackend

    function open() {
        if (backend.phase === "ready" && page.pendingOpen) {
            page.pendingOpen = false
            applicationWindow().pageStack.layers.push(Qt.resolvedUrl("GameInstallPage.qml"))
        }
    }

    Connections {
        target: backend
        function onChanged() { page.open() }
    }

    Kirigami.PromptDialog {
        id: confirm
        title: qsTr("Uninstall game")
        subtitle: qsTr("The game folder, including its saves inside the Wine prefix, will be deleted. This cannot be undone.")
        standardButtons: Kirigami.Dialog.Yes | Kirigami.Dialog.No
        onAccepted: backend.uninstall(page.confirmSlug)
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: isLive
            type: Kirigami.MessageType.Information
            text: qsTr("This is the live session: games can be browsed here, but installing only works once Arctiva is installed.")
        }

        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.error !== ""
            type: Kirigami.MessageType.Error
            text: backend.error
        }

        Kirigami.Heading {
            level: 2
            visible: backend.library.length > 0
            text: qsTr("Installed games")
        }

        Repeater {
            model: backend.library
            delegate: Kirigami.AbstractCard {
                id: gameCard
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    QQC2.Label {
                        Layout.fillWidth: true
                        text: gameCard.modelData.name
                        font.bold: true
                        elide: Text.ElideRight
                    }
                    QQC2.Button {
                        text: qsTr("Play")
                        icon.name: "media-playback-start"
                        enabled: !isLive
                        onClicked: {
                            backend.play(gameCard.modelData.slug)
                            applicationWindow().pageStack.layers.push(Qt.resolvedUrl("GameInstallPage.qml"), { playing: true })
                        }
                    }
                    QQC2.Button {
                        text: qsTr("Uninstall")
                        icon.name: "edit-delete"
                        onClicked: {
                            page.confirmSlug = gameCard.modelData.slug
                            confirm.open()
                        }
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Launchers")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Install a launcher first, then use it to download your games.")
        }

        Kirigami.CardsLayout {
            Layout.fillWidth: true
            maximumColumns: 2
            Repeater {
                model: backend.recipes
                delegate: Kirigami.AbstractCard {
                    id: recipeCard
                    required property var modelData
                    showClickFeedback: true
                    onClicked: {
                        page.pendingOpen = true
                        backend.prepareRecipe(recipeCard.modelData.slug)
                    }
                    contentItem: ColumnLayout {
                        QQC2.Label { text: recipeCard.modelData.name; font.bold: true }
                        QQC2.Label {
                            Layout.fillWidth: true
                            text: recipeCard.modelData.description
                            wrapMode: Text.WordWrap
                            opacity: 0.7
                        }
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Search installers")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            text: qsTr("Installers come from lutris.net, written by its community. Check the summary before installing.")
        }

        Kirigami.SearchField {
            Layout.fillWidth: true
            placeholderText: qsTr("Search games…")
            onAccepted: backend.search(text)
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            visible: backend.searching
            QQC2.BusyIndicator { running: backend.searching }
            QQC2.Label { text: qsTr("Searching…") }
        }

        Repeater {
            model: backend.results
            delegate: Kirigami.AbstractCard {
                id: resultCard
                required property var modelData
                Layout.fillWidth: true
                showClickFeedback: true
                onClicked: {
                    page.pendingOpen = true
                    backend.prepareOnline(resultCard.modelData.slug)
                }
                contentItem: RowLayout {
                    QQC2.Label { Layout.fillWidth: true; text: resultCard.modelData.name; elide: Text.ElideRight }
                    QQC2.Label { text: resultCard.modelData.year; opacity: 0.7 }
                }
            }
        }
    }
}
