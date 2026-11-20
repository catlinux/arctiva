// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Bienvenida» (welcomeq): idioma del instalador, requisitos y enlaces.
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
        titulo: { es: "Te damos la bienvenida a Arctiva", ca: "Et donem la benvinguda a Arctiva", en: "Welcome to Arctiva" },
        intro: { es: "En unos minutos tendrás el mismo escritorio que estás probando, instalado en tu equipo. Puedes volver atrás en cualquier paso hasta pulsar «Instalar».",
                 ca: "En uns minuts tindràs el mateix escriptori que estàs provant, instal·lat al teu ordinador. Pots tornar enrere en qualsevol pas fins que premis «Instal·la».",
                 en: "In a few minutes you will have the same desktop you are trying, installed on your computer. You can go back at any step until you press \"Install\"." },
        idiomaInstalador: { es: "Idioma del instalador", ca: "Idioma de l'instal·lador", en: "Installer language" },
        requisitos: { es: "Requisitos", ca: "Requisits", en: "Requirements" },
        comprobando: { es: "Comprobando el equipo…", ca: "S'està comprovant l'ordinador…", en: "Checking the computer…" },
        notas: { es: "Notas de la versión", ca: "Notes de la versió", en: "Release notes" },
        ayuda: { es: "Ayuda", ca: "Ajuda", en: "Help" },
        problemas: { es: "Problemas conocidos", ca: "Problemes coneguts", en: "Known issues" }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    function onActivate() {
        recargarRequisitos();
    }

    // El modelo de requisitos se rellena desde otro hilo y la vista puede perderse el aviso de
    // reinicio: se vuelve a enlazar al terminar la comprobación.
    function recargarRequisitos() {
        requisitos.model = null;
        requisitos.model = config.requirementsModel;
    }
    Connections {
        target: config.requirementsModel
        function onSatisfiedRequirementsChanged() { page.recargarRequisitos(); }
        function onSatisfiedMandatoryChanged() { page.recargarRequisitos(); }
        function onProgressMessageChanged() { page.recargarRequisitos(); }
    }
    Timer {
        interval: 1000
        repeat: true
        running: requisitos.count === 0
        onTriggered: page.recargarRequisitos()
    }

    Rectangle { anchors.fill: parent; color: A.fondo }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 16

            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 96
                Layout.preferredHeight: 96
                source: "file:" + Branding.imagePath(Branding.ProductLogo)
                sourceSize.width: 192
                sourceSize.height: 192
                fillMode: Image.PreserveAspectFit
            }

            Cabecera {
                titulo: page.t("titulo")
                intro: page.t("intro")
            }

            Tarjeta {
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 12
                    Label { text: page.t("idiomaInstalador"); font.bold: true; color: A.texto }
                    ComboBox {
                        id: idiomas
                        Layout.fillWidth: true
                        model: config.languagesModel
                        textRole: "label"
                        currentIndex: config.localeIndex
                        onActivated: {
                            config.localeIndex = currentIndex;
                        }
                    }
                }
            }

            Tarjeta {
                Label { text: page.t("requisitos"); font.bold: true; color: A.texto }
                Label {
                    visible: requisitos.count === 0
                    text: page.t("comprobando")
                    color: A.secundario
                }
                Repeater {
                    id: requisitos
                    model: config.requirementsModel
                    delegate: RowLayout {
                        Layout.fillWidth: true
                        spacing: 10
                        // Símbolo además del color (accesibilidad).
                        Label {
                            Layout.alignment: Qt.AlignTop
                            Layout.preferredWidth: 18
                            text: model.satisfied ? "✓" : model.mandatory ? "✕" : "!"
                            font.bold: true
                            color: model.satisfied ? A.ok : model.mandatory ? A.error : A.aviso
                        }
                        Label {
                            Layout.fillWidth: true
                            // «name» es el identificador interno (storage, ram…); «details», el texto.
                            text: model.satisfied ? model.details : model.negatedText
                            wrapMode: Text.WordWrap
                            color: A.texto
                        }
                    }
                }
            }

            RowLayout {
                Layout.alignment: Qt.AlignHCenter
                spacing: 8
                Button {
                    flat: true
                    visible: config.releaseNotesUrl !== ""
                    text: page.t("notas")
                    onClicked: Qt.openUrlExternally(config.releaseNotesUrl)
                }
                Button {
                    flat: true
                    visible: config.supportUrl !== ""
                    text: page.t("ayuda")
                    onClicked: Qt.openUrlExternally(config.supportUrl)
                }
                Button {
                    flat: true
                    visible: config.knownIssuesUrl !== ""
                    text: page.t("problemas")
                    onClicked: Qt.openUrlExternally(config.knownIssuesUrl)
                }
            }
        }
    }
}
