# SPDX-License-Identifier: GPL-3.0-or-later
"""Controladores (D-10): salida de arctiva-gpu frente a lo que ya está instalado."""
from dataclasses import dataclass, field
from pathlib import Path

NVIDIA_KMS_CONF = "/etc/mkinitcpio.conf.d/arctiva-nvidia.conf"


@dataclass
class GpuReport:
    gpus: list = field(default_factory=list)
    packages: list = field(default_factory=list)
    services: list = field(default_factory=list)
    nvidia_kms: bool = False
    warning: str = ""


def parse(text):
    values = {}
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip()
    return GpuReport(
        gpus=values.get("gpus", "").split(),
        packages=values.get("packages", "").split(),
        services=values.get("services", "").split(),
        nvidia_kms=values.get("nvidia_kms") == "1",
        warning=values.get("warning", ""),
    )


def parse_installed(pacman_qq):
    """Nombres de `pacman -Qq`."""
    return {line.strip() for line in pacman_qq.splitlines() if line.strip()}


def missing(report, installed, kms_conf=NVIDIA_KMS_CONF):
    """Lo que falta para dejar los controladores como los quiere arctiva-gpu."""
    packages = [p for p in report.packages if p not in installed]
    kms = report.nvidia_kms and not Path(kms_conf).exists()
    return packages, kms
