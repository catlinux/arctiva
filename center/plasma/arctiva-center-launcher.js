// SPDX-License-Identifier: GPL-3.0-or-later
// El sistema instalado no lleva Discover (D-09) y su lanzador fijado en el panel quedaría como un
// icono en blanco: se cambia por Arctiva Center. En la live Discover existe y no se toca.
// Plasma ejecuta cada script de updates/ una sola vez por usuario.
var DISCOVER = "applications:org.kde.discover.desktop";
var CENTER = "applications:arctiva-center.desktop";
// Lista por defecto del gestor de tareas (Plasma 6) con Arctiva Center en el sitio de Discover.
// Con la configuración sin tocar, readConfig devuelve "" y no da acceso al valor por defecto.
var DEFAULT = ["applications:systemsettings.desktop", CENTER, "preferred://filemanager", "preferred://browser"];

if (!applicationExists("org.kde.discover.desktop") && applicationExists("arctiva-center.desktop")) {
    panels().forEach(function (panel) {
        panel.widgetIds.forEach(function (id) {
            var widget = panel.widgetById(id);
            if (widget.type !== "org.kde.plasma.icontasks" && widget.type !== "org.kde.plasma.taskmanager") {
                return;
            }
            widget.currentConfigGroup = ["General"];
            var value = widget.readConfig("launchers", "");
            var launchers = Array.isArray(value) ? value : String(value).split(",").filter(Boolean);
            if (launchers.length === 0) {
                launchers = DEFAULT;
            } else if (launchers.indexOf(DISCOVER) >= 0) {
                launchers = launchers.indexOf(CENTER) >= 0
                    ? launchers.filter(function (l) { return l !== DISCOVER; })
                    : launchers.map(function (l) { return l === DISCOVER ? CENTER : l; });
            } else {
                return;
            }
            widget.writeConfig("launchers", launchers);
            widget.reloadConfig();
        });
    });
}
