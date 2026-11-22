# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Aplicaciones» (fase 6): catálogo de Arch y Flathub, búsqueda y operaciones.

El catálogo y las listas de instalados se cargan en un hilo para no congelar la ventana. Arch se
instala y quita con el ayudante privilegiado; Flatpak, con su propia línea de órdenes (decisiones 4 y
6 del plan de la fase 6)."""
import subprocess
import threading
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, QProcess, QProcessEnvironment, Signal, Slot

from .core import alpm_query, appstream, store

EX_UNAVAILABLE = 69
EX_NO_UPDATES_CHECK = 75


class AppsBackend(QObject):
    changed = Signal()
    log = Signal(str)
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
    def _begin(self, app_id, action):
        if self._op is not None or self._helper.running:
            return False
        if self._live:
            self.log.emit("arctiva-center: no disponible en la sesión live")
            self.finished.emit(EX_UNAVAILABLE, app_id, action)
            return False
        self._op = (app_id, action)
        self.changed.emit()
        return True

    def _end(self, code):
        op, self._op = self._op, None
        self._proc = None
        self.changed.emit()
        if op:
            self.finished.emit(code, op[0], op[1])
        self.refreshInstalled()

    @Slot(str, str)
    def install(self, app_id, kind):
        app = self._catalog.get(app_id) if self._catalog else None
        source = app.source(kind) if app else None
        if source is None or not self._begin(app_id, "install"):
            return
        self._pending = None
        if kind == "arch":
            self._check_updates(app_id, kind, source.ref)
        elif kind == "flathub":
            self._run_flatpak(store.flatpak_install_argv(source.ref))
        else:
            self._end(64)

    @Slot(str, str)
    def remove(self, app_id, kind):
        app = self._catalog.get(app_id) if self._catalog else None
        source = app.source(kind) if app else None
        if source is None or not self._begin(app_id, "remove"):
            return
        if kind == "arch":
            if not self._helper.run("app-remove", [source.ref]):
                self._end(64)
        elif kind == "flathub":
            self._run_flatpak(store.flatpak_uninstall_argv(source.ref))
        else:
            self._end(64)

    @Slot()
    def continuePending(self):
        if self._pending:
            app_id, kind = self._pending
            self._pending = None
            self.changed.emit()
            self.install(app_id, kind)

    @Slot()
    def discardPending(self):
        self._pending = None
        self.changed.emit()

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
            self.log.emit("checkupdates no está disponible")
            self._end(EX_NO_UPDATES_CHECK)

    def _updates_checked(self, code, app_id, kind, ref):
        if self._proc is not None:
            self._proc.deleteLater()
        self._proc = None   # a partir de aquí, lo que termine es el ayudante
        pending = store.checkupdates_pending(code)
        if pending is None:
            self.log.emit("No se ha podido comprobar si hay actualizaciones (¿sin conexión?)")
            self._end(EX_NO_UPDATES_CHECK)
        elif pending:
            self._pending = (app_id, kind)
            self._op = None
            self.changed.emit()
            self.updatesNeeded.emit(app_id, kind)
        elif not self._helper.run("app-install", [ref]):
            self._end(64)

    def _run_flatpak(self, argv):
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda: [self.log.emit(l) for l in bytes(proc.readAllStandardOutput()).decode("utf-8", "replace").splitlines() if l])
        proc.finished.connect(lambda code, status: self._flatpak_done(code if status == QProcess.ExitStatus.NormalExit else -1))
        proc.errorOccurred.connect(lambda e: self._flatpak_failed(e))
        self._proc = proc
        self.log.emit("$ " + " ".join(argv))
        proc.start(argv[0], argv[1:])

    def _flatpak_failed(self, error):
        if error == QProcess.ProcessError.FailedToStart and self._op is not None:
            self.log.emit("flatpak no se pudo iniciar")
            self._end(EX_UNAVAILABLE)

    def _flatpak_done(self, code):
        if self._proc is not None:
            self._proc.deleteLater()
        self._end(code)

    # --- ayudante (pacman) ---
    def _helper_line(self, text):
        if self._op is not None:
            self.log.emit(text)

    def _helper_finished(self, code):
        if self._op is not None and self._proc is None:
            self._end(code)
