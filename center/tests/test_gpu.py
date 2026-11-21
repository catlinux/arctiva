# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center.core import gpu

RTX = """gpus=nvidia
packages=nvidia-open nvidia-utils
services=
nvidia_kms=1
warning=
"""

LEGACY = """gpus=nvidia-legacy
packages=
services=
nvidia_kms=0
warning=nvidia-legacy
"""


def test_parse():
    r = gpu.parse(RTX)
    assert r.gpus == ["nvidia"]
    assert r.packages == ["nvidia-open", "nvidia-utils"]
    assert r.services == [] and r.nvidia_kms and r.warning == ""
    legacy = gpu.parse(LEGACY)
    assert legacy.warning == "nvidia-legacy" and not legacy.nvidia_kms and legacy.packages == []
    assert gpu.parse("") == gpu.GpuReport()


def test_missing(tmp_path):
    r = gpu.parse(RTX)
    conf = tmp_path / "arctiva-nvidia.conf"
    installed = gpu.parse_installed("linux\nnvidia-utils\n")
    assert gpu.missing(r, installed, conf) == (["nvidia-open"], True)
    conf.write_text("x")
    assert gpu.missing(r, installed | {"nvidia-open"}, conf) == ([], False)
    assert gpu.missing(gpu.parse(LEGACY), set(), conf) == ([], False)
