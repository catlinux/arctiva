// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Resumen» (summaryq): una tarjeta por paso con lo que hará, en el idioma de Calamares,
// y el aviso de copia de seguridad. Hasta pulsar «Instalar» no se toca el disco.
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
        titulo: { es: "Resumen", ca: "Resum", en: "Summary" },
        intro: { es: "Revisa antes de instalar. Hasta pulsar «Instalar» no se cambia nada.",
                 ca: "Revisa-ho abans d'instal·lar. Fins que no premis «Instal·la» no es canvia res.",
                 en: "Review before installing. Nothing changes until you press \"Install\"." },
        perfilesT: { es: "Perfiles", ca: "Perfils", en: "Profiles" },
        basico: { es: "Básico", ca: "Bàsic", en: "Basic" },
        juegos: { es: "Juegos", ca: "Jocs", en: "Gaming" },
        oficina: { es: "Oficina", ca: "Oficina", en: "Office" },
        perfilesNota: { es: "Se descargan al instalar; sin conexión se instala solo Básico y se pueden añadir después. Algunas aplicaciones básicas (Kate, Okular, Gwenview, Spectacle…) también se descargan: sin conexión se instalarán la primera vez que te conectes, con un aviso.",
                        ca: "Es baixen en instal·lar; sense connexió s'instal·la només Bàsic i es poden afegir després. Algunes aplicacions bàsiques (Kate, Okular, Gwenview, Spectacle…) també es baixen: sense connexió s'instal·laran la primera vegada que et connectis, amb un avís.",
                        en: "Downloaded during installation; offline, only Basic is installed and you can add the rest later. Some basic applications (Kate, Okular, Gwenview, Spectacle…) are also downloaded: offline, they will be installed the first time you connect, with a notice." },
        copiaT: { es: "Haz una copia de lo importante", ca: "Fes una còpia del que és important", en: "Back up what matters" },
        copia: { es: "Cambiar las particiones es seguro casi siempre, pero un corte de luz a mitad podría dañarlas.",
                 ca: "Canviar les particions és segur gairebé sempre, però un tall de llum a mitges les podria malmetre.",
                 en: "Changing partitions is almost always safe, but a power cut halfway through could damage them." }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    // packagechooser no aporta línea al resumen: se deduce de las operaciones de paquetes que
    // deja en GlobalStorage (steam identifica Juegos; libreoffice-fresh, Oficina).
    property var extras: []
    function leerPerfiles() {
        var ops = Global.value("packageOperations");
        var paquetes = [];
        if (ops) {
            for (var i = 0; i < ops.length; i++) {
                var lista = ops[i]["install"] || [];
                for (var j = 0; j < lista.length; j++)
                    paquetes.push(lista[j]);
            }
        }
        var r = [];
        if (paquetes.indexOf("steam") >= 0) r.push(t("juegos"));
        if (paquetes.indexOf("libreoffice-fresh") >= 0) r.push(t("oficina"));
        extras = r;
    }
    // La página se crea al arrancar y no recibe aviso al activarse: se relee mientras exista.
    Timer {
        interval: 500
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: page.leerPerfiles()
    }

    Rectangle { anchors.fill: parent; color: A.fondo }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 12

            Cabecera {
                titulo: page.t("titulo")
                intro: page.t("intro")
            }

            Repeater {
                model: config.summaryModel
                delegate: Tarjeta {
                    Label {
                        Layout.fillWidth: true
                        text: model.title
                        font.bold: true
                        color: A.acento
                    }
                    Label {
                        Layout.fillWidth: true
                        text: model.message
                        textFormat: Text.StyledText
                        wrapMode: Text.WordWrap
                        color: A.texto
                    }
                }
            }

            Tarjeta {
                Label {
                    Layout.fillWidth: true
                    text: page.t("perfilesT")
                    font.bold: true
                    color: A.acento
                }
                Label {
                    Layout.fillWidth: true
                    text: [page.t("basico")].concat(page.extras).join(" · ")
                    wrapMode: Text.WordWrap
                    color: A.texto
                }
                Label {
                    Layout.fillWidth: true
                    visible: page.extras.length > 0
                    text: page.t("perfilesNota")
                    wrapMode: Text.WordWrap
                    color: A.secundario
                }
            }

            Rectangle {
                Layout.fillWidth: true
                implicitHeight: aviso.implicitHeight + 24
                radius: 8
                color: "#fff6e0"
                border.color: A.aviso
                RowLayout {
                    id: aviso
                    anchors.fill: parent
                    anchors.margins: 12
                    spacing: 12
                    Label { Layout.alignment: Qt.AlignTop; text: "!"; font.pixelSize: 22; font.bold: true; color: A.aviso }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 4
                        Label { text: page.t("copiaT"); font.bold: true; color: A.texto }
                        Label { Layout.fillWidth: true; text: page.t("copia"); wrapMode: Text.WordWrap; color: A.texto }
                    }
                }
            }
        }
    }
}
