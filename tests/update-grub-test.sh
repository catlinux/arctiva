#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Prueba /usr/lib/arctiva/update-grub (hook de arctiva-settings) con una raíz falsa y
# grub-install, grub-mkconfig y mountpoint falsos. No necesita root ni UEFI.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
script="${here}/../packages/arctiva-settings/files/usr/lib/arctiva/update-grub"
tmp="$(mktemp -d)"
trap 'rm -rf -- "$tmp"' EXIT

mkdir -p "${tmp}/bin"
for cmd in grub-install grub-mkconfig; do
    cat >"${tmp}/bin/${cmd}" <<'FAKE'
#!/usr/bin/env bash
echo "$(basename "$0") $*" >>"$FAKE_LOG"
[[ "$(basename "$0")" == grub-install && "${FAKE_INSTALL_FAILS:-0}" == 1 ]] && exit 1
exit 0
FAKE
    chmod +x "${tmp}/bin/${cmd}"
done
cat >"${tmp}/bin/mountpoint" <<'FAKE'
#!/usr/bin/env bash
[[ "${FAKE_ESP_MOUNTED:-1}" == 1 ]]
FAKE
chmod +x "${tmp}/bin/mountpoint"
export PATH="${tmp}/bin:${PATH}"

fallos=0
# preparar <uefi 0|1> <reserva: igual|distinta|ninguna|minusculas> [nuestro 0|1]
preparar() {
    local r="${tmp}/raiz"
    rm -rf -- "$r"
    mkdir -p "${r}/boot/efi/EFI/arctiva" "${r}/boot/grub"
    (( $1 )) && mkdir -p "${r}/sys/firmware/efi"
    if (( ${3:-1} )); then echo grub-viejo >"${r}/boot/efi/EFI/arctiva/grubx64.efi"; fi
    case "$2" in
        igual) mkdir -p "${r}/boot/efi/EFI/Boot"; echo grub-viejo >"${r}/boot/efi/EFI/Boot/BOOTX64.EFI" ;;
        minusculas) mkdir -p "${r}/boot/efi/EFI/Boot"; echo grub-viejo >"${r}/boot/efi/EFI/Boot/bootx64.efi" ;;
        distinta) mkdir -p "${r}/boot/efi/EFI/Boot"; echo windows >"${r}/boot/efi/EFI/Boot/BOOTX64.EFI" ;;
    esac
}
# probar <nombre> <código esperado> <llamadas esperadas, separadas por «|»>
probar() {
    local nombre="$1" esperado="$2" llamadas="$3" real obtenido r="${tmp}/raiz"
    : >"${tmp}/log"
    set +e
    FAKE_LOG="${tmp}/log" ARCTIVA_UPDATE_GRUB_ROOT="$r" "$script" >"${tmp}/salida" 2>&1
    real=$?
    set -e
    obtenido="$(paste -sd'|' "${tmp}/log")"
    if [[ "$real" == "$esperado" && "$obtenido" == "$llamadas" ]]; then
        echo "ok    ${nombre}"
    else
        echo "FALLO ${nombre}: código ${real} (esperado ${esperado}); llamadas «${obtenido}» (esperadas «${llamadas}»)"
        sed 's/^/      /' "${tmp}/salida"
        fallos=$((fallos + 1))
    fi
}

r="${tmp}/raiz"
normal="grub-install --target=x86_64-efi --efi-directory=${r}/boot/efi --bootloader-id=arctiva"
reserva="grub-install --target=x86_64-efi --efi-directory=${r}/boot/efi --removable --no-nvram"
mkconfig="grub-mkconfig -o ${r}/boot/grub/grub.cfg"

preparar 0 igual;            probar "BIOS: no se toca" 0 ""
preparar 1 igual;            FAKE_ESP_MOUNTED=0 probar "ESP sin montar: no se toca" 0 ""
preparar 1 ninguna 0;        probar "sin EFI/arctiva: no se toca" 0 ""
preparar 1 igual;            probar "reserva nuestra: se actualiza" 0 "${normal}|${reserva}|${mkconfig}"
preparar 1 minusculas;       probar "reserva nuestra en minúsculas" 0 "${normal}|${reserva}|${mkconfig}"
preparar 1 distinta;         probar "reserva ajena (Windows): no se toca" 0 "${normal}|${mkconfig}"
preparar 1 ninguna;          probar "sin reserva" 0 "${normal}|${mkconfig}"
preparar 1 igual;            FAKE_INSTALL_FAILS=1 probar "grub-install falla: sin grub-mkconfig" 1 "${normal}"

if (( fallos )); then
    echo "${fallos} comprobaciones fallidas" >&2
    exit 1
fi
echo "Todo correcto."
