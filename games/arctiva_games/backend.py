# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: buscar, instalar paso a paso y lanzar juegos de Windows con Wine.

Todo corre como el usuario, sin ayudante ni polkit (D-G1). Las llamadas de red y las descargas van en
hilos y devuelven el resultado por señales (se encolan en el hilo de la interfaz)."""
import json
import os
import shutil
import threading
import time
from pathlib import Path

import yaml
from PySide6.QtCore import Property, QObject, QProcess, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QGuiApplication

from .core import (games_api, games_engine, games_library, games_procs, games_recipes, games_runners,
                   games_runtime, games_script, games_shortcuts)


class GamesBackend(QObject):
    changed = Signal()
    procsChanged = Signal()
    logLine = Signal(str)
    stepsChanged = Signal()
    installFinished = Signal(bool)
    _searchDone = Signal(list, str)
    _installersDone = Signal(list, str)
    _downloaded = Signal(object, str)

    def __init__(self, data_dir, live=False, parent=None, api=None, base=None, root=None, downloads=None,
                 runners=None, menu_dir=None, desk_dir=None):
        super().__init__(parent)
        self._live = live
        self._api = api or games_api.GamesApi()
        self._base = Path(base) if base else games_library.BASE
        self._root = Path(root) if root else games_library.ROOT
        self._downloads = Path(downloads) if downloads else games_runtime.DOWNLOADS
        self._recipes = games_recipes.load(data_dir)
        # `runners()` → (lista de Runner, ruta de umu-run o None); se sustituye en las pruebas.
        self._scan = runners or (lambda: (games_runners.list_runners(), games_runners.find_umu()))
        self._runners, self._umu, self._runner, self._pref = [], None, None, None
        self._menu_dir = Path(menu_dir) if menu_dir else games_shortcuts.MENU_DIR
        self._desk_dir = Path(desk_dir) if desk_dir else None
        self._opt_menu, self._opt_desktop = True, False
        self._results, self._searching, self._error = [], False, ""
        self._plan, self._script, self._summary, self._warnings = None, None, {}, []
        self._engine, self._states, self._waiting, self._detailed = None, [], "", False
        self._phase = "idle"     # idle | ready | downloading | installing | done | failed
        self._procs, self._monitor, self._play = [], None, None
        self._log_path = ""
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._poll)
        self._searchDone.connect(self._on_search)
        self._installersDone.connect(self._on_installers)
        self._downloaded.connect(self._on_downloaded)

    # --- propiedades ---
    live = Property(bool, lambda s: s._live, constant=True)
    recipes = Property(list, lambda s: [{k: r[k] for k in ("slug", "name", "description")}
                                        for r in s._recipes], constant=True)
    results = Property(list, lambda s: s._results, notify=changed)
    searching = Property(bool, lambda s: s._searching, notify=changed)
    error = Property(str, lambda s: s._error, notify=changed)
    phase = Property(str, lambda s: s._phase, notify=changed)
    summary = Property("QVariantMap", lambda s: s._summary, notify=changed)
    warnings = Property(list, lambda s: s._warnings, notify=changed)
    waiting = Property(str, lambda s: s._waiting, notify=changed)
    procs = Property(list, lambda s: s._procs, notify=procsChanged)
    logPath = Property(str, lambda s: s._log_path, notify=changed)
    detailed = Property(bool, lambda s: s._detailed, lambda s, v: s._set_detailed(v), notify=changed)

    @Property(list, notify=stepsChanged)
    def steps(self):
        if not self._plan:
            return []
        return [{"description": s.description, "state": self._states[i] if i < len(self._states) else "pending"}
                for i, s in enumerate(self._plan.steps)]

    @Property(list, notify=changed)
    def runnerChoices(self):
        return [r.name for r in self._runners if self._umu or not r.is_proton]

    @Property(str, notify=changed)
    def runnerName(self):
        return self._runner.name if self._runner else ""

    @Slot(str)
    def setRunner(self, name):
        runner = games_runners.by_name(name, self._runners)
        if runner and self._phase == "ready" and (self._umu or not runner.is_proton):
            self._runner = runner
            self._refresh_warnings()
            self.changed.emit()

    @Property(bool, notify=changed)
    def shortcutMenu(self):
        return self._opt_menu

    @shortcutMenu.setter
    def shortcutMenu(self, value):
        self._opt_menu = bool(value)
        self.changed.emit()

    @Property(bool, notify=changed)
    def shortcutDesktop(self):
        return self._opt_desktop

    @shortcutDesktop.setter
    def shortcutDesktop(self, value):
        self._opt_desktop = bool(value)
        self.changed.emit()

    @Property(list, notify=changed)
    def library(self):
        out = []
        for g in games_library.list_games(self._base):
            st = games_shortcuts.status(g.slug, self._menu_dir, self._desk_dir)
            out.append({"slug": g.slug, "name": g.name, "runner": Path(g.runner).name if g.runner != "wine" else "wine",
                        "menu": st["menu"], "desktop": st["desktop"]})
        return out

    @Slot(str, str, bool)
    def setShortcut(self, slug, kind, enabled):
        game = games_library.get(slug, self._base)
        if game is None or kind not in ("menu", "desktop"):
            return
        if enabled:
            games_shortcuts.create(game, kind == "menu", kind == "desktop", self._menu_dir, self._desk_dir)
        else:
            current = games_shortcuts.status(slug, self._menu_dir, self._desk_dir)
            games_shortcuts.remove(slug, self._menu_dir, self._desk_dir)
            if kind == "menu" and current["desktop"]:
                games_shortcuts.create(game, False, True, self._menu_dir, self._desk_dir)
            if kind == "desktop" and current["menu"]:
                games_shortcuts.create(game, True, False, self._menu_dir, self._desk_dir)
        self.changed.emit()

    def _set_detailed(self, value):
        self._detailed = bool(value)
        self.changed.emit()

    # --- búsqueda y plan ---
    @Slot(str)
    def search(self, text):
        if self._searching:
            return
        self._searching, self._error = True, ""
        self.changed.emit()

        def work():
            try:
                self._searchDone.emit(self._api.search(text), "")
            except games_api.ApiError as e:
                self._searchDone.emit([], str(e))
        threading.Thread(target=work, daemon=True).start()

    def _on_search(self, results, error):
        self._results = [{"slug": r.get("slug", ""), "name": r.get("name", ""), "year": r.get("year") or ""}
                         for r in results if games_library.valid_slug(r.get("slug", ""))]
        self._searching, self._error = False, error
        self.changed.emit()

    @Slot(str)
    def prepareRecipe(self, slug):
        recipe = next((r for r in self._recipes if r["slug"] == slug), None)
        if recipe:
            self._prepare(recipe["script"], recipe.get("runners"))

    @Slot(str)
    def prepareOnline(self, slug):
        self._error = ""
        self._phase = "idle"
        self.changed.emit()

        def work():
            try:
                self._installersDone.emit(self._api.installers(slug), "")
            except games_api.ApiError as e:
                self._installersDone.emit([], str(e))
        threading.Thread(target=work, daemon=True).start()

    def _on_installers(self, installers, error):
        wine = [i for i in installers if str(i.get("runner", "wine")) == "wine"]
        if error or not wine:
            self._error = error or "Este juego no tiene un instalador para Wine."
            self.changed.emit()
            return
        item = dict(wine[0])
        if not isinstance(item.get("script"), dict) and isinstance(item.get("content"), str):
            try:
                item["script"] = yaml.safe_load(item["content"])
            except yaml.YAMLError:
                pass
        self._prepare(json.dumps({k: v for k, v in item.items() if k != "content"}, default=str))

    def _prepare(self, text, preference=None):
        try:
            script = games_script.parse(text)
            plan = games_script.plan(script, games_library.game_dir(script.slug or "juego", self._root))
        except games_script.UnsupportedCommand as e:
            self._error = f"Este instalador usa «{e.name}», que Arctiva Games todavía no soporta."
            self.changed.emit()
            return
        except (games_script.ScriptError, games_library.LibraryError) as e:
            self._error = str(e)
            self.changed.emit()
            return
        self._script, self._plan, self._error = script, plan, ""
        self._summary = games_script.summary(plan)
        self._runners, self._umu = self._scan()
        self._runner = games_runners.choose(preference, self._runners, self._umu is not None)
        self._refresh_warnings()
        self._states = ["pending"] * len(plan.steps)
        self._phase = "ready"
        self.changed.emit()
        self.stepsChanged.emit()

    def _refresh_warnings(self):
        warnings = games_runtime.unsupported_steps(self._plan)
        if self._runner is None:
            warnings.append("no hay ningún ejecutor de Wine: instala wine o un Proton (GE-Proton) con ProtonPlus"
                            + ("" if self._umu else " y el paquete umu-launcher"))
        elif not self._runner.is_proton and self._summary["winetricks"] and shutil.which("winetricks") is None:
            warnings.append("falta el paquete winetricks (pacman -S winetricks)")
        self._warnings = warnings

    # --- instalación ---
    @Slot()
    def install(self):
        if self._live or self._phase != "ready" or self._warnings:
            return
        self._phase = "downloading"
        self.changed.emit()
        plan = self._plan

        def work():
            try:
                self._downloaded.emit(games_runtime.download_files(plan, self._downloads, self.logLine.emit), "")
            except games_runtime.DownloadError as e:
                self._downloaded.emit(None, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _on_downloaded(self, files, error):
        if files is None:
            self._error, self._phase = error, "failed"
            self.logLine.emit(error)
            self.changed.emit()
            return
        runner = {"path": self._runner.path, "umu": self._umu} if self._runner and self._runner.is_proton else None
        engine = games_engine.GameEngine(self._plan, self._base, detailed=self._detailed, files=files,
                                         runner=runner, parent=self)
        self._engine = engine
        engine.stepChanged.connect(self._on_step)
        engine.logLine.connect(self.logLine)
        engine.waitingForUser.connect(lambda i, msg: self._set_waiting(msg))
        engine.finished.connect(self._on_finished)
        self._phase = "installing"
        self.changed.emit()
        engine.start()
        self._log_path = str(engine.log_path or "")
        self._monitor = games_procs.PrefixMonitor(self._plan.prefix)
        self._timer.start()
        self.changed.emit()

    def _set_waiting(self, message):
        self._waiting = message
        self.changed.emit()

    def _on_step(self, index, state):
        if index < len(self._states):
            self._states[index] = state
            self.stepsChanged.emit()

    def _on_finished(self, ok):
        self._waiting = ""
        self._timer.stop()
        if ok:
            self._register()
        self._phase = "done" if ok else "failed"
        self.changed.emit()
        self.installFinished.emit(ok)

    def _register(self):
        plan = self._plan
        exe = str(plan.game.get("exe") or "")
        env = {k: v for k, v in plan.env.items()}
        game = games_library.Game(plan.slug, plan.name or plan.slug, exe, plan.game_dir,
                                   plan.prefix, env, self._runner.path if self._runner and self._runner.is_proton else "wine")
        games_library.save(game, self._base)
        games_shortcuts.create(game, self._opt_menu, self._opt_desktop, self._menu_dir, self._desk_dir)

    @Slot()
    def retry(self):
        if self._engine:
            self._engine.retry()

    @Slot()
    def skip(self):
        if self._engine:
            self._engine.skip()

    @Slot()
    def continueInstall(self):
        if self._engine:
            self._waiting = ""
            self.changed.emit()
            self._engine.continue_()

    @Slot()
    def stopInstall(self):
        if self._engine:
            self._engine.stop()

    @Slot()
    def cancelPlan(self):
        if self._phase in ("ready", "done", "failed"):
            self._phase, self._plan, self._engine = "idle", None, None
            self._error = ""
            self.changed.emit()
            self.stepsChanged.emit()

    # --- procesos ---
    @Slot()
    def startMonitor(self):
        if self._monitor is not None:
            self._timer.start()

    @Slot()
    def stopMonitor(self):
        if self._play is None and self._phase != "installing":
            self._timer.stop()

    def _poll(self):
        if self._monitor is None:
            return
        alive, _new, gone = self._monitor.poll()
        for p in gone:
            self.logLine.emit(f"El proceso {p.name} (pid {p.pid}) ha terminado.")
        self._procs = [{"pid": p.pid, "name": p.name, "uptime": int(p.uptime)} for p in alive]
        self.procsChanged.emit()

    # --- biblioteca ---
    @Slot(str)
    def play(self, slug):
        game = games_library.get(slug, self._base)
        if game is None or self._play is not None:
            return
        try:
            program, args, env = games_library.launch_argv(game, games_runners.find_umu())
        except games_library.LibraryError as e:
            self._error = str(e)
            self.changed.emit()
            return
        if not self._detailed:
            env.setdefault("WINEDEBUG", "-all")
        logs = self._base / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        self._log_path = str(logs / f"{slug}-play-{time.strftime('%Y%m%d-%H%M%S')}.log")
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.setStandardOutputFile(self._log_path)
        qenv = proc.processEnvironment()
        for k, v in {**os.environ, **env}.items():
            qenv.insert(k, v)
        proc.setProcessEnvironment(qenv)
        proc.setWorkingDirectory(game.game_dir)
        proc.finished.connect(lambda *_: self._play_done())
        proc.errorOccurred.connect(lambda e: self._play_done()
                                   if e == QProcess.ProcessError.FailedToStart else None)
        self._play = proc
        self._monitor = games_procs.PrefixMonitor(game.prefix)
        self._timer.start()
        self.changed.emit()
        proc.start(program, args)

    def _play_done(self):
        proc, self._play = self._play, None
        if proc:
            proc.deleteLater()
        self._timer.stop()
        self.changed.emit()

    @Slot(str, result=bool)
    def uninstall(self, slug):
        try:
            games_library.remove(slug, self._base, self._root)
            games_shortcuts.remove(slug, self._menu_dir, self._desk_dir)
        except games_library.LibraryError as e:
            self._error = str(e)
            self.changed.emit()
            return False
        self.changed.emit()
        return True

    # --- registro ---
    @Slot()
    def openLog(self):
        if self._log_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._log_path))

    @Slot()
    def copyLog(self):
        try:
            QGuiApplication.clipboard().setText(Path(self._log_path).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
