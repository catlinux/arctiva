/* SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Barra lateral del instalador (maquetas del estudio E2): degradado azul noche, símbolo de
 * Arctiva y los pasos numerados; el actual en una píldora azul con borde cian y los ya
 * hechos con una marca. Basada en calamares-sidebar.qml de Calamares (GPL-3.0-or-later).
 */
import io.calamares.ui 1.0
import io.calamares.core 1.0

import QtQuick
import QtQuick.Layouts

Rectangle {
    id: sideBar
    anchors.fill: parent
    gradient: Gradient {
        orientation: Gradient.Vertical
        GradientStop { position: 0.0; color: "#0d1730" }
        GradientStop { position: 0.6; color: "#0b1f5c" }
        GradientStop { position: 1.0; color: "#0b2d8f" }
    }

    // El modelo de pasos no avisa cuando se cambia el idioma en la bienvenida, pero las etiquetas
    // de los botones sí: al cambiar, se vuelve a cargar el modelo para traducir los nombres.
    readonly property string etiqueta: ViewManager.backLabel
    onEtiquetaChanged: {
        pasos.model = null;
        pasos.model = ViewManager;
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 2

        RowLayout {
            Layout.bottomMargin: 18
            Layout.leftMargin: 6
            spacing: 10

            Image {
                source: "file:/" + Branding.imagePath(Branding.ProductLogo)
                sourceSize.width: 40
                sourceSize.height: 40
                Layout.preferredWidth: 40
                Layout.preferredHeight: 40
            }
            ColumnLayout {
                spacing: 0
                Text {
                    text: Branding.string(Branding.ShortProductName)
                    color: "#ffffff"
                    font.pixelSize: 18
                    font.bold: true
                }
                Text {
                    text: Branding.string(Branding.ShortVersion)
                    color: "#8fa3cf"
                    font.pixelSize: 11
                }
            }
        }

        Repeater {
            id: pasos
            model: ViewManager
            Rectangle {
                readonly property bool actual: index === ViewManager.currentStepIndex
                readonly property bool hecho: index < ViewManager.currentStepIndex

                Layout.fillWidth: true
                height: 36
                radius: 8
                color: actual ? "#1d4ed8" : "transparent"
                border.color: actual ? "#4cc3ff" : "transparent"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 10

                    Rectangle {
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 22
                        radius: 11
                        color: actual ? "#ffffff" : hecho ? "#16306f" : "transparent"
                        border.color: actual ? "#ffffff" : hecho ? "#16306f" : "#3a4f86"
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            text: hecho ? "✓" : (index + 1)
                            color: actual ? "#1d4ed8" : hecho ? "#4cc3ff" : "#8fa3cf"
                            font.pixelSize: 11
                            font.bold: actual
                        }
                    }
                    Text {
                        Layout.fillWidth: true
                        text: display
                        color: actual ? "#ffffff" : "#c3cee8"
                        font.pixelSize: 13
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // «Acerca de» y, con -d, la ventana de depuración.
        RowLayout {
            Layout.fillWidth: true
            Layout.leftMargin: 8
            spacing: 14
            Text {
                text: qsTr("About")
                color: "#7187b8"
                font.pixelSize: 11
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: debug.about()
                }
            }
            Text {
                visible: debug.enabled
                text: qsTr("Debug")
                color: "#7187b8"
                font.pixelSize: 11
                MouseArea {
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: debug.toggle()
                }
            }
        }
    }
}
