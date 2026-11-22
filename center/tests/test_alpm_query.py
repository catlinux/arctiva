# SPDX-License-Identifier: GPL-3.0-or-later
from types import SimpleNamespace as NS

from arctiva_center.core import alpm_query as aq


class FakeDb:
    def __init__(self, name, pkgs):
        self.name = name
        self._pkgs = {p.name: p for p in pkgs}
        self.pkgcache = list(pkgs)

    def get_pkg(self, name):
        return self._pkgs.get(name)


def pkg(name, version="1.0-1", dl=100, isize=300, reason=0):
    return NS(name=name, version=version, download_size=dl, isize=isize, reason=reason)


class FakeHandle:
    def __init__(self, root, db):
        self.args = (root, db)
        self.registered = []
        self.local = FakeDb("local", [pkg("nano", reason=0), pkg("libfoo", reason=1)])
        self.syncs = {"core": FakeDb("core", [pkg("nano", "9.3-1", 650)]),
                      "extra": FakeDb("extra", [pkg("krita", "6.0-1", 7000, 9000)]),
                      "multilib": FakeDb("multilib", [])}

    def register_syncdb(self, name, level):
        self.registered.append(name)
        return self.syncs[name]

    def get_localdb(self):
        return self.local


def test_sync_db_path(tmp_path):
    assert aq.sync_db_path({"CHECKUPDATES_DB": str(tmp_path)}) == tmp_path
    assert aq.sync_db_path({}).name == "syncdb"


def test_query():
    q = aq.AlpmQuery("/tmp/db", handle_factory=FakeHandle)
    assert q.handle.args == ("/", "/tmp/db") and q.handle.registered == ["core", "extra", "multilib"]
    assert q.installed_names() == {"nano", "libfoo"}
    assert q.explicit_names() == {"nano"}
    krita = q.info("krita")
    assert (krita.version, krita.repo, krita.download_size, krita.installed) == ("6.0-1", "extra", 7000, False)
    nano = q.info("nano")
    assert nano.installed and nano.repo == "core"
    assert q.info("no-existe") is None
    assert set(q.infos(["krita", "x", "nano"])) == {"krita", "nano"}
