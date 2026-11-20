#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-or-later
# Perfil de archiso de Arctiva, derivado del perfil releng de archiso.
# shellcheck disable=SC2034

iso_name="arctiva"
iso_label="ARCTIVA_$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y%m)"
iso_publisher="Arctiva <https://github.com/catlinux/arctiva>"
iso_application="Arctiva Live"
# build.sh exporta ARCTIVA_VERSION desde el archivo VERSION (D-16).
iso_version="${ARCTIVA_VERSION:-$(date --date="@${SOURCE_DATE_EPOCH:-$(date +%s)}" +%Y.%m.%d)}"
install_dir="arctiva"
buildmodes=('iso')
# Solo UEFI (D-04): un equipo sin UEFI no llega al instalador.
bootmodes=('uefi.systemd-boot')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/usr/local/bin/arctiva-live-setup"]="0:0:755"
)
