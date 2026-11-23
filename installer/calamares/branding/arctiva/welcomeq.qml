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

    // Textos propios de los requisitos, por identificador. Calamares los genera una sola vez, en
    // el idioma de la sesión al arrancar, y no los retraduce al cambiar de idioma en esta página.
    // Si falta alguno (un requisito nuevo), se usa el texto de Calamares.
    readonly property var textosRequisito: ({
        storage_ok: { es: "Hay al menos 25 GiB libres en el disco.", ca: "Hi ha almenys 25 GiB lliures al disc.", en: "There is at least 25 GiB of free disk space." },
        storage_no: { es: "Hacen falta al menos 25 GiB libres en el disco.", ca: "Calen almenys 25 GiB lliures al disc.", en: "At least 25 GiB of free disk space is needed." },
        ram_ok: { es: "Hay al menos 4 GiB de memoria.", ca: "Hi ha almenys 4 GiB de memòria.", en: "There is at least 4 GiB of memory." },
        ram_no: { es: "Hacen falta al menos 4 GiB de memoria.", ca: "Calen almenys 4 GiB de memòria.", en: "At least 4 GiB of memory is needed." },
        power_ok: { es: "El equipo está conectado a la corriente.", ca: "L'ordinador està connectat al corrent.", en: "The computer is plugged in." },
        power_no: { es: "Conecta el equipo a la corriente antes de instalar.", ca: "Connecta l'ordinador al corrent abans d'instal·lar.", en: "Plug the computer in before installing." },
        internet_ok: { es: "Hay conexión a internet.", ca: "Hi ha connexió a internet.", en: "There is an internet connection." },
        internet_no: { es: "Sin conexión a internet: conéctate antes de instalar para añadir el kernel LTS, los perfiles y algunas aplicaciones (Kate, Okular, Gwenview, Spectacle…). Sin ella se instala solo lo que trae la ISO y esas aplicaciones se instalarán solas la primera vez que te conectes, con un aviso.",
                       ca: "Sense connexió a internet: connecta't abans d'instal·lar per afegir el nucli LTS, els perfils i algunes aplicacions (Kate, Okular, Gwenview, Spectacle…). Sense ella només s'instal·la el que porta la ISO i aquestes aplicacions s'instal·laran soles la primera vegada que et connectis, amb un avís.",
                       en: "No internet connection: connect before installing to add the LTS kernel, the profiles and some applications (Kate, Okular, Gwenview, Spectacle…). Without it only what the ISO includes is installed, and those applications will install themselves the first time you connect, with a notice." },
        root_ok: { es: "El instalador tiene los permisos necesarios.", ca: "L'instal·lador té els permisos necessaris.", en: "The installer has the permissions it needs." },
        root_no: { es: "El instalador debe ejecutarse como administrador.", ca: "L'instal·lador s'ha d'executar com a administrador.", en: "The installer must be run as administrator." },
        screen_ok: { es: "La pantalla es lo bastante grande.", ca: "La pantalla és prou gran.", en: "The screen is large enough." },
        screen_no: { es: "La pantalla es pequeña: algunas páginas pueden verse recortadas.", ca: "La pantalla és petita: algunes pàgines poden veure's retallades.", en: "The screen is small: some pages may look cut off." }
    })
    function textoRequisito(requisito) {
        var clave = requisito.name + (requisito.satisfied ? "_ok" : "_no");
        if (textosRequisito[clave] === undefined)
            return requisito.satisfied ? requisito.details : requisito.negatedText;
        return A.t(textosRequisito, clave, idioma);
    }

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
                            text: page.textoRequisito(model)
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
