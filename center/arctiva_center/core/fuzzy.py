# SPDX-License-Identifier: GPL-3.0-or-later
"""Búsqueda tolerante: sin tildes ni mayúsculas, sin guiones, puntos ni espacios («claude code»,
«claude-code» y «claudecode» son lo mismo) y con margen para una o dos erratas."""
import re
import unicodedata


def fold(text):
    nfkd = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in nfkd if not unicodedata.combining(c)).casefold()


def tokens(text):
    """Palabras de la consulta: se parte por cualquier cosa que no sea letra o número."""
    return [t for t in re.split(r"[\W_]+", fold(text)) if t]


def squash(text):
    """Solo letras y números, para comparar sin fijarse en separadores."""
    return re.sub(r"[\W_]+", "", fold(text))


def distance(a, b):
    """Distancia de edición con transposiciones («cluade» está a 1 de «claude»)."""
    if a == b:
        return 0
    if not a or not b:
        return max(len(a), len(b))
    prev2, prev = None, list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            best = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                best = min(best, prev2[j - 2] + 1)
            cur.append(best)
        prev2, prev = prev, cur
    return prev[-1]


def budget(length):
    """Erratas que se admiten según lo larga que es la palabra: ninguna en las muy cortas."""
    return 0 if length < 4 else 1 if length < 8 else 2


def closeness(token, word):
    """Distancia de `token` a `word` (entera o solo a su comienzo, para lo escrito a medias),
    o None si supera el margen de erratas."""
    if token in word:
        return 0
    allowed = budget(len(token))
    best = min(distance(token, word), distance(token, word[:len(token)]))
    return best if best <= allowed else None


def fuzzy_total(query_tokens, words):
    """Suma de distancias si cada palabra de la consulta se parece a alguna de `words`; si no, None."""
    total = 0
    for token in query_tokens:
        found = [d for d in (closeness(token, w) for w in words) if d is not None]
        if not found:
            return None
        total += min(found)
    return total
