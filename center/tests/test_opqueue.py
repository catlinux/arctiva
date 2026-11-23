# SPDX-License-Identifier: GPL-3.0-or-later
from arctiva_center.core import opqueue as oq


def test_add_and_order():
    q = oq.OpQueue()
    a = q.add("a", "arch", "install", "A")
    b = q.add("b", "flathub", "install", "B")
    assert q.next_queued() is a
    q.start(a)
    assert q.running() is a and q.next_queued() is b
    assert q.has_work()


def test_duplicate_active_is_refused_but_finished_is_replaced():
    q = oq.OpQueue()
    a = q.add("a", "arch", "install", "A")
    assert q.add("a", "arch", "install", "A") is None
    q.start(a)
    assert q.add("a", "arch", "remove", "A") is None        # en curso: tampoco
    q.finish(a, 1)
    again = q.add("a", "arch", "install", "A")
    assert again is not None and len(q.items) == 1           # el fallido anterior desaparece
    # otra fuente de la misma app es otra operación
    assert q.add("a", "flathub", "install", "A") is not None


def test_finish_states_and_fraction():
    q = oq.OpQueue()
    a, b = q.add("a", "arch", "install"), q.add("b", "arch", "install")
    q.start(a)
    q.finish(a, 0)
    q.start(b)
    q.finish(b, 126)
    assert (a.state, a.fraction) == (oq.DONE, 1.0)
    assert (b.state, b.code) == (oq.FAILED, 126)
    assert not q.has_work()


def test_blocked_is_not_work_and_can_be_replaced_or_discarded():
    q = oq.OpQueue()
    a = q.add("a", "arch", "install")
    q.start(a)
    q.block(a)
    assert not q.has_work() and q.running() is None
    assert q.add("a", "arch", "install") is not None         # se vuelve a pedir tras actualizar
    assert [i.state for i in q.items] == [oq.QUEUED]
    assert q.discard("a", "arch") and q.items == []


def test_discard_only_before_start():
    q = oq.OpQueue()
    a = q.add("a", "arch", "install")
    b = q.add("b", "arch", "install")
    q.start(a)
    assert not q.discard("a", "arch")                        # en curso: no se corta
    assert q.discard("b", "arch")
    assert q.items == [a] and b not in q.items


def test_clear_finished_keeps_active_and_blocked():
    q = oq.OpQueue()
    done, run, wait, blocked = (q.add(x, "arch", "install") for x in "drwb")
    q.start(done); q.finish(done, 0)
    q.start(blocked); q.block(blocked)
    q.start(run)
    q.clear_finished()
    assert {i.app_id for i in q.items} == {"r", "w", "b"}


def test_counts_for_batch_position():
    q = oq.OpQueue()
    items = [q.add(x, "arch", "install") for x in "abc"]
    assert q.counts() == (1, 3)
    q.start(items[0]); q.finish(items[0], 0)
    q.start(items[1])
    assert q.counts() == (2, 3)
    q.finish(items[1], 1); q.start(items[2]); q.finish(items[2], 0)
    assert q.counts() == (3, 3)
    assert oq.OpQueue().counts() == (0, 0)


def test_feed_parses_pacman_and_flatpak_progress():
    item = oq.Item("a", "arch", "install", "A")
    item.feed(":: Retrieving packages...")
    assert item.step == "Retrieving packages..." and item.fraction < 0
    item.feed("(2/8) installing foo")
    assert item.fraction == 0.25 and item.step == "installing foo"
    item.feed("(0/0) raro")
    assert item.fraction == 0.25                              # sin dividir entre cero
    fp = oq.Item("b", "flathub", "install")
    fp.feed("Installing org.kde.Platform")
    fp.feed("Instalando org.kde.Sdk")
    assert fp.steps == 2 and fp.fraction < 0


def test_log_is_capped():
    item = oq.Item("a", "arch", "install")
    for n in range(oq.MAX_LINES + 50):
        item.feed(f"línea {n}")
    assert len(item.lines) == oq.MAX_LINES
    assert item.lines[-1] == f"línea {oq.MAX_LINES + 49}"


def test_latest_and_summaries():
    q = oq.OpQueue()
    q.add("a", "arch", "install", "Aplicación")
    q.add("a", "flathub", "install", "Aplicación")
    assert q.latest("a").kind == "flathub"
    assert q.latest("zz") is None
    s = q.summaries()
    assert [x["kind"] for x in s] == ["arch", "flathub"] and s[0]["name"] == "Aplicación"
    assert oq.Item("x", "arch", "install").summary()["name"] == "x"
