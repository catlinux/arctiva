// SPDX-License-Identifier: GPL-3.0-or-later
// Disposición tipo Windows 11: barra inferior de lado a lado, iconos centrados, menú de inicio con
// buscador, bandeja y reloj a la derecha y «Mostrar escritorio» en la esquina. En Plasma 6 el
// panel solo se mueve desde el modo de edición (clic derecho → «Entrar en modo edición»).
var desktopsArray = desktopsForActivity(currentActivity());
for (var j = 0; j < desktopsArray.length; j++) {
    desktopsArray[j].wallpaperPlugin = "org.kde.image";
}

var panel = new Panel();
panel.location = "bottom";
panel.height = 2 * Math.ceil(gridUnit * 2.7 / 2);
panel.floating = false;
panel.hiding = "none";

// Los dos separadores flexibles centran inicio y aplicaciones.
var left = panel.addWidget("org.kde.plasma.panelspacer");
left.currentConfigGroup = ["General"];
left.writeConfig("expanding", true);

panel.addWidget("org.kde.plasma.kickoff");

var tasks = panel.addWidget("org.kde.plasma.icontasks");
var launchers = [];
if (applicationExists("arctiva-center.desktop")) {
    launchers.push("applications:arctiva-center.desktop");
} else if (applicationExists("org.kde.discover.desktop")) {
    launchers.push("applications:org.kde.discover.desktop");
}
launchers.push("preferred://filemanager", "preferred://browser", "applications:systemsettings.desktop");
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", launchers);

var right = panel.addWidget("org.kde.plasma.panelspacer");
right.currentConfigGroup = ["General"];
right.writeConfig("expanding", true);

panel.addWidget("org.kde.plasma.systemtray");
panel.addWidget("org.kde.plasma.digitalclock");
panel.addWidget("org.kde.plasma.showdesktop");
