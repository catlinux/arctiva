// SPDX-License-Identifier: GPL-3.0-or-later
// Arctiva Games: biblioteca de juegos instalados, lanzadores con receta propia y buscador de instaladores.
import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ScrollablePage {
    id: page

    property bool pendingOpen: false
    property string confirmSlug: ""
    readonly property var backend: gamesBackend

    title: qsTr("Arctiva Games")

    function open() {
        if (backend.phase === "ready" && page.pendingOpen) {
            page.pendingOpen = false
            applicationWindow().pageStack.layers.push(Qt.resolvedUrl("GameInstallPage.qml"))
        }
    }

    // Color estable por nombre, para el distintivo de cada juego o lanzador.
    function badgeColor(text) {
        var h = 0
        for (var i = 0; i < text.length; i++)
            h = (h * 31 + text.charCodeAt(i)) % 360
        return Qt.hsla(h / 360, 0.55, 0.42, 1)
    }

    function installed(slug) {
        return backend.library.some(g => g.slug === slug)
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

    component Badge: Rectangle {
        property string label: ""
        implicitWidth: Kirigami.Units.gridUnit * 3
        implicitHeight: Kirigami.Units.gridUnit * 3
        radius: Kirigami.Units.largeSpacing
        color: page.badgeColor(label)
        QQC2.Label {
            anchors.centerIn: parent
            text: parent.label.length > 0 ? parent.label.charAt(0).toUpperCase() : ""
            color: "white"
            font.bold: true
            font.pointSize: Kirigami.Theme.defaultFont.pointSize * 1.8
        }
    }

    ColumnLayout {
        spacing: Kirigami.Units.largeSpacing

        ColumnLayout {
            Layout.fillWidth: true
            Layout.bottomMargin: Kirigami.Units.smallSpacing
            Kirigami.Heading { level: 1; text: qsTr("Your Windows games on Linux") }
            QQC2.Label {
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
                opacity: 0.75
                text: qsTr("Install a launcher, sign in, and play. Every step is shown and logged, and you choose how it runs.")
            }
        }

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

        // GE-Proton viene «de serie»: se instala o actualiza solo al abrir Arctiva Games.
        Kirigami.InlineMessage {
            Layout.fillWidth: true
            visible: backend.protonState === "working" || backend.protonState === "failed"
            type: backend.protonState === "failed" ? Kirigami.MessageType.Warning : Kirigami.MessageType.Information
            text: backend.protonState === "working"
                ? qsTr("Preparing Proton-Wineland, the runner most launchers need (a download of about 350 MB, repeated at most once a week when there is a new version)… %1 %").arg(Math.round(backend.protonProgress * 100))
                : qsTr("Proton-Wineland could not be prepared (%1). You can still install with another runner; it will be tried again next time.").arg(backend.protonDetail)
            actions: Kirigami.Action {
                visible: backend.protonState === "failed"
                text: qsTr("Try again")
                icon.name: "view-refresh"
                onTriggered: backend.ensureProton()
            }
        }

        Kirigami.Heading {
            level: 2
            text: qsTr("Installed games")
        }

        Kirigami.PlaceholderMessage {
            Layout.fillWidth: true
            visible: backend.library.length === 0
            icon.name: "applications-games"
            text: qsTr("No games installed yet")
            explanation: qsTr("Pick a launcher below to get started.")
        }

        Repeater {
            model: backend.library
            delegate: Kirigami.AbstractCard {
                id: gameCard
                required property var modelData
                Layout.fillWidth: true
                contentItem: RowLayout {
                    spacing: Kirigami.Units.largeSpacing
                    Badge { label: gameCard.modelData.name }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 0
                        Kirigami.Heading { level: 3; text: gameCard.modelData.name; elide: Text.ElideRight; Layout.fillWidth: true }
                        QQC2.Label { text: qsTr("Runner: %1").arg(gameCard.modelData.runner); opacity: 0.7 }
                    }
                    QQC2.Button {
                        text: qsTr("Play")
                        icon.name: "media-playback-start"
                        highlighted: true
                        enabled: !isLive
                        onClicked: {
                            backend.play(gameCard.modelData.slug)
                            applicationWindow().pageStack.layers.push(Qt.resolvedUrl("GameInstallPage.qml"), { playing: true })
                        }
                    }
                    QQC2.ToolButton {
                        icon.name: "overflow-menu"
                        onClicked: menu.popup()
                        QQC2.Menu {
                            id: menu
                            QQC2.MenuItem {
                                text: qsTr("Add to the application menu")
                                checkable: true
                                checked: gameCard.modelData.menu
                                onToggled: backend.setShortcut(gameCard.modelData.slug, "menu", checked)
                            }
                            QQC2.MenuItem {
                                text: qsTr("Add to the desktop")
                                checkable: true
                                checked: gameCard.modelData.desktop
                                onToggled: backend.setShortcut(gameCard.modelData.slug, "desktop", checked)
                            }
                            QQC2.MenuSeparator {}
                            QQC2.MenuItem {
                                text: qsTr("Uninstall")
                                icon.name: "edit-delete"
                                onTriggered: {
                                    page.confirmSlug = gameCard.modelData.slug
                                    confirm.open()
                                }
                            }
                        }
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            Layout.topMargin: Kirigami.Units.largeSpacing
            text: qsTr("Launchers")
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
                    contentItem: RowLayout {
                        spacing: Kirigami.Units.largeSpacing
                        Badge { label: recipeCard.modelData.name }
                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 0
                            Kirigami.Heading { level: 3; text: recipeCard.modelData.name; elide: Text.ElideRight; Layout.fillWidth: true }
                            QQC2.Label { text: recipeCard.modelData.description; opacity: 0.7 }
                        }
                        Kirigami.Icon {
                            visible: page.installed(recipeCard.modelData.slug)
                            source: "emblem-ok-symbolic"
                            implicitWidth: Kirigami.Units.iconSizes.smallMedium
                            implicitHeight: Kirigami.Units.iconSizes.smallMedium
                        }
                        QQC2.Button {
                            text: page.installed(recipeCard.modelData.slug) ? qsTr("Reinstall") : qsTr("Install")
                            onClicked: {
                                page.pendingOpen = true
                                backend.prepareRecipe(recipeCard.modelData.slug)
                            }
                        }
                    }
                }
            }
        }

        Kirigami.Heading {
            level: 2
            Layout.topMargin: Kirigami.Units.largeSpacing
            text: qsTr("Search installers")
        }

        QQC2.Label {
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
            opacity: 0.75
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
                    spacing: Kirigami.Units.largeSpacing
                    Badge { label: resultCard.modelData.name; implicitWidth: Kirigami.Units.gridUnit * 2; implicitHeight: Kirigami.Units.gridUnit * 2 }
                    QQC2.Label { Layout.fillWidth: true; text: resultCard.modelData.name; elide: Text.ElideRight }
                    QQC2.Label { text: resultCard.modelData.year; opacity: 0.7 }
                }
            }
        }
    }
}
