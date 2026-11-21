#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Genera el tema de GRUB de Arctiva: copia branding/grub/arctiva en <destino> y le añade lo que
# sale de otros archivos del repositorio (fondo, logo, iconos y fuentes .pf2 de Outfit).
# Uso: build-theme.sh <carpeta-de-branding> <destino>
# Necesita rsvg-convert (librsvg), grub-mkfont (grub) y fontTools (python-fonttools).
set -euo pipefail

branding="${1:?uso: $0 <branding> <destino>}"
out="${2:?uso: $0 <branding> <destino>}"
src="${branding}/grub/arctiva"

mkdir -p -- "$out/icons"
cp -- "$src/theme.txt" "$src"/select_*.png "$out/"
rsvg-convert -w 1920 -h 1080 "$src/background.svg" -o "$out/background.png"
rsvg-convert -w 96 -h 96 "${branding}/logo/arctiva-mark.svg" -o "$out/logo.png"
for svg in "$src"/icons/*.svg; do
    rsvg-convert -w 32 -h 32 "$svg" -o "$out/icons/$(basename -- "${svg%.svg}").png"
done

# GRUB no lee fuentes variables: se fijan los pesos y se pasan a .pf2. El nombre que usa theme.txt
# («Outfit Regular <tamaño>») sale de la familia y el estilo de la fuente: se comprueba.
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT
python3 - "${branding}/fonts/Outfit[wght].ttf" "$tmp" <<'PY'
import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
for weight, name in ((400, "Regular"), (600, "SemiBold")):
    font = instantiateVariableFont(TTFont(sys.argv[1]), {"wght": weight}, updateFontNames=True)
    font.save(f"{sys.argv[2]}/Outfit-{name}.ttf")
PY
grub-mkfont -s 14 -o "$out/outfit-regular-14.pf2" "$tmp/Outfit-Regular.ttf"
grub-mkfont -s 20 -o "$out/outfit-regular-20.pf2" "$tmp/Outfit-Regular.ttf"
grub-mkfont -s 32 -o "$out/outfit-semibold-32.pf2" "$tmp/Outfit-SemiBold.ttf"
python3 - "$out" <<'PY'
import re, struct, sys
theme = open(sys.argv[1] + "/theme.txt", encoding="utf-8").read()
names = set()
for pf2 in ("outfit-regular-14", "outfit-regular-20", "outfit-semibold-32"):
    data = open(f"{sys.argv[1]}/{pf2}.pf2", "rb").read()
    i = data.index(b"NAME")
    size = struct.unpack(">I", data[i + 4:i + 8])[0]
    names.add(data[i + 8:i + 8 + size].rstrip(b"\0").decode())
used = set(re.findall(r'"(Outfit [^"]+)"', theme))
if not used <= names:
    sys.exit("build-theme.sh: theme.txt usa fuentes que no existen: %s (hay %s)" % (sorted(used - names), sorted(names)))
PY
