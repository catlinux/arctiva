/* SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Navegación del instalador (maquetas del estudio E2): fondo blanco con una línea arriba,
 * «Cancelar» discreto a la izquierda y «Atrás» / «Siguiente» a la derecha, con «Siguiente»
 * en azul. Basada en calamares-navigation.qml de Calamares (GPL-3.0-or-later).
 */
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: navigationBar
    color: "#ffffff"
    height: 56

    Rectangle {
        anchors.top: parent.top
        width: parent.width
        height: 1
        color: "#dbe3f4"
    }

    component Boton: Button {
        id: boton
        property bool principal: false
        leftPadding: 18
        rightPadding: 18
        topPadding: 8
        bottomPadding: 8
        font.pixelSize: 14
        font.bold: principal
        contentItem: Text {
            // Las etiquetas de Calamares traen el «&» de los atajos de teclado de los widgets.
            text: boton.text.replace(/&(?!&)/g, "")
            font: boton.font
            color: !boton.enabled ? "#9aa6c2" : boton.principal ? "#ffffff" : boton.flat ? "#5b6b8c" : "#0d1730"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            radius: 7
            opacity: boton.enabled ? 1.0 : 0.45
            color: boton.principal ? (boton.down ? "#1a43b8" : "#1d4ed8") : boton.flat ? "transparent" : (boton.down ? "#e9efff" : "#ffffff")
            border.color: boton.principal ? "#1d4ed8" : boton.flat ? "transparent" : (boton.hovered ? "#3d86ff" : "#dbe3f4")
            border.width: 1
        }
    }

    // En la última página «Cancelar» pasa a ser «Hecho»: botón principal, a la derecha.
    readonly property bool ultimo: ViewManager.currentStepIndex === ViewManager.rowCount() - 1

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: 28
        anchors.rightMargin: 28
        spacing: 8

        Boton {
            flat: true
            visible: !navigationBar.ultimo && ViewManager.quitVisible
            text: ViewManager.quitLabel
            enabled: ViewManager.quitEnabled
            ToolTip.visible: hovered && ViewManager.quitTooltip !== ""
            ToolTip.delay: 1000
            ToolTip.text: ViewManager.quitTooltip
            onClicked: ViewManager.quit()
        }

        Item { Layout.fillWidth: true }

        Boton {
            text: ViewManager.backLabel
            enabled: ViewManager.backEnabled
            visible: ViewManager.backAndNextVisible && !navigationBar.ultimo
            onClicked: ViewManager.back()
        }
        Boton {
            principal: true
            text: ViewManager.nextLabel
            enabled: ViewManager.nextEnabled
            visible: ViewManager.backAndNextVisible && !navigationBar.ultimo
            onClicked: ViewManager.next()
        }
        Boton {
            principal: true
            visible: navigationBar.ultimo && ViewManager.quitVisible
            text: ViewManager.quitLabel
            enabled: ViewManager.quitEnabled
            onClicked: ViewManager.quit()
        }
    }
}
