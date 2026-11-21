// SPDX-License-Identifier: GPL-3.0-or-later
// Paleta y textos compartidos por las páginas QML del instalador.
.pragma library

var fondo = "#f5f7fc";
var tarjeta = "#ffffff";
var borde = "#dbe3f4";
var texto = "#0d1730";
var secundario = "#4a5878";
var acento = "#1d4ed8";
var brillante = "#3d86ff";
var ok = "#2e7d4f";
var aviso = "#b7791f";
var error = "#c62828";
// Tipografía corporativa (arctiva-branding la instala); sin ella Qt usa la de siempre.
var marca = "Outfit";

// Idioma de la interfaz («es», «ca» o «en»). Calamares cambia el QLocale por defecto al elegir
// idioma en la bienvenida, pero las páginas QML no se retraducen solas. «disparador» no se usa:
// pasar ViewManager.backLabel, que Calamares retraduce, hace que el enlace se recalcule.
function idioma(locale, disparador) {
    var codigo = locale.name.substring(0, 2);
    return (codigo === "es" || codigo === "ca") ? codigo : "en";
}

// textos: { clave: { es, ca, en } }; si falta la traducción, inglés.
function t(textos, clave, lengua) {
    var entrada = textos[clave];
    if (entrada === undefined)
        return clave;
    return entrada[lengua] !== undefined ? entrada[lengua] : entrada.en;
}

// «es_ES.UTF-8 UTF-8» → «es_ES»
function codigoLocale(linea) {
    return linea.split(" ")[0].split(".")[0].split("@")[0];
}
