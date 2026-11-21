# SPDX-License-Identifier: GPL-3.0-or-later
"""Personalización (decisión 2 de la fase 5): cada ajuste es una orden de Plasma que se ejecuta
como el usuario, sin el ayudante. Las funciones devuelven listas de órdenes; `apply` las ejecuta
con un `runner` que se sustituye en las pruebas."""
import json
import os
import re
import subprocess
from pathlib import Path

LIGHT_SCHEME = "ArctivaLight"
DARK_SCHEME = "BreezeDark"
LOOK_AND_FEEL = "org.arctiva.desktop"
WALLPAPER = "/usr/share/wallpapers/Arctiva"
# Acento de cada modo cuando el usuario no ha elegido otro (el esquema claro ya lo trae).
DEFAULT_ACCENT = {"light": "#1d4ed8", "dark": "#3d86ff"}

ACCENTS = {  # nombre → color; el primero es el de Arctiva
    "arctiva": "#1d4ed8",
    "sky": "#3d86ff",
    "cyan": "#0891b2",
    "green": "#16a34a",
    "orange": "#ea580c",
    "red": "#dc2626",
    "purple": "#7c3aed",
}

# (clave, tamaño base en puntos); el resto de fuentes se dejan como estén.
FONT_KEYS = (("font", 10), ("menuFont", 10), ("toolBarFont", 10), ("smallestReadableFont", 8))
TEXT_SCALES = (0.9, 1.0, 1.15, 1.3)
SCREEN_SCALES = (1.0, 1.25, 1.5, 1.75, 2.0)

DEFAULT_FONT = "Noto Sans,{size},-1,5,400,0,0,0,0,0,0,0,0,0,0,1"

# Script de Plasma (se ejecuta con evaluateScript). Los separadores del panel de Arctiva son los
# dos panelspacer que hay antes y después de la lista de tareas.
_PANEL_SCRIPT = """
panels().forEach(function (panel) {
    var spacers = [];
    var hasTasks = false;
    panel.widgetIds.forEach(function (id) {
        var type = panel.widgetById(id).type;
        if (type === "org.kde.plasma.panelspacer") spacers.push(panel.widgetById(id));
        if (type === "org.kde.plasma.icontasks") hasTasks = true;
    });
    if (!hasTasks) return;
%s
});
"""


def prefs_file(env=os.environ):
    config = env.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(config) / "arctiva-center" / "appearance.json"


