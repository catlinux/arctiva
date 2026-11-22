# SPDX-License-Identifier: GPL-3.0-or-later
import json

import pytest

from arctiva_games.core import games_api
from arctiva_games.core.games_api import ApiError, GamesApi


class Net:
    def __init__(self, body=None, fail=False):
        self.urls, self.body, self.fail = [], body, fail

    def __call__(self, url):
        self.urls.append(url)
        if self.fail:
            raise OSError("sin red")
        return self.body


class Clock:
    def __init__(self):
        self.now, self.slept = 1000.0, []

    def __call__(self):
        return self.now

    def sleep(self, s):
        self.slept.append(s)
        self.now += s


def make(tmp_path, net, clock=None):
    clock = clock or Clock()
    return GamesApi(tmp_path, net, clock, clock.sleep), clock


def test_busca_y_usa_cache(tmp_path):
    net = Net(json.dumps({"results": [{"slug": "ejemplo", "name": "Ejemplo"}]}))
    api, _ = make(tmp_path, net)
    assert api.search("ejemplo")[0]["slug"] == "ejemplo"
    assert api.search("ejemplo")[0]["slug"] == "ejemplo"
    assert len(net.urls) == 1 and "search=ejemplo" in net.urls[0]


def test_caduca_a_las_24_h(tmp_path):
    net = Net(json.dumps([{"slug": "a"}]))
    api, clock = make(tmp_path, net)
    api.installers("juego")
    clock.now += games_api.TTL + 1
    api.installers("juego")
    assert len(net.urls) == 2


def test_una_peticion_por_segundo(tmp_path):
    net = Net("[]")
    api, clock = make(tmp_path, net)
    api.installers("uno")
    api.installers("dos")
    assert len(net.urls) == 2 and clock.slept and clock.slept[0] == pytest.approx(1.0)


def test_sin_red_usa_cache_caducada(tmp_path):
    net = Net(json.dumps([{"slug": "a"}]))
    api, clock = make(tmp_path, net)
    api.installers("juego")
    clock.now += games_api.TTL * 3
    net.fail = True
    assert api.installers("juego") == [{"slug": "a"}]


def test_sin_red_ni_cache_es_error_claro(tmp_path):
    api, _ = make(tmp_path, Net(fail=True))
    with pytest.raises(ApiError, match="lutris.net"):
        api.search("ejemplo")


def test_respuesta_invalida(tmp_path):
    api, _ = make(tmp_path, Net("<html>"))
    with pytest.raises(ApiError):
        api.search("ejemplo")


def test_slug_invalido_no_hace_peticion(tmp_path):
    net = Net("[]")
    api, _ = make(tmp_path, net)
    for bad in ("../x", "a/b", "", "A B"):
        with pytest.raises(ApiError):
            api.installers(bad)
    assert api.search(" a ") == [] and net.urls == []


def test_user_agent_generico(monkeypatch):
    seen = {}

    class R:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self): return b"[]"

    def fake(req, timeout):
        seen["ua"] = req.get_header("User-agent")
        return R()
    monkeypatch.setattr(games_api.urllib.request, "urlopen", fake)
    games_api.default_fetch("https://lutris.net/api/games")
    assert seen["ua"].startswith("Arctiva-Games/")
