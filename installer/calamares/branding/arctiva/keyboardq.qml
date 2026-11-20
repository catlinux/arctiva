// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Teclado» (keyboardq): distribución con búsqueda, variante, modelo y campo de prueba.
// Calamares aplica la distribución a la sesión live en cuanto se elige.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import io.calamares.core 1.0
import io.calamares.ui 1.0
import "Arctiva.js" as A

Item {
    id: page
    // Se recalcula al cambiar de idioma: Calamares retraduce entonces las etiquetas de los botones.
    // No todos los módulos llaman a onActivate() de la página (keyboardq y summaryq no).
    property string idioma: A.idioma(Qt.locale(), ViewManager.backLabel)

    readonly property var textos: ({
        titulo: { es: "Teclado", ca: "Teclat", en: "Keyboard" },
        intro: { es: "Comprueba que las teclas escriben lo que esperas.",
                 ca: "Comprova que les tecles escriuen el que esperes.",
                 en: "Check that the keys type what you expect." },
        buscar: { es: "Buscar distribución…", ca: "Cerca una distribució…", en: "Search layout…" },
        distribucion: { es: "Distribución", ca: "Distribució", en: "Layout" },
        variante: { es: "Variante", ca: "Variant", en: "Variant" },
        modelo: { es: "Modelo", ca: "Model", en: "Model" },
        prueba: { es: "Prueba aquí", ca: "Prova-ho aquí", en: "Try it here" }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    // Lista con selección resaltada; las filas que no coinciden con el filtro se pliegan.
    component Lista: ListView {
        id: lista
        property string filtro: ""
        clip: true
        currentIndex: model.currentIndex
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}

        // Al mostrarse la página la lista aún no tiene tamaño: se centra en el siguiente ciclo.
        function centrar() { Qt.callLater(function() { lista.positionViewAtIndex(lista.currentIndex, ListView.Center); }); }
        Component.onCompleted: centrar()
        onCountChanged: centrar()

        delegate: ItemDelegate {
            id: fila
            readonly property bool coincide: lista.filtro === ""
                || model.label.toLowerCase().indexOf(lista.filtro.toLowerCase()) >= 0
            width: lista.width
            height: coincide ? implicitHeight : 0
            visible: coincide
            highlighted: ListView.isCurrentItem
            onClicked: lista.model.currentIndex = index

            contentItem: Label {
                text: model.label
                color: fila.highlighted ? "#ffffff" : A.texto
                elide: Text.ElideRight
            }
            background: Rectangle {
                color: fila.highlighted ? A.acento : fila.hovered ? "#e9efff" : "transparent"
                radius: 6
            }
        }
    }

    Rectangle { anchors.fill: parent; color: A.fondo }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 24
        spacing: 16

        Cabecera {
            titulo: page.t("titulo")
            intro: page.t("intro")
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 16

            Tarjeta {
                Layout.fillHeight: true
                Layout.preferredWidth: 3
                Label { text: page.t("distribucion"); font.bold: true; color: A.texto }
                TextField {
                    id: buscar
                    Layout.fillWidth: true
                    placeholderText: page.t("buscar")
                }
                Lista {
                    id: distribuciones
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: config.keyboardLayoutsModel
                    filtro: buscar.text
                }
            }

            Tarjeta {
                Layout.fillHeight: true
                Layout.preferredWidth: 2
                Label { text: page.t("variante"); font.bold: true; color: A.texto }
                Lista {
                    id: variantes
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: config.keyboardVariantsModel
                }
            }
        }

        Tarjeta {
            GridLayout {
                Layout.fillWidth: true
                columns: 2
                columnSpacing: 16
                rowSpacing: 12

                Label { text: page.t("modelo"); font.bold: true; color: A.texto }
                ComboBox {
                    Layout.fillWidth: true
                    model: config.keyboardModelsModel
                    textRole: "label"
                    currentIndex: config.keyboardModelsModel.currentIndex
                    onActivated: config.keyboardModelsModel.currentIndex = currentIndex
                }

                Label { text: page.t("prueba"); font.bold: true; color: A.texto }
                TextField {
                    Layout.fillWidth: true
                    placeholderText: "Año, pingüino, acción, àéíòú, ç"
                }
            }
        }
    }
}
