# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: cliente de lutris.net con caché en disco (24 h) y como mucho una petición por segundo.

`search(texto)` devuelve los juegos y `installers(slug)` los scripts de instalación de un juego (el campo
`content` es el YAML que analiza `games_script`). Los scripts se descargan en el momento y no se guardan
en el repositorio. Sin red se usa la caché, aunque haya caducado; sin caché, `ApiError`."""
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

from .. import __version__

BASE = "https://lutris.net/api"
TTL = 24 * 3600
MIN_INTERVAL = 1.0
TIMEOUT = 15
CACHE = Path.home() / ".cache" / "arctiva-games"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class ApiError(Exception):
    pass


def default_fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"Arctiva-Games/{__version__}",
                                               "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8")


class GamesApi:
    def __init__(self, cache_dir=CACHE, fetch=default_fetch, clock=time.time, sleep=time.sleep):
        self.cache_dir = Path(cache_dir)
        self._fetch, self._clock, self._sleep = fetch, clock, sleep
        self._last_request = None

    def _cache_file(self, url):
        return self.cache_dir / (hashlib.sha256(url.encode()).hexdigest()[:32] + ".json")

    def _read_cache(self, url):
        try:
            entry = json.loads(self._cache_file(url).read_text())
            return entry["time"], entry["data"]
        except (OSError, ValueError, KeyError, TypeError):
            return None, None

    def _write_cache(self, url, data):
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._cache_file(url).write_text(json.dumps({"time": self._clock(), "data": data}))
        except OSError:
            pass

    def _get(self, url):
        stamp, cached = self._read_cache(url)
        if stamp is not None and 0 <= self._clock() - stamp < TTL:
            return cached
        if self._last_request is not None:
            wait = MIN_INTERVAL - (self._clock() - self._last_request)
            if wait > 0:
                self._sleep(wait)
        self._last_request = self._clock()
        try:
            data = json.loads(self._fetch(url))
        except (OSError, ValueError) as e:
            if cached is not None:
                return cached
            if isinstance(e, ValueError):
                raise ApiError("respuesta de lutris.net no válida") from e
            raise ApiError("no se pudo conectar con lutris.net y no hay datos guardados") from e
        self._write_cache(url, data)
        return data

    @staticmethod
    def _items(data):
        if isinstance(data, dict):
            data = data.get("results", [])
        if not isinstance(data, list):
            raise ApiError("respuesta de lutris.net no válida")
        return [d for d in data if isinstance(d, dict)]

    def search(self, text):
        text = (text or "").strip()
        if len(text) < 2:
            return []
        url = f"{BASE}/games?{urllib.parse.urlencode({'search': text})}"
        return self._items(self._get(url))

    def installers(self, slug):
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            raise ApiError(f"slug no válido: {slug!r}")
        return self._items(self._get(f"{BASE}/installers/{slug}"))
