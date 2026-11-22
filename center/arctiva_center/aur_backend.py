# SPDX-License-Identifier: GPL-3.0-or-later
"""AUR en Arctiva Center (decisión 7 de la fase 6): búsqueda, revisión, compilación como usuario e
instalación con el ayudante. Desactivado de serie; se activa en Aplicaciones tras un aviso.

Flujo de instalación: revisar (PKGBUILD y .install de todo lo que se va a compilar) → confirmar →
`aur-prepare` si faltan git o base-devel → `aur-deps` (repos) → para cada paquete del AUR, de las
dependencias al final: `makepkg` como usuario y `aur-install` con lo compilado."""
import shutil
import subprocess
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, QObject, QProcess, QProcessEnvironment, Signal, Slot

from .core import alpm_query, aur

EX_UNAVAILABLE = 69


class AurBackend(QObject):
    changed = Signal()
    log = Signal(str)
    finished = Signal(int)
    _searchDone = Signal(object)
    _reviewDone = Signal(object)
    _updatesDone = Signal(object)

    def __init__(self, helper, live=False, parent=None):
        super().__init__(parent)
        self._helper = helper
        self._live = live
        self._enabled = aur.aur_enabled()
        self._results = []
        self._query = ""
        self._busy = False
        self._error = ""
        self._review = {}
        self._updates = []
        self._steps = []
        self._proc = None
        self._plan = None
        self._clones = {}                 # nombre → (carpeta, commit)
        self._searchDone.connect(self._on_search)
        self._reviewDone.connect(self._on_review)
        self._updatesDone.connect(self._on_updates)
        helper.line.connect(self._helper_line)
        helper.finished.connect(self._helper_finished)

    # --- estado ---
    @Property(bool, notify=changed)
    def enabled(self):
        return self._enabled

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(list, notify=changed)
    def results(self):
        return self._results

    @Property(str, notify=changed)
    def query(self):
        return self._query

    @Property("QVariantMap", notify=changed)
    def review(self):
        return self._review

    @Property(list, notify=changed)
    def updates(self):
        return self._updates

    @Slot(bool)
    def setEnabled(self, enabled):
        aur.set_aur_enabled(enabled)
        self._enabled = enabled
        if not enabled:
            self._results, self._query, self._updates = [], "", []
        self.changed.emit()

    # --- búsqueda ---
    @Slot(str)
    def search(self, text):
        self._query = text.strip()
        self._results = []
        if not self._enabled or len(self._query) < 2:
            self.changed.emit()
            return
        self._busy, self._error = True, ""
        self.changed.emit()

        def work():
            try:
                self._searchDone.emit((self._query, aur.search(self._query), ""))
            except (aur.AurError, OSError) as e:
                self._searchDone.emit((self._query, [], str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _on_search(self, payload):
        query, packages, error = payload
        if query != self._query:
            return
        self._busy, self._error = False, error
        self._results = [{"name": p.name, "version": p.version, "description": p.description,
                          "votes": p.votes, "maintainer": p.maintainer} for p in packages[:40]]
        self.changed.emit()

    # --- revisión ---
    @Slot(str, bool)
    def prepare(self, name, update):
        """Reúne todo lo que el usuario debe revisar antes de instalar o actualizar `name`."""
        if not self._enabled or not aur.valid_name(name) or self._busy:
            return
        self._busy, self._error, self._review = True, "", {}
        self.changed.emit()
        threading.Thread(target=self._prepare_worker, args=(name, update), daemon=True).start()

    def _prepare_worker(self, name, update):
        try:
            found = aur.info([name])
            root = next((p for p in found if p.name == name), None)
            if root is None:
                raise aur.AurError("El paquete no existe en el AUR.")
            query = alpm_query.AlpmQuery()
            installed = query.installed_names()
            plan = aur.resolve(root, lambda d: d in installed or self._provided(query, d),
                               lambda d: self._in_repos(query, d))
            state = aur.load_state()
            entries, clones = [], {}
            for pkg in plan.aur_chain:
                folder, commit = aur.clone(pkg.base)
                hidden = aur.unreviewable(folder)
                if hidden:
                    raise aur.AurError(f"{pkg.name}: {', '.join(hidden)} es un enlace simbólico y no se puede revisar")
                clones[pkg.name] = (folder, commit)
                old = (state.get(pkg.name) or {}).get("commit")
                diff = ""
                if update and old and pkg.name == name:
                    diff = aur.diff_since(folder, old)
                entries.append({
                    "name": pkg.name, "base": pkg.base, "version": pkg.version, "description": pkg.description,
                    "votes": pkg.votes, "popularity": round(pkg.popularity, 2), "maintainer": pkg.maintainer,
                    "firstSubmitted": pkg.first_submitted, "lastModified": pkg.last_modified,
                    "warnings": aur.warnings(pkg, time.time()), "diff": diff,
                    "files": [{"name": n, "text": t} for n, t in aur.review_files(folder)]})
            self._reviewDone.emit({"name": name, "update": update, "plan": plan, "clones": clones, "packages": entries,
                                   "repoDeps": plan.repo_deps, "unresolved": plan.unresolved, "error": ""})
        except (aur.AurError, OSError, subprocess.SubprocessError) as e:
            self._reviewDone.emit({"error": str(e)})
        except Exception as e:  # el hilo no puede morir en silencio
            self._reviewDone.emit({"error": f"{type(e).__name__}: {e}"})

    @staticmethod
    def _in_repos(query, dep):
        return any(db.get_pkg(dep) for db in query.dbs) or any(
            dep in (p.split("=")[0] for p in pkg.provides) for db in query.dbs for pkg in db.pkgcache)

    @staticmethod
    def _provided(query, dep):
        return any(dep in (p.split("=")[0] for p in pkg.provides) for pkg in query._local.pkgcache)

    def _on_review(self, data):
        self._busy = False
        if data.get("error"):
            self._error, self._review = data["error"], {}
        else:
            self._plan, self._clones = data.pop("plan"), data.pop("clones")
            self._review = data
        self.changed.emit()

    # --- instalación ---
    @Slot()
    def install(self):
        """Solo tras la confirmación de la ventana: instala lo que acaba de revisarse."""
        if self._busy or self._helper.running or not self._review or self._plan is None:
            return
        if self._live:
            self.log.emit("arctiva-center: no disponible en la sesión live")
            self.finished.emit(EX_UNAVAILABLE)
            return
        if self._plan.unresolved:
            self.log.emit("Dependencias sin resolver: " + ", ".join(self._plan.unresolved))
            self.finished.emit(65)
            return
        steps = []
        if not (shutil.which("git") and shutil.which("makepkg") and shutil.which("gcc")):
            steps.append(("helper", "aur-prepare", []))
        if self._plan.repo_deps:
            steps.append(("helper", "aur-deps", list(self._plan.repo_deps)))
        for pkg in self._plan.aur_chain:
            steps.append(("build", pkg))
        self._steps = steps
        self._busy = True
        self.changed.emit()
        self._next()

    def _next(self):
        if not self._steps:
            self._finish(0)
            return
        step = self._steps.pop(0)
        if step[0] == "helper":
            self.log.emit(f"→ {step[1]} {' '.join(step[2])}")
            if not self._helper.run(step[1], step[2]):
                self._finish(64)
        else:
            self._build(step[1])

    def _helper_line(self, text):
        if self._busy and self._proc is None:
            self.log.emit(text)

    def _helper_finished(self, code):
        if not self._busy or self._proc is not None:
            return
        if code != 0:
            self._finish(code)
        elif self._installing:
            self._record_installed()
            self._next()
        else:
            self._next()

    _installing = False
    _current = None

    def _build(self, pkg):
        folder, commit = self._clones[pkg.name]
        work = aur.BUILD_DIR / pkg.base
        shutil.rmtree(work, ignore_errors=True)
        work.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(folder, work, ignore=shutil.ignore_patterns(".git"))
        self._current = (pkg, work, commit)
        self.log.emit(f"→ makepkg {pkg.name}")
        proc = QProcess(self)
        proc.setWorkingDirectory(str(work))
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("LC_ALL", "C.UTF-8")
        proc.setProcessEnvironment(env)
        proc.readyReadStandardOutput.connect(lambda: self._stream(proc))
        proc.finished.connect(lambda code, status: self._built(proc, code, status))
        proc.errorOccurred.connect(lambda e: self._build_failed(proc, e))
        self._proc = proc
        proc.start("makepkg", ["-f", "--noconfirm", "--nodeps", "--noprogressbar"])

    def _stream(self, proc):
        for line in bytes(proc.readAllStandardOutput()).decode("utf-8", "replace").splitlines():
            if line:
                self.log.emit(line)

    def _build_failed(self, proc, error):
        if error == QProcess.ProcessError.FailedToStart and self._proc is proc:
            self.log.emit("makepkg no se pudo iniciar")
            self._finish(EX_UNAVAILABLE)

    def _built(self, proc, code, status):
        self._stream(proc)
        proc.deleteLater()
        self._proc = None
        if code != 0 or status != QProcess.ExitStatus.NormalExit:
            self._finish(code or 1)
            return
        pkg, work, _ = self._current
        files = sorted(str(p) for p in work.glob("*.pkg.tar.zst") if "-debug-" not in p.name)
        if not files:
            self.log.emit("makepkg no ha dejado ningún paquete")
            self._finish(1)
            return
        self._installing = True
        self.log.emit(f"→ aur-install {pkg.name}")
        if not self._helper.run("aur-install", files):
            self._finish(64)

    def _record_installed(self):
        pkg, _, commit = self._current
        self._installing = False
        aur.record_install(pkg.name, pkg.base, commit, pkg.version)

    def _finish(self, code):
        self._busy = False
        self._installing = False
        self._steps = []
        self.changed.emit()
        self.finished.emit(code)

    # --- actualizaciones ---
    @Slot()
    def checkUpdates(self):
        if not self._enabled or self._busy:
            return
        self._busy, self._error = True, ""
        self.changed.emit()

        def work():
            try:
                import pyalpm
                # Solo lo que este Centro instaló (de eso guarda el commit para mostrar el diff).
                state = aur.load_state()
                foreign = {n: v for n, v in aur.foreign_packages().items() if n in state}
                newer = aur.newer_versions(foreign, pyalpm.vercmp)
                self._updatesDone.emit(([{"name": p.name, "old": foreign[p.name], "new": p.version} for p in newer], ""))
            except Exception as e:
                self._updatesDone.emit(([], str(e)))
        threading.Thread(target=work, daemon=True).start()

    def _on_updates(self, payload):
        self._updates, error = payload
        self._busy, self._error = False, error
        self.changed.emit()
