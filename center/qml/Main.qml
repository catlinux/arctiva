// SPDX-License-Identifier: GPL-3.0-or-later
import QtQuick
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root

    title: qsTr("Arctiva Center")
    width: Kirigami.Units.gridUnit * 50
    height: Kirigami.Units.gridUnit * 34
    minimumWidth: Kirigami.Units.gridUnit * 30
    minimumHeight: Kirigami.Units.gridUnit * 20

    // Mismo orden que MODULES en arctiva_center/modules.py.
    readonly property var modules: [
        { title: qsTr("Welcome"), icon: "help-about" },
        { title: qsTr("Updates"), icon: "system-software-update" },
        { title: qsTr("Drivers"), icon: "computer" },
        { title: qsTr("Extras"), icon: "package-x-generic" }
    ]
    property int current: -1

    function show(index) {
        if (index === current)
            return
        current = index
        const page = index === 1 ? Qt.resolvedUrl("UpdatesPage.qml") : modulePage
        const props = { title: modules[index].title }
        if (pageStack.depth === 0)
            pageStack.push(page, props)
        else
            pageStack.replace(page, props)
    }

    // Mientras el ayudante trabaja, la ventana no se cierra: cortar pacman a medias es peor
    // que un fallo.
    onClosing: (close) => { if (helper.running) close.accepted = false }

    Component {
        id: modulePage
        Kirigami.Page {}
    }

    globalDrawer: Kirigami.GlobalDrawer {
        modal: false
        collapsible: false
        actions: [
            Kirigami.Action {
                text: root.modules[0].title
                icon.name: root.modules[0].icon
                checkable: true
                checked: root.current === 0
                onTriggered: root.show(0)
            },
            Kirigami.Action {
                text: root.modules[1].title
                icon.name: root.modules[1].icon
                checkable: true
                checked: root.current === 1
                onTriggered: root.show(1)
            },
            Kirigami.Action {
                text: root.modules[2].title
                icon.name: root.modules[2].icon
                checkable: true
                checked: root.current === 2
                onTriggered: root.show(2)
            },
            Kirigami.Action {
                text: root.modules[3].title
                icon.name: root.modules[3].icon
                checkable: true
                checked: root.current === 3
                onTriggered: root.show(3)
            }
        ]
    }

    Component.onCompleted: show(initialModule)
}
