// SPDX-License-Identifier: GPL-3.0-or-later
// Presentación durante la instalación (slideshowAPI: 2). Solo describe lo que el sistema
// instalado ya tiene; Arctiva Center y la tienda se añadirán cuando existan.
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "Arctiva.js" as A

Item {
    id: presentacion

    // API 1 solo usa esta propiedad; la API 2 llama además a onActivate() y onLeave().
    property bool activatedInCalamares: false
    property int actual: 0
    property string idioma: A.idioma(Qt.locale())

    readonly property var diapositivas: [
        { titulo: { es: "Si algo falla, vuelve atrás", ca: "Si alguna cosa falla, torna enrere", en: "If something breaks, go back" },
          texto: { es: "Antes de cada actualización Arctiva guarda una instantánea del sistema. Si después algo no va, elige una anterior en el menú de arranque.",
                   ca: "Abans de cada actualització Arctiva desa una instantània del sistema. Si després alguna cosa no va, tria'n una d'anterior al menú d'arrencada.",
                   en: "Before every update Arctiva saves a snapshot of the system. If something stops working, pick an earlier one from the boot menu." } },
        { titulo: { es: "El escritorio que ya conoces", ca: "L'escriptori que ja coneixes", en: "The desktop you already know" },
          texto: { es: "KDE Plasma, el mismo que estás usando ahora, con tus ajustes de idioma, teclado y zona horaria.",
                   ca: "KDE Plasma, el mateix que fas servir ara, amb els teus ajustos d'idioma, teclat i zona horària.",
                   en: "KDE Plasma, the same one you are using now, with your language, keyboard and time zone settings." } },
        { titulo: { es: "Siempre al día", ca: "Sempre al dia", en: "Always up to date" },
          texto: { es: "Arctiva se basa en Arch Linux: recibes las versiones nuevas de los programas en cuanto salen, sin reinstalar.",
                   ca: "Arctiva es basa en Arch Linux: reps les versions noves dels programes tan bon punt surten, sense reinstal·lar.",
                   en: "Arctiva is based on Arch Linux: you get new versions of your programs as soon as they are released, without reinstalling." } },
        { titulo: { es: "Tus datos, protegidos", ca: "Les teves dades, protegides", en: "Your data, protected" },
          texto: { es: "Si has elegido cifrar el sistema, nadie podrá leer el disco sin tu contraseña, aunque se lleven el equipo.",
                   ca: "Si has triat xifrar el sistema, ningú no podrà llegir el disc sense la teva contrasenya, encara que s'emportin l'ordinador.",
                   en: "If you chose to encrypt the system, nobody can read the disk without your password, even if the computer is taken." } }
    ]

    function onActivate() {
        idioma = A.idioma(Qt.locale());
        actual = 0;
        activatedInCalamares = true;
    }
    function onLeave() { activatedInCalamares = false; }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            orientation: Gradient.Vertical
            GradientStop { position: 0.0; color: "#0d1730" }
            GradientStop { position: 1.0; color: "#0b2d8f" }
        }
    }

    Timer {
        interval: 9000
        repeat: true
        running: presentacion.activatedInCalamares
        onTriggered: presentacion.actual = (presentacion.actual + 1) % presentacion.diapositivas.length
    }

    ColumnLayout {
        id: contenido
        anchors.centerIn: parent
        width: Math.min(parent.width - 64, 640)
        spacing: 16

        Label {
            Layout.alignment: Qt.AlignHCenter
            text: (presentacion.actual + 1) + " / " + presentacion.diapositivas.length
            color: "#9be7ff"
            font.pixelSize: 13
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: A.t(presentacion.diapositivas[presentacion.actual], "titulo", presentacion.idioma)
            color: "#ffffff"
            font.pixelSize: 30
            font.bold: true
            wrapMode: Text.WordWrap
        }
        Label {
            Layout.fillWidth: true
            horizontalAlignment: Text.AlignHCenter
            text: A.t(presentacion.diapositivas[presentacion.actual], "texto", presentacion.idioma)
            color: "#c3cee8"
            font.pixelSize: 16
            wrapMode: Text.WordWrap
        }
    }

    // Puntos para pasar de diapositiva a mano.
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 24
        spacing: 10
        Repeater {
            model: presentacion.diapositivas.length
            delegate: Rectangle {
                width: 10; height: 10; radius: 5
                color: index === presentacion.actual ? "#4cc3ff" : "#3a4f86"
                MouseArea { anchors.fill: parent; onClicked: presentacion.actual = index }
            }
        }
    }
}
