# SPDX-License-Identifier: GPL-3.0-or-later
"""Elección del catálogo de traducciones a partir de los idiomas de la interfaz."""


def catalog_candidates(languages):
    """Nombres de catálogo por orden de preferencia («es-ES» → «es_ES», «es»).

    El inglés es el idioma de los textos fuente: si aparece antes que cualquier idioma con
    catálogo, no se carga ninguno.
    """
    names = []
    for lang in languages:
        norm = lang.replace("-", "_")
        base = norm.split("_")[0]
        if base == "en":
            break
        for name in (norm, base):
            if name not in names:
                names.append(name)
    return names
