# SPDX-License-Identifier: GPL-3.0-or-later
"""Vuelve a comprobar internet antes de instalar paquetes.

Calamares mira la red una sola vez, al abrir el instalador, y guarda el resultado en
GlobalStorage («hasInternet»). El módulo «packages» (con skip_if_no_internet) usa ese valor:
si la persona se conecta después de abrir el instalador, se saltaría linux-lts y los perfiles
aunque ya haya red. Este trabajo lo actualiza justo antes de «packages».
"""
import urllib.request

import libcalamares

# La misma URL que internetCheckUrl de welcomeq.conf.
URL = "http://ping.archlinux.org/nm-check.txt"


def pretty_name():
    return "Checking the internet connection"


def run():
    try:
        with urllib.request.urlopen(URL, timeout=10) as response:
            online = 200 <= response.status < 300
    except OSError:
        online = False
    libcalamares.globalstorage.insert("hasInternet", online)
    libcalamares.utils.debug("arctivanet: hasInternet = {}".format(online))
    return None
