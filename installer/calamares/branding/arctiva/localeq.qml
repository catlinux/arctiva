// SPDX-License-Identifier: GPL-3.0-or-later
// Página «Idioma y zona» (localeq): zona horaria, idioma del sistema y formatos, sin mapa
// (el de Calamares descarga los mosaicos de Internet; esta página funciona igual sin red).
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
        titulo: { es: "Idioma y zona", ca: "Idioma i zona", en: "Language and region" },
        intro: { es: "Elige dónde estás. Lo usamos para la hora y para proponerte el idioma y los formatos.",
                 ca: "Tria on ets. Ho fem servir per a l'hora i per proposar-te l'idioma i els formats.",
                 en: "Choose where you are. We use it for the clock and to suggest the language and formats." },
        region: { es: "Región", ca: "Regió", en: "Region" },
        zona: { es: "Zona horaria", ca: "Zona horària", en: "Time zone" },
        idiomaSistema: { es: "Idioma del sistema", ca: "Idioma del sistema", en: "System language" },
        formatos: { es: "Números y fechas", ca: "Nombres i dates", en: "Numbers and dates" },
        ejemplo: { es: "Ejemplo", ca: "Exemple", en: "Example" }
    })
    function t(clave) { return A.t(textos, clave, idioma); }

    // Locales UTF-8 de /usr/share/i18n/SUPPORTED, con su nombre en su propio idioma.
    property var locales: []

    function nombreLocale(codigo) {
        var l = Qt.locale(codigo);
        var nombre = l.nativeLanguageName !== "" ? l.nativeLanguageName : codigo;
        nombre = nombre.charAt(0).toUpperCase() + nombre.slice(1);
        if (l.nativeTerritoryName !== "")
            nombre += " (" + l.nativeTerritoryName + ")";
        return nombre + " · " + codigo;
    }

    function cargarLocales() {
        var lista = [];
        var vistos = {};
        for (var i = 0; i < config.supportedLocales.length; i++) {
            var linea = config.supportedLocales[i];
            if (linea.indexOf("UTF-8") < 0)
                continue;
            var codigo = A.codigoLocale(linea);
            if (linea.indexOf("@") >= 0 || vistos[codigo])
                continue;
            vistos[codigo] = true;
            lista.push({ texto: nombreLocale(codigo), linea: linea, codigo: codigo });
        }
        lista.sort(function(a, b) { return a.texto.localeCompare(b.texto); });
        locales = lista;
    }

    function indiceLocale(valor) {
        var codigo = A.codigoLocale(valor);
        for (var i = 0; i < locales.length; i++)
            if (locales[i].codigo === codigo)
                return i;
        return -1;
    }

    function sincronizar() {
        var zona = config.currentLocation;
        if (zona) {
            regiones.currentIndex = regiones.indexOfValue(zona.region);
            config.regionalZonesModel.region = zona.region;
            zonas.currentIndex = zonas.indexOfValue(zona.zone);
        }
        idiomas.currentIndex = indiceLocale(config.currentLanguageCode);
        formatos.currentIndex = indiceLocale(config.currentLCCode);
    }

    function onActivate() {
        sincronizar();
    }

    Component.onCompleted: {
        cargarLocales();
        sincronizar();
    }

    Connections {
        target: config
        function onCurrentLocationChanged() { page.sincronizar(); }
        function onCurrentLanguageCodeChanged() { idiomas.currentIndex = page.indiceLocale(config.currentLanguageCode); }
        function onCurrentLCCodeChanged() { formatos.currentIndex = page.indiceLocale(config.currentLCCode); }
    }

    Rectangle { anchors.fill: parent; color: A.fondo }

    ScrollView {
        anchors.fill: parent
        anchors.margins: 24
        contentWidth: availableWidth

        ColumnLayout {
            width: parent.width
            spacing: 16

            Cabecera {
                titulo: page.t("titulo")
                intro: page.t("intro")
            }

            Tarjeta {
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 12

                    Label { text: page.t("region"); font.bold: true; color: A.texto }
                    ComboBox {
                        id: regiones
                        Layout.fillWidth: true
                        model: config.regionModel
                        textRole: "name"
                        valueRole: "key"
                        onActivated: {
                            config.regionalZonesModel.region = currentValue;
                            zonas.currentIndex = 0;
                            config.setCurrentLocation(currentValue, zonas.currentValue);
                        }
                    }

                    Label { text: page.t("zona"); font.bold: true; color: A.texto }
                    ComboBox {
                        id: zonas
                        Layout.fillWidth: true
                        model: config.regionalZonesModel
                        textRole: "name"
                        valueRole: "key"
                        onActivated: config.setCurrentLocation(regiones.currentValue, currentValue)
                    }
                }
            }

            Tarjeta {
                GridLayout {
                    Layout.fillWidth: true
                    columns: 2
                    columnSpacing: 16
                    rowSpacing: 12

                    Label { text: page.t("idiomaSistema"); font.bold: true; color: A.texto }
                    ComboBox {
                        id: idiomas
                        Layout.fillWidth: true
                        model: page.locales
                        textRole: "texto"
                        onActivated: config.currentLanguageCode = page.locales[currentIndex].linea
                    }

                    Label { text: page.t("formatos"); font.bold: true; color: A.texto }
                    ComboBox {
                        id: formatos
                        Layout.fillWidth: true
                        model: page.locales
                        textRole: "texto"
                        onActivated: config.currentLCCode = page.locales[currentIndex].linea
                    }

                    Label { text: page.t("ejemplo"); color: A.secundario }
                    Label {
                        Layout.fillWidth: true
                        color: A.secundario
                        text: {
                            if (formatos.currentIndex < 0)
                                return "";
                            var l = Qt.locale(page.locales[formatos.currentIndex].codigo);
                            return Number(1234.56).toLocaleString(l, "f", 2) + " · "
                                 + new Date().toLocaleDateString(l, Locale.ShortFormat);
                        }
                    }
                }
            }

            Label {
                Layout.fillWidth: true
                text: config.prettyStatus
                textFormat: Text.StyledText
                wrapMode: Text.WordWrap
                color: A.secundario
            }
        }
    }
}
