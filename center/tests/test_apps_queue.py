# SPDX-License-Identifier: GPL-3.0-or-later
"""La cola de AppsBackend con un ayudante y un catálogo de mentira: orden, de una en una y estados."""
import time
from types import SimpleNamespace as NS

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QCoreApplication, QObject, QTimer, Signal  # noqa: E402

from arctiva_center import apps_backend as ab  # noqa: E402
from arctiva_center.core import store  # noqa: E402


class FakeHelper(QObject):
    line = Signal(str)
    finished = Signal(int)

    def __init__(self):
        super().__init__()
        self.running = False
        self.calls = []
        self.result = 0

    def run(self, action, args):
        self.calls.append((action, tuple(args)))
        self.running = True

        def end():
            self.line.emit("(1/2) descargando")
            self.line.emit("(2/2) instalando")
            self.running = False
            self.finished.emit(self.result)
        QTimer.singleShot(30, end)
        return True


class FakeCatalog:
    def __init__(self, apps):
        self.apps = apps

    def get(self, app_id):
        return self.apps.get(app_id)


def make_app(name, kinds):
    return NS(name=name, source=lambda kind: NS(ref=f"{name}-{kind}") if kind in kinds else None)


@pytest.fixture
def qapp():
    return QCoreApplication.instance() or QCoreApplication([])


@pytest.fixture
def backend(qapp, monkeypatch, tmp_path):
    helper = FakeHelper()
    b = ab.AppsBackend(tmp_path, helper, live=False)
    b._catalog = FakeCatalog({"a": make_app("A", ("arch",)), "b": make_app("B", ("flathub",)),
                              "c": make_app("C", ("arch",)), "both": make_app("Both", ("arch", "flathub"))})
    monkeypatch.setattr(b, "refreshInstalled", lambda: None)
    # checkupdates real no existe en las pruebas: se da por bueno y se sigue con el ayudante.
    monkeypatch.setattr(b, "_check_updates", lambda app_id, kind, ref: helper.run("app-install", [ref]))
    monkeypatch.setattr(store, "flatpak_install_argv",
                        lambda ref: ["sh", "-c", f"echo 'Installing {ref}'; sleep 0.05"])
    monkeypatch.setattr(store, "flatpak_uninstall_argv", lambda ref: ["sh", "-c", f"echo 'Uninstalling {ref}'"])
    return b


def wait_until(app, cond, timeout=8.0):
    end = time.time() + timeout
    while not cond() and time.time() < end:
        app.processEvents()
        time.sleep(0.005)
    assert cond(), "tiempo agotado"


def test_queue_runs_one_by_one_in_order(qapp, backend):
    order, concurrent = [], []
    backend.finished.connect(lambda code, app_id, action: order.append((code, app_id, action)))
    backend.queueChanged.connect(lambda: concurrent.append(
        sum(1 for i in backend.queue if i["state"] == "running")))
    backend.install("a", "arch")
    backend.install("b", "flathub")
    backend.install("c", "arch")
    assert [i["state"] for i in backend.queue] == ["running", "queued", "queued"]
    assert backend.queueActive and backend.busy
    wait_until(qapp, lambda: not backend.queueActive)
    assert order == [(0, "a", "install"), (0, "b", "install"), (0, "c", "install")]
    assert max(concurrent) == 1
    assert [i["state"] for i in backend.queue] == ["done"] * 3
    assert not backend.busy


def test_progress_and_log_are_kept_per_item(qapp, backend):
    backend.install("a", "arch")
    wait_until(qapp, lambda: not backend.queueActive)
    info = backend.itemInfo("a")
    assert info["state"] == "done" and info["fraction"] == 1.0
    assert "(2/2) instalando" in info["log"]
    assert backend.itemInfo("zz") == {}


def test_failure_does_not_stop_the_queue(qapp, backend):
    backend._helper.result = 126
    backend.install("a", "arch")
    backend.install("b", "flathub")
    wait_until(qapp, lambda: not backend.queueActive)
    states = {i["id"]: (i["state"], i["code"]) for i in backend.queue}
    assert states["a"] == ("failed", 126) and states["b"][0] == "done"


def test_duplicates_and_cancel(qapp, backend):
    backend.install("a", "arch")
    backend.install("a", "arch")          # repetida: se ignora
    backend.install("c", "arch")
    assert len(backend.queue) == 2
    backend.cancelQueued("a", "arch")       # en curso: no se corta
    backend.cancelQueued("c", "arch")       # en cola: se quita
    assert [i["id"] for i in backend.queue] == ["a"]
    wait_until(qapp, lambda: not backend.queueActive)
    backend.clearFinished()
    assert backend.queue == []


def test_remove_and_other_helper_task_delays_start(qapp, backend):
    backend._helper.running = True          # p. ej. una actualización en marcha
    backend.install("a", "arch")
    assert backend.queue[0]["state"] == "queued"
    backend._helper.running = False
    backend._helper.finished.emit(0)
    wait_until(qapp, lambda: not backend.queueActive)
    assert backend._helper.calls == [("app-install", ("A-arch",))]
    backend.remove("b", "flathub")
    wait_until(qapp, lambda: not backend.queueActive)
    assert backend.itemInfo("b")["action"] == "remove"


def test_blocked_when_updates_are_pending(qapp, backend, monkeypatch):
    seen = []
    backend.updatesNeeded.connect(lambda app_id, kind: seen.append((app_id, kind)))
    monkeypatch.setattr(backend, "_check_updates", lambda app_id, kind, ref: backend._updates_checked(1, app_id, kind, ref))
    monkeypatch.setattr(store, "checkupdates_pending", lambda code: True)
    backend.install("a", "arch")
    backend.install("b", "flathub")
    wait_until(qapp, lambda: not backend.queueActive)
    states = {i["id"]: i["state"] for i in backend.queue}
    assert states == {"a": "blocked", "b": "done"}
    assert seen == [("a", "arch")] and backend.pending["id"] == "a"
    backend.discardPending()
    assert [i["id"] for i in backend.queue] == ["b"]


def test_live_session_refuses(qapp, backend):
    backend._live = True
    codes = []
    backend.finished.connect(lambda code, app_id, action: codes.append(code))
    backend.install("a", "arch")
    assert codes == [ab.EX_UNAVAILABLE] and backend.queue == []
