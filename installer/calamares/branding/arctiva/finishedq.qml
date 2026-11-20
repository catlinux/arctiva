// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Fin» (finishedq): reiniciar ahora o seguir en la live; si la instalación falla,
// el mensaje de Calamares y sus detalles.
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
        titulo: { es: "Arctiva está instalada", ca: "Arctiva està instal·lada", en: "Arctiva is installed" },
        texto: { es: "Reinicia el equipo y retira el USB cuando se apague la pantalla. Arrancará Arctiva desde el disco.",
                 ca: "Reinicia l'ordinador i retira l'USB quan s'apagui la pantalla. Arrencarà Arctiva des del disc.",
                 en: "Restart the computer and remove the USB stick when the screen goes dark. Arctiva will start from the disk." },
        reiniciar: { es: "Reiniciar ahora", ca: "Reinicia ara", en: "Restart now" },
        seguir: { es: "Seguir probando", ca: "Continua provant", en: "Keep trying it" },
        falloT: { es: "La instalación no ha terminado", ca: "La instal·lació no ha acabat", en: "The installation did not finish" },
        fallo: { es: "Tu equipo no ha cambiado más allá de lo que indica el mensaje. Puedes cerrar el instalador y volver a intentarlo; el registro está en ~/.cache/calamares/session.log.",
                 ca: "L'ordinador no ha canviat més enllà del que indica el missatge. Pots tancar l'instal·lador i tornar-ho a provar; el registre és a ~/.cache/calamares/session.log.",
                 en: "Your computer has not changed beyond what the message says. You can close the installer and try again; the log is in ~/.cache/calamares/session.log." },
        cerrar: { es: "Cerrar el instalador", ca: "Tanca l'instal·lador", en: "Close the installer" }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    function onLeave() {}

    Rectangle { anchors.fill: parent; color: A.fondo }

    ColumnLayout {
        anchors.centerIn: parent
        width: Math.min(parent.width - 48, 620)
        spacing: 16
        visible: !config.failed

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 72
            Layout.preferredHeight: 72
            radius: 36
            color: "#e8f6ee"
            border.color: A.ok
            border.width: 2
            Label { anchors.centerIn: parent; text: "✓"; font.pixelSize: 36; font.bold: true; color: A.ok }
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: page.t("titulo")
            font.pixelSize: 26
            font.bold: true
            color: A.texto
            wrapMode: Text.WordWrap
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: page.t("texto")
            color: A.secundario
            wrapMode: Text.WordWrap
        }
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 12
            Button {
                text: page.t("seguir")
                onClicked: ViewManager.quit()
            }
            Button {
                id: reiniciar
                text: page.t("reiniciar")
                onClicked: config.doRestart(true)
                // Botón principal, como «Siguiente» en la navegación (el estilo del sistema no
                // distingue «highlighted»).
                contentItem: Label {
                    text: reiniciar.text
                    font.bold: true
                    color: "#ffffff"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    implicitWidth: 120
                    implicitHeight: 36
                    radius: 7
                    color: reiniciar.down ? "#1a43b8" : A.acento
                }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        contentWidth: availableWidth
        visible: config.failed

        ColumnLayout {
            width: parent.width
            spacing: 12

            Cabecera {
                titulo: page.t("falloT")
                intro: page.t("fallo")
            }
            Tarjeta {
                Label {
                    Layout.fillWidth: true
                    text: config.failureMessage
                    font.bold: true
                    color: A.error
                    wrapMode: Text.WordWrap
                }
                TextArea {
                    Layout.fillWidth: true
                    visible: config.failureDetails !== ""
                    text: config.failureDetails
                    readOnly: true
                    wrapMode: TextEdit.Wrap
                    font.family: "monospace"
                }
            }
            Button {
                text: page.t("cerrar")
                onClicked: ViewManager.quit()
            }
        }
    }
}