def load_prefs(env=os.environ):
    """Barra centrada y flotante: Plasma no los devuelve de forma fiable, el Centro los recuerda."""
    try:
        data = json.loads(prefs_file(env).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {"centered": bool(data.get("centered", True)), "floating": bool(data.get("floating", False))}


def save_pref(key, value, env=os.environ):
    prefs = load_prefs(env)
    prefs[key] = bool(value)
    path = prefs_file(env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(prefs), encoding="utf-8")


def hex_to_rgb(color):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", color)
    if not m:
        raise ValueError(color)
    v = int(m.group(1), 16)
    return v >> 16, (v >> 8) & 255, v & 255


def run(argv, timeout=15):
    """Ejecuta una orden; (código, salida). Si no existe o tarda demasiado, código -1."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError):
        return -1, ""
    return p.returncode, p.stdout


def apply(commands, runner=run):
    """Ejecuta las órdenes en fila; True si todas terminan bien."""
    ok = True
    for argv in commands:
        code, _ = runner(argv)
        ok = ok and code == 0
    return ok


def _kwrite(file, group, key, value):
    return ["kwriteconfig6", "--file", file, "--group", group, "--key", key, value]


def _kdelete(file, group, key):
    return ["kwriteconfig6", "--file", file, "--group", group, "--key", key, "--delete"]


def _plasma_script(js):
    return ["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js]


def accent_commands(color):
    hex_to_rgb(color)
    return [["plasma-apply-colorscheme", "--accent-color", color]]


def mode_commands(mode, accent=None):
    """Claro, oscuro o automático (por la salida y la puesta del sol, Plasma 6.2 o posterior)."""
    if mode == "auto":
        return [
            _kwrite("kdeglobals", "KDE", "AutomaticLookAndFeel", "true"),
            _kwrite("kdeglobals", "KDE", "DefaultLightLookAndFeel", LOOK_AND_FEEL),
            _kwrite("kdeglobals", "KDE", "DefaultDarkLookAndFeel", LOOK_AND_FEEL + ".dark"),
        ]
    if mode not in ("light", "dark"):
        raise ValueError(mode)
    if not accent or accent in DEFAULT_ACCENT.values():
        accent = DEFAULT_ACCENT[mode]
    return [_kwrite("kdeglobals", "KDE", "AutomaticLookAndFeel", "false"),
            ["plasma-apply-colorscheme", LIGHT_SCHEME if mode == "light" else DARK_SCHEME]
            ] + accent_commands(accent)


def wallpaper_commands(path=WALLPAPER):
    return [["plasma-apply-wallpaperimage", path]]


def alignment_commands(centered):
    body = ('    if (spacers.length >= 2) {\n'
            '        spacers[0].currentConfigGroup = ["General"];\n'
            '        spacers[0].writeConfig("expanding", %s);\n'
            '        spacers[0].reloadConfig();\n'
            '    }') % ("true" if centered else "false")
    return [_plasma_script(_PANEL_SCRIPT % body)]


def floating_commands(floating):
    body = "    panel.floating = %s;" % ("true" if floating else "false")
    return [_plasma_script(_PANEL_SCRIPT % body)]


def scale_font(spec, size):
    """Cambia el tamaño (segundo campo) de una fuente de KDE: «Noto Sans,10,-1,5,400,…»."""
    parts = (spec or "").split(",")
    if len(parts) < 2:
        parts = DEFAULT_FONT.format(size=size).split(",")
    parts[1] = str(size)
    return ",".join(parts)


def text_commands(scale, current=None):
    """`current` son las fuentes actuales por clave (para conservar la familia)."""
    current = current or {}
    cmds = [_kwrite("kdeglobals", "General", key, scale_font(current.get(key), round(base * scale)))
            for key, base in FONT_KEYS]
    cmds.append(["dbus-send", "--session", "/KGlobalSettings", "org.kde.KGlobalSettings.notifyChange",
                 "int32:3", "int32:0"])
    return cmds


def screen_commands(scale, outputs):
    """`outputs` son los nombres de las pantallas activas."""
    if not outputs:
        return []
    return [["kscreen-doctor"] + ["output.%s.scale.%s" % (name, scale) for name in outputs]]


def parse_outputs(kscreen_json):
    try:
        data = json.loads(kscreen_json)
    except ValueError:
        return []
    return [o["name"] for o in data.get("outputs", []) if o.get("enabled") and o.get("name")]


def parse_scale(kscreen_json):
    try:
        data = json.loads(kscreen_json)
    except ValueError:
        return 1.0
    for o in data.get("outputs", []):
        if o.get("enabled"):
            return float(o.get("scale", 1.0))
    return 1.0


def night_light_commands(active):
    return [_kwrite("kwinrc", "NightColor", "Active", "true" if active else "false"),
            ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"]]


def restore_commands():
    """Vuelve al tema global, panel y fondo de Arctiva; borra los tamaños de texto y el modo automático; el acento vuelve con el esquema."""
    cmds = [_kwrite("kdeglobals", "KDE", "AutomaticLookAndFeel", "false")]
    cmds += [_kdelete("kdeglobals", "General", key) for key, _ in FONT_KEYS]
    cmds.append(["lookandfeeltool", "-a", LOOK_AND_FEEL, "--resetLayout"])
    cmds += wallpaper_commands()
    return cmds


def read_state(runner=run):
    """Estado actual para la página: modo, acento, texto y luz nocturna."""
    def value(file, group, key):
        code, out = runner(["kreadconfig6", "--file", file, "--group", group, "--key", key])
        return out.strip() if code == 0 else ""

    scheme = value("kdeglobals", "General", "ColorScheme")
    auto = value("kdeglobals", "KDE", "AutomaticLookAndFeel") == "true"
    mode = "auto" if auto else ("dark" if "dark" in scheme.lower() else "light")
    # El acento no se guarda en una clave propia: Plasma lo escribe en los colores del esquema.
    m = re.fullmatch(r"(\d+),(\d+),(\d+)", value("kdeglobals", "Colors:View", "DecorationFocus"))
    accent = "#%02x%02x%02x" % tuple(int(x) for x in m.groups()) if m else ""
    fonts = {key: value("kdeglobals", "General", key) for key, _ in FONT_KEYS}
    text_scale = 1.0
    m = re.match(r"[^,]*,(\d+)", fonts.get("font", ""))
    if m:
        text_scale = min(TEXT_SCALES, key=lambda s: abs(round(10 * s) - int(m.group(1))))
    return {
        "mode": mode,
        "accent": accent,
        "nightLight": value("kwinrc", "NightColor", "Active") == "true",
        "fonts": fonts,
        "textScale": text_scale,
    }
