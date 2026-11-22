// SPDX-License-Identifier: GPL-3.0-or-later
// Texto de solo lectura con barra de desplazamiento (registro de pacman, diff de un .pacnew).
// Un TextArea suelto con altura fija recorta lo que no cabe y no se puede desplazar.
import QtQuick
import QtQuick.Controls as QQC2

QQC2.ScrollView {
    id: view

    property alias text: area.text
    // Al añadir líneas se baja al final, para seguir el registro mientras corre.
    function append(line) {
        area.append(line)
        area.cursorPosition = area.length
    }
    function clear() { area.clear() }

    QQC2.TextArea {
        id: area
        readOnly: true
        wrapMode: TextEdit.WrapAnywhere
        font.family: "monospace"
    }
}
