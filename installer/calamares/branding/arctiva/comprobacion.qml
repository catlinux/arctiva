/* SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Página «Comprobación» (módulo notesqml, D-03): muestra lo que arctiva-installer ha
 * encontrado en el equipo (/run/arctiva/equipo.json) antes de llegar a la página de disco.
 * Calamares no deja bloquear «Siguiente» desde QML: el nivel «bloqueo» recomienda salir y
 * ofrece un botón para hacerlo. ntfsresize se niega a redimensionar un NTFS hibernado.
 */
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import io.calamares.ui 1.0

Item {
    id: page

    // null: sin datos (Calamares abierto sin el lanzador o archivo ilegible).
    property var equipo: null

    // La página se crea al arrancar Calamares, antes de elegir idioma en la bienvenida: el idioma
    // (QLocale por defecto, que fija la bienvenida) se vuelve a leer cada vez que se muestra.
    property string idioma: "en"

    // Textos en castellano, catalán e inglés.
    readonly property var textos: ({
        titulo: { es: "Comprobación del equipo", ca: "Comprovació de l'ordinador", en: "Computer check" },
        intro: { es: "Antes de tocar el disco, revisamos lo que podría darte problemas.",
                 ca: "Abans de tocar el disc, revisem el que et podria donar problemes.",
                 en: "Before touching the disk, we check for anything that could cause trouble." },
        sinDatosT: { es: "No se ha podido revisar el equipo", ca: "No s'ha pogut revisar l'ordinador", en: "The computer could not be checked" },
        sinDatos: { es: "Abre el instalador desde «Instalar Arctiva» para que revise Windows y BitLocker. Puedes seguir, pero sin estas comprobaciones.",
                    ca: "Obre l'instal·lador des de «Instal·la Arctiva» perquè revisi Windows i BitLocker. Pots continuar, però sense aquestes comprovacions.",
                    en: "Open the installer from \"Install Arctiva\" so it can check Windows and BitLocker. You can continue, but without these checks." },
        hibernadoT: { es: "Windows no se apagó del todo", ca: "Windows no es va apagar del tot", en: "Windows did not fully shut down" },
        hibernado: { es: "Windows está hibernado o con el inicio rápido, y su disco está bloqueado: si se modifica ahora, puedes perder datos. Arranca Windows, ejecuta «shutdown /s /t 0» (o desactiva el inicio rápido en Opciones de energía) y vuelve a abrir el instalador. Hasta entonces no se puede instalar junto a Windows.",
                     ca: "Windows està hibernat o amb l'inici ràpid, i el seu disc està bloquejat: si es modifica ara, pots perdre dades. Arrenca Windows, executa «shutdown /s /t 0» (o desactiva l'inici ràpid a Opcions d'energia) i torna a obrir l'instal·lador. Fins aleshores no es pot instal·lar al costat de Windows.",
                     en: "Windows is hibernated or uses Fast Startup, so its disk is locked: changing it now could lose data. Start Windows, run \"shutdown /s /t 0\" (or turn off Fast Startup in Power Options) and open the installer again. Until then you cannot install alongside Windows." },
        salir: { es: "Salir del instalador", ca: "Surt de l'instal·lador", en: "Quit the installer" },
        bitlockerT: { es: "Windows con BitLocker", ca: "Windows amb BitLocker", en: "Windows with BitLocker" },
        bitlocker: { es: "Arctiva no puede reducir una partición cifrada con BitLocker. Si quieres conservar Windows: en Windows, abre «Administración de discos» y reduce su partición (deja 40 GB libres o más); y ten a mano la clave de recuperación de BitLocker (aka.ms/myrecoverykey), porque Windows te la pedirá al haber cambiado Secure Boot.",
                     ca: "Arctiva no pot reduir una partició xifrada amb BitLocker. Si vols conservar Windows: a Windows, obre «Administració de discos» i redueix la seva partició (deixa 40 GB lliures o més); i tingues a mà la clau de recuperació de BitLocker (aka.ms/myrecoverykey), perquè Windows te la demanarà en haver canviat Secure Boot.",
                     en: "Arctiva cannot shrink a BitLocker-encrypted partition. To keep Windows: in Windows, open \"Disk Management\" and shrink its partition (leave 40 GB or more free); and keep your BitLocker recovery key at hand (aka.ms/myrecoverykey), because Windows will ask for it after the Secure Boot change." },
        windowsOkT: { es: "Windows apagado del todo", ca: "Windows apagat del tot", en: "Windows fully shut down" },
        windowsOk: { es: "Puedes instalar Arctiva junto a Windows.", ca: "Pots instal·lar Arctiva al costat de Windows.", en: "You can install Arctiva alongside Windows." },
        sinWindowsT: { es: "Todo listo", ca: "Tot a punt", en: "All set" },
        sinWindows: { es: "No hemos encontrado Windows en este equipo.", ca: "No hem trobat Windows en aquest ordinador.", en: "No Windows installation was found on this computer." },
        relojT: { es: "Hora de Windows", ca: "Hora de Windows", en: "Windows clock" },
        reloj: { es: "Arctiva guarda la hora del equipo en UTC y Windows en hora local: tras volver a Windows, la hora puede salir desfasada. La guía de instalación explica cómo ajustarlo.",
                 ca: "Arctiva desa l'hora de l'ordinador en UTC i Windows en hora local: en tornar a Windows, l'hora pot sortir desfasada. La guia d'instal·lació explica com ajustar-ho.",
                 en: "Arctiva keeps the hardware clock in UTC and Windows in local time: back in Windows, the time may be off. The installation guide explains how to fix it." },
        bateriaT: { es: "Conecta el cargador", ca: "Connecta el carregador", en: "Plug in the charger" },
        bateria: { es: "El equipo funciona con batería. Si se apaga durante la instalación, el sistema puede quedar inutilizable.",
                   ca: "L'ordinador funciona amb bateria. Si s'apaga durant la instal·lació, el sistema pot quedar inutilitzable.",
                   en: "The computer is running on battery. If it powers off during the installation, the system may be left unusable." },
        sinRedT: { es: "Sin conexión a Internet", ca: "Sense connexió a Internet", en: "No Internet connection" },
        sinRed: { es: "Se instalará lo que lleva el USB, sin actualizar y sin el kernel LTS de reserva. Puedes conectarte ahora desde el icono de red.",
                  ca: "S'instal·larà el que porta l'USB, sense actualitzar i sense el nucli LTS de reserva. Pots connectar-te ara des de la icona de xarxa.",
                  en: "What is on the USB stick will be installed, without updates and without the backup LTS kernel. You can connect now from the network icon." },
        nvidiaT: { es: "Gráfica NVIDIA", ca: "Gràfica NVIDIA", en: "NVIDIA graphics" },
        nvidia: { es: "Se instalará el controlador de NVIDIA. Necesita conexión: sin ella se usa el controlador libre y podrás instalar el de NVIDIA después.",
                  ca: "S'instal·larà el controlador de NVIDIA. Necessita connexió: sense ella s'usa el controlador lliure i podràs instal·lar el de NVIDIA després.",
                  en: "The NVIDIA driver will be installed. It needs a connection: without one the free driver is used and you can install NVIDIA's later." },
        nvidiaLegacyT: { es: "Gráfica NVIDIA antigua", ca: "Gràfica NVIDIA antiga", en: "Older NVIDIA graphics" },
        nvidiaLegacy: { es: "Tu NVIDIA (GTX 900/1000 o anterior) usará el controlador libre «nouveau». El controlador propietario 580xx solo está en el AUR.",
                        ca: "La teva NVIDIA (GTX 900/1000 o anterior) usarà el controlador lliure «nouveau». El controlador propietari 580xx només és a l'AUR.",
                        en: "Your NVIDIA card (GTX 900/1000 or older) will use the free \"nouveau\" driver. The proprietary 580xx driver is only in the AUR." }
    })

    function t(clave) {
        var entrada = textos[clave];
        return entrada[idioma] !== undefined ? entrada[idioma] : entrada.en;
    }

    function cargar() {
        idioma = Qt.locale().name.substring(0, 2);
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState !== XMLHttpRequest.DONE)
                return;
            try {
                page.equipo = JSON.parse(xhr.responseText);
            } catch (e) {
                page.equipo = null;
            }
        };
        xhr.open("GET", "file:///run/arctiva/equipo.json");
        xhr.send();
    }

    // Calamares llama a onActivate() al mostrar la página.
    function onActivate() { cargar(); }
    Component.onCompleted: cargar()

    // Tarjeta de estado: color, símbolo y texto (nunca solo color).
    component Estado: Rectangle {
        id: tarjeta
        property string tipo: "ok"   // ok, aviso, bloqueo, info
        property string titulo
        property string texto
        default property alias extra: pie.data

        Layout.fillWidth: true
        implicitHeight: fila.implicitHeight + 24
        radius: 8
        color: tipo === "bloqueo" ? "#fdecec" : tipo === "aviso" ? "#fff6e0" : tipo === "ok" ? "#e8f6ee" : "#eef2fb"
        border.color: tipo === "bloqueo" ? "#c62828" : tipo === "aviso" ? "#b7791f" : tipo === "ok" ? "#2e7d4f" : "#1d4ed8"
        border.width: 1

        RowLayout {
            id: fila
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Label {
                Layout.alignment: Qt.AlignTop
                text: tarjeta.tipo === "bloqueo" ? "✕" : tarjeta.tipo === "aviso" ? "!" : tarjeta.tipo === "ok" ? "✓" : "i"
                font.pixelSize: 22
                font.bold: true
                color: tarjeta.border.color
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 4
                Label { text: tarjeta.titulo; font.bold: true; Layout.fillWidth: true; wrapMode: Text.WordWrap; color: "#1a1a1a" }
                Label { text: tarjeta.texto; Layout.fillWidth: true; wrapMode: Text.WordWrap; color: "#333333" }
                RowLayout { id: pie }
            }
        }
    }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 16
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 12

            Label { text: page.t("titulo"); font.pixelSize: 22; font.bold: true }
            Label { text: page.t("intro"); Layout.fillWidth: true; wrapMode: Text.WordWrap }

            Estado {
                visible: page.equipo === null
                tipo: "aviso"
                titulo: page.t("sinDatosT")
                texto: page.t("sinDatos")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.hibernado.length > 0
                tipo: "bloqueo"
                titulo: page.t("hibernadoT")
                texto: page.t("hibernado")
                Button {
                    text: page.t("salir")
                    onClicked: ViewManager.quit()
                }
            }
            Estado {
                visible: page.equipo !== null && page.equipo.bitlocker.length > 0
                tipo: "aviso"
                titulo: page.t("bitlockerT")
                texto: page.t("bitlocker")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.windows
                         && page.equipo.hibernado.length === 0 && page.equipo.bitlocker.length === 0
                tipo: "ok"
                titulo: page.t("windowsOkT")
                texto: page.t("windowsOk")
            }
            Estado {
                visible: page.equipo !== null && !page.equipo.windows
                tipo: "ok"
                titulo: page.t("sinWindowsT")
                texto: page.t("sinWindows")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.windows
                tipo: "info"
                titulo: page.t("relojT")
                texto: page.t("reloj")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.bateria
                tipo: "aviso"
                titulo: page.t("bateriaT")
                texto: page.t("bateria")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.gpu !== undefined
                         && page.equipo.gpu.familias.indexOf("nvidia") >= 0
                tipo: "info"
                titulo: page.t("nvidiaT")
                texto: page.t("nvidia")
            }
            Estado {
                visible: page.equipo !== null && page.equipo.gpu !== undefined
                         && page.equipo.gpu.aviso === "nvidia-legacy"
                tipo: "aviso"
                titulo: page.t("nvidiaLegacyT")
                texto: page.t("nvidiaLegacy")
            }
            Estado {
                visible: page.equipo !== null && !page.equipo.red
                tipo: "info"
                titulo: page.t("sinRedT")
                texto: page.t("sinRed")
            }
        }
    }
}
