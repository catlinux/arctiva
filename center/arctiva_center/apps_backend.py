# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Aplicaciones» (fase 6): catálogo de Arch y Flathub, búsqueda y operaciones.

El catálogo y las listas de instalados se cargan en un hilo para no congelar la ventana. Arch se
instala y quita con el ayudante privilegiado; Flatpak, con su propia línea de órdenes (decisiones 4 y
6 del plan de la fase 6)."""
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, QProcess, QProcessEnvironment, QTimer, Signal, Slot

from .core import alpm_query, appstream, opqueue, store

EX_UNAVAILABLE = 69
EX_NO_UPDATES_CHECK = 75


class AppsBackend(QObject):
    changed = Signal()
    log = Signal(str)
    logFor = Signal(str, str)               # id de la aplicación, línea
    queueChanged = Signal()                 # estado, progreso o contenido de la cola
    finished = Signal(int, str, str)        # código, id de la aplicación, «install» o «remove»
    updatesNeeded = Signal(str, str)        # id, fuente: hay actualizaciones pendientes antes de instalar
    _loadDone = Signal(object)

    def __init__(self, data_dir, helper, live=False, parent=None):
        super().__init__(parent)
        self._data = Path(data_dir)
        self._helper = helper
        self._live = live
        self._catalog = None
        self._pacman = set()
        self._flatpak = set()
        self._loading = False
        self._error = ""
        self._results = []
        self._query = ""
        self._category = ""
        self._op = None                     # (id, acción) mientras hay una operación en marcha
        self._queue = opqueue.OpQueue()     # instalar y quitar se acumulan y van de una en una
        self._proc = None
        self._pending = None                # (id, fuente) a la espera de actualizar el sistema
        self._loadDone.connect(self._on_loaded)
        helper.line.connect(self._helper_line)
        helper.finished.connect(self._helper_finished)

    # --- estado visible ---
    @Property(bool, notify=changed)
    def loading(self):
        return self._loading

    @Property(bool, notify=changed)
    def loaded(self):
        return self._catalog is not None

    @Property(str, notify=changed)
    def error(self):
        return self._error

    @Property(bool, notify=changed)
    def busy(self):
        return self._op is not None

    @Property(list, notify=queueChanged)
    def queue(self):
        return self._queue.summaries()

    @Property(bool, notify=queueChanged)
    def queueActive(self):
        return self._queue.has_work()

    @Property("QVariantMap", notify=queueChanged)
    def queueProgress(self):
        """Resumen para la barra global: qué se está haciendo, cuántas van y el progreso de la actual."""
        item = self._queue.running()
        position, total = self._queue.counts()
        if item is None:
            return {"active": False, "position": position, "total": total}
        return {"active": True, "position": position, "total": total, "name": item.name or item.app_id,
                "action": item.action, "fraction": item.fraction, "step": item.step}

    @Slot(str, result="QVariantMap")
    def itemInfo(self, app_id):
        """Estado y registro de la última operación de una aplicación, para reconstruir su ficha."""
        item = self._queue.latest(app_id)
        if item is None:
            return {}
        return {**item.summary(), "log": "\n".join(item.lines)}

    @Slot(str, str)
    def cancelQueued(self, app_id, kind):
        if self._queue.discard(app_id, kind):
            if self._pending and self._pending[0] == app_id:
                self._pending = None
            self.changed.emit()
            self.queueChanged.emit()

    @Slot()
    def clearFinished(self):
        self._queue.clear_finished()
        self.queueChanged.emit()

    @Property(list, notify=changed)
    def results(self):
        return self._results

    @Property(list, notify=changed)
    def featured(self):
        if self._catalog is None:
            return []
        apps = appstream.load_featured(self._data / "featured.toml", self._catalog)
        return [store.app_summary(a, self._pacman, self._flatpak) for a in apps]

    @Property(list, notify=changed)
    def categories(self):
        if self._catalog is None:
            return []
        return [{"id": c, "count": n} for c, n in self._catalog.category_counts().items() if n]

    @Property(str, notify=changed)
    def query(self):
        return self._query

    @Property(str, notify=changed)
    def category(self):
        return self._category

    @Property("QVariantMap", notify=changed)
    def pending(self):
        if self._pending is None or self._catalog is None:
            return {}
        app = self._catalog.get(self._pending[0])
        return {"id": self._pending[0], "kind": self._pending[1], "name": app.name if app else ""}

    # --- carga ---
    @Slot()
    def load(self):
        if self._loading or self._catalog is not None:
            return
        self._loading = True
        self._error = ""
        self.changed.emit()
        languages = QLocale().uiLanguages()
        threading.Thread(target=self._load_worker, args=(languages,), daemon=True).start()

    @Slot()
    def reload(self):
        self._catalog = None
        self.load()

    def _load_worker(self, languages):
        try:
            flathub = Path(appstream.FLATHUB_DIR) / "appstream.xml.gz"
            if store.appstream_stale(flathub):
                # Flathub no trae su catálogo hasta pedirlo; sin red, se sigue con lo que haya.
                try:
                    subprocess.run(store.flatpak_refresh_argv(), capture_output=True, timeout=120)
                except (OSError, subprocess.SubprocessError):
                    pass
            cache = Path.home() / ".cache" / "arctiva-center" / "catalog.pickle"
            icons = [appstream.ARCH_ICON_DIR, str(Path(appstream.FLATHUB_DIR) / "icons")]
            catalog = appstream.load_cached(appstream.default_files(), cache, languages, icons,
                                            appstream.load_sources(self._data / "sources.toml"))
            self._loadDone.emit((catalog, self._read_pacman(), self._read_flatpak(), ""))
        except Exception as e:  # el hilo no puede morir en silencio
            self._loadDone.emit((None, set(), set(), str(e)))

    @staticmethod
    def _read_pacman():
        try:
            out = subprocess.run(["pacman", "-Qq"], capture_output=True, text=True, timeout=30)
            return set(out.stdout.split()) if out.returncode == 0 else set()
        except (OSError, subprocess.SubprocessError):
            return set()

    @staticmethod
    def _read_flatpak():
        try:
            out = subprocess.run(store.flatpak_list_argv(), capture_output=True, text=True, timeout=30)
            return store.parse_flatpak_list(out.stdout) if out.returncode == 0 else set()
        except (OSError, subprocess.SubprocessError):
            return set()

    def _on_loaded(self, payload):
        catalog, self._pacman, self._flatpak, error = payload
        self._catalog, self._error, self._loading = catalog, error, False
        self._refilter()
        self.changed.emit()

    @Slot()
    def refreshInstalled(self):
        def work():
            self._loadDone.emit((self._catalog, self._read_pacman(), self._read_flatpak(), self._error))
        threading.Thread(target=work, daemon=True).start()

    # --- búsqueda ---
    def _refilter(self):
        if self._catalog is None:
            self._results = []
        elif self._query:
            apps = self._catalog.search(self._query)
        elif self._category:
            apps = self._catalog.category(self._category)
        else:
            apps = []
        if self._catalog is not None:
            self._results = [store.app_summary(a, self._pacman, self._flatpak) for a in apps]

    @Slot(str)
    def search(self, text):
        self._query = text.strip()
        self._category = ""
        self._refilter()
        self.changed.emit()

    @Slot(str)
    def selectCategory(self, category):
        self._query = ""
        self._category = category
        self._refilter()
        self.changed.emit()

    @Slot()
    def clearFilter(self):
        self._query = self._category = ""
        self._refilter()
        self.changed.emit()

    @Slot(str, result="QVariantMap")
    def detail(self, app_id):
        app = self._catalog.get(app_id) if self._catalog else None
        if app is None:
            return {}
        try:
            alpm = alpm_query.AlpmQuery().infos([s.ref for s in app.sources if s.kind == "arch"])
        except Exception:  # sin pyalpm o sin base temporal: se muestra sin versión
            alpm = {}
        return store.app_detail(app, self._pacman, self._flatpak, alpm)

    # --- operaciones ---
    def _log(self, text):
        item = self._queue.running()
        if item is not None:
            item.feed(text)
            self.logFor.emit(item.app_id, text)
            self.queueChanged.emit()
        self.log.emit(text)

    def _enqueue(self, app_id, kind, action):
        app = self._catalog.get(app_id) if self._catalog else None
        if app is None or app.source(kind) is None:
            return
        if self._live:
            self.log.emit("arctiva-center: no disponible en la sesión live")
            self.finished.emit(EX_UNAVAILABLE, app_id, action)
            return
        if self._queue.add(app_id, kind, action, app.name) is None:
            return
        self.changed.emit()
        self.queueChanged.emit()
        self._pump()

    def _pump(self):
        """Arranca la siguiente operación de la cola si no hay ninguna en marcha."""
        if self._op is not None or self._helper.running:
            return
        item = self._queue.next_queued()
        if item is None:
            return
        app = self._catalog.get(item.app_id) if self._catalog else None
        source = app.source(item.kind) if app else None
        self._queue.start(item)
        self._op = (item.app_id, item.action)
        self.changed.emit()
        self.queueChanged.emit()
        if source is None:
            self._end(64)
        elif item.action == "remove":
            if item.kind == "arch":
                if not self._helper.run("app-remove", [source.ref]):
                    self._end(64)
            elif item.kind == "flathub":
                self._run_flatpak(store.flatpak_uninstall_argv(source.ref))
            else:
                self._end(64)
        elif item.kind == "arch":
            self._check_updates(item.app_id, item.kind, source.ref)
        elif item.kind == "flathub":
            self._run_flatpak(store.flatpak_install_argv(source.ref))
        else:
            self._end(64)

    def _end(self, code):
        op, self._op = self._op, None
        self._proc = None
        item = self._queue.running()
        if item is not None:
            self._queue.finish(item, code)
        self.changed.emit()
        self.queueChanged.emit()
        if op:
            self.finished.emit(code, op[0], op[1])
        self.refreshInstalled()
        QTimer.singleShot(0, self._pump)

    @Slot(str, str)
    def install(self, app_id, kind):
        self._enqueue(app_id, kind, "install")

    @Slot(str, str)
    def remove(self, app_id, kind):
        self._enqueue(app_id, kind, "remove")

    @Slot()
    def continuePending(self):
        if self._pending:
            app_id, kind = self._pending
            self._pending = None
            self.changed.emit()
            self._queue.discard(app_id, kind)       # el bloqueado se sustituye por uno nuevo
            self.install(app_id, kind)

    @Slot()
    def discardPending(self):
        if self._pending:
            self._queue.discard(*self._pending)
        self._pending = None
        self.changed.emit()
        self.queueChanged.emit()

    @Slot()
    def openPermissions(self):
        QProcess.startDetached("systemsettings", ["kcm_app-permissions"])

    # Hay que actualizar antes de instalar desde Arch: D-07 no admite actualizaciones parciales.
    def _check_updates(self, app_id, kind, ref):
        proc = QProcess(self)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("CHECKUPDATES_DB", str(alpm_query.sync_db_path()))
        proc.setProcessEnvironment(env)
        self._proc = proc
        proc.finished.connect(lambda code, _s: self._updates_checked(code, app_id, kind, ref))
        proc.errorOccurred.connect(lambda e: self._updates_failed(e))
        proc.start("checkupdates")

    def _updates_failed(self, error):
        if error == QProcess.ProcessError.FailedToStart and self._op is not None:
            self._log("checkupdates no está disponible")
            self._end(EX_NO_UPDATES_CHECK)

    def _updates_checked(self, code, app_id, kind, ref):
        if self._proc is not None:
            self._proc.deleteLater()
        self._proc = None   # a partir de aquí, lo que termine es el ayudante
        pending = store.checkupdates_pending(code)
        if pending is None:
            self._log("No se ha podido comprobar si hay actualizaciones (¿sin conexión?)")
            self._end(EX_NO_UPDATES_CHECK)
        elif pending:
            item = self._queue.running()
            if item is not None:
                self._queue.block(item)
            self._pending = (app_id, kind)
            self._op = None
            self.changed.emit()
            self.queueChanged.emit()
            self.updatesNeeded.emit(app_id, kind)
            QTimer.singleShot(0, self._pump)
        elif not self._helper.run("app-install", [ref]):
            self._end(64)

    def _run_flatpak(self, argv):
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: [self._log(l) for l in bytes(proc.readAllStandardOutput()).decode("utf-8", "replace").splitlines() if l])
        proc.finished.connect(lambda code, status: self._flatpak_done(code if status == QProcess.ExitStatus.NormalExit else -1))
        proc.errorOccurred.connect(lambda e: self._flatpak_failed(e))
        self._proc = proc
        self._log("$ " + " ".join(argv))
        proc.start(argv[0], argv[1:])

    def _flatpak_failed(self, error):
        if error == QProcess.ProcessError.FailedToStart and self._op is not None:
            self._log("flatpak no se pudo iniciar")
            self._end(EX_UNAVAILABLE)

    def _flatpak_done(self, code):
        if self._proc is not None:
            self._proc.deleteLater()
        self._end(code)

    # --- ayudante (pacman) ---
    def _helper_line(self, text):
        if self._op is not None:
            self._log(text)

    def _helper_finished(self, code):
        if self._op is not None and self._proc is None:
            self._end(code)
        else:
            QTimer.singleShot(0, self._pump)    # terminó otra tarea del ayudante: sigue la cola
