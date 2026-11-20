// SPDX-License-Identifier: GPL-3.0-or-later
// Tarjeta blanca de las páginas del instalador; el contenido va dentro de una columna.
import QtQuick
import QtQuick.Layouts
import "Arctiva.js" as A

Rectangle {
    id: tarjeta
    default property alias contenido: columna.data
    property int relleno: 16

    Layout.fillWidth: true
    implicitHeight: columna.implicitHeight + 2 * relleno
    radius: 10
    color: A.tarjeta
    border.color: A.borde
    border.width: 1

    ColumnLayout {
        id: columna
        anchors.fill: parent
        anchors.margins: tarjeta.relleno
        spacing: 10
    }
}
