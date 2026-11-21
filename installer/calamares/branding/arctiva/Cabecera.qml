// SPDX-License-Identifier: GPL-3.0-or-later
// Título y frase de entrada de cada página.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Arctiva.js" as A

ColumnLayout {
    property alias titulo: etiquetaTitulo.text
    property alias intro: etiquetaIntro.text

    Layout.fillWidth: true
    spacing: 4

    Label {
        id: etiquetaTitulo
        Layout.fillWidth: true
        font.family: A.marca
        font.pixelSize: 24
        font.bold: true
        color: A.texto
        wrapMode: Text.WordWrap
    }
    Label {
        id: etiquetaIntro
        Layout.fillWidth: true
        visible: text !== ""
        color: A.secundario
        wrapMode: Text.WordWrap
    }
}
