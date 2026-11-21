# SPDX-License-Identifier: GPL-3.0-or-later
"""Explica los errores habituales de pacman (D-08) a partir de errors.toml.

El ayudante ejecuta pacman con los mensajes en inglés (LC_ALL=C.UTF-8): así las expresiones
regulares no dependen del idioma del usuario, y la explicación se muestra traducida.
"""
import re
import tomllib
from dataclasses import dataclass

ACTIONS = {"retry", "keyring-first", "free-space", "check-network", "none"}


@dataclass(frozen=True)
class Explanation:
    id: str
    message: str
    action: str


class ErrorCatalog:
    def __init__(self, entries):
        self.entries = entries

    @classmethod
    def load(cls, path):
        with open(path, "rb") as f:
            return cls.parse(tomllib.load(f))

    @classmethod
    def parse(cls, data):
        entries = []
        for e in data.get("error", []):
            action = e.get("action", "none")
            if action not in ACTIONS:
                raise ValueError(f"acción desconocida en errors.toml: {action}")
            entries.append((e["id"], re.compile(e["pattern"], re.IGNORECASE | re.MULTILINE),
                            dict(e["message"]), action))
        return cls(entries)

    def explain(self, log_text, languages=("en",)):
        """Primera entrada (en el orden del archivo) que casa con el registro, o None."""
        for error_id, pattern, messages, action in self.entries:
            if pattern.search(log_text):
                return Explanation(error_id, _pick(messages, languages), action)
        return None


def _pick(messages, languages):
    for lang in languages:
        base = lang.replace("-", "_").split("_")[0]
        if base in messages:
            return messages[base]
    return messages["en"]
