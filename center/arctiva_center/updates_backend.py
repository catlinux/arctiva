# SPDX-License-Identifier: GPL-3.0-or-later
"""Módulo «Actualizaciones» (D-08): lo que ve la página QML y las tareas que la alimentan."""
import os
import threading
import tomllib
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Property, QDate, QLocale, QObject, QProcess, Signal, Slot

from .core import errors, helper_client, pacnew, updates

PACMAN_LOG = "/var/log/pacman.log"
STATE = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state") / "arctiva-center"


def _read(path):
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


class UpdatesBackend(QObject):
    changed = Signal()
    newsLoaded = Signal(list, str)
    flatpakLine = Signal(str)
    flatpakFinished = Signal(int)

    def __init__(self, data_dir, parent=None):
        super().__init__(parent)
        self._delicate = tomllib.loads(_read(Path(data_dir) / "delicate.toml") or "").get("patterns", [])
        try:
            self._errors = errors.ErrorCatalog.load(Path(data_dir) / "errors.toml")
        except (OSError, ValueError):
            self._errors = errors.ErrorCatalog([])
        self._read_news = updates.ReadNews(STATE / "news.json")
        self._checking = False
        self._updates = []
        self._news = []
        self._news_error = ""
        self._check_error = ""
        self._pacnew = []
        self._reboot = False
        self._explanation = {}
        self._started = None
        self._flatpak = None
        self.live = os.path.exists("/run/archiso")
        self.newsLoaded.connect(self._news_done)

    # --- propiedades para el QML ---
    @Property(bool, notify=changed)
    def checking(self):
        return self._checking

    @Property(list, notify=changed)
    def updates(self):
        return self._updates

    @Property(list, notify=changed)
    def news(self):
        return self._news

    @Property(str, notify=changed)
    def newsError(self):
        return self._news_error

    @Property(str, notify=changed)
    def checkError(self):
        return self._check_error

    @Property(bool, notify=changed)
    def blocked(self):
        return any(n["manual"] and not n["read"] for n in self._news)

    @Property(list, notify=changed)
    def pacnewFiles(self):
        return self._pacnew

    @Property(bool, notify=changed)
    def rebootRecommended(self):
        return self._reboot

    @Property("QVariantMap", notify=changed)
    def explanation(self):
        return self._explanation

    @Property(bool, constant=True)
    def isLive(self):
        return self.live

    # --- comprobar ---
    @Slot()
    def check(self):
        if self._checking:
            return
        self._checking = True
        self._check_error = ""
        self._explanation = {}
        self.changed.emit()
        proc = QProcess(self)
        proc.finished.connect(lambda code, _s, p=proc: self._checkupdates_done(p, code))
        proc.start("checkupdates", [])
        threading.Thread(target=self._fetch_news, daemon=True).start()
        self.refreshPacnew()

    def _checkupdates_done(self, proc, code):
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        err = bytes(proc.readAllStandardError()).decode("utf-8", "replace").strip()
        proc.deleteLater()
        # 0: hay actualizaciones; 2: no hay; otro: error (sin red, base bloqueada…).
        if code in (0, 2):
            found = updates.parse_checkupdates(out) if code == 0 else []
            marked = {u.name for u in updates.delicate(found, self._delicate)}
            self._updates = [{"name": u.name, "old": u.old, "new": u.new,
                              "delicate": u.name in marked} for u in found]
        else:
            self._updates = []
            self._check_error = err or f"checkupdates: {code}"
        self._checking = False
        self.changed.emit()

    def _fetch_news(self):
        # En un hilo: solo urllib y el análisis; el resultado vuelve por señal al hilo de Qt.
        try:
            with urllib.request.urlopen(updates.NEWS_URL, timeout=updates.NEWS_TIMEOUT) as r:
                items = updates.parse_news(r.read().decode("utf-8", "replace"))
        except Exception as e:  # sin red, tiempo agotado, XML roto: se avisa y se sigue
            self.newsLoaded.emit([], str(e) or e.__class__.__name__)
            return
        since = updates.last_full_upgrade(_read(PACMAN_LOG))
        shown = updates.news_since(items, since)
        self.newsLoaded.emit([{"guid": n.guid, "title": n.title, "link": n.link, "text": n.text,
                               "published": n.published.isoformat(), "manual": n.manual}
                              for n in shown], "")

    def _news_done(self, items, error):
        read = self._read_news.load()
        self._news = []
        for n in items:
            d = datetime.fromisoformat(n["published"]).astimezone()
            date = QLocale().toString(QDate(d.year, d.month, d.day), QLocale.FormatType.ShortFormat)
            self._news.append(dict(n, date=date, read=n["guid"] in read))
        self._news_error = error
        self.changed.emit()

    @Slot(str)
    def markRead(self, guid):
        read = self._read_news.mark(guid)
        self._news = [dict(n, read=n["guid"] in read) for n in self._news]
        self.changed.emit()

    # --- antes y después de actualizar ---
    @Slot()
    def updateStarted(self):
        self._started = datetime.now(timezone.utc)
        self._explanation = {}
        self._reboot = False
        self.changed.emit()

    @Slot(int, str)
    def updateFinished(self, code, log):
        if code == 0:
            names = updates.upgraded_packages(_read(PACMAN_LOG), self._started or datetime.now(timezone.utc))
            self._reboot = updates.needs_reboot(names)
            self._updates = []
            self.refreshPacnew()
        else:
            # 75: el ayudante encontró la base bloqueada sin llegar a ejecutar pacman.
            if code == helper_client.EX_TEMPFAIL:
                log += "\nerror: unable to lock database"
            e = self._errors.explain(log, QLocale().uiLanguages())
            self._explanation = {"id": e.id, "message": e.message, "action": e.action} if e else {}
        self.changed.emit()

    @Slot()
    def refreshPacnew(self):
        proc = QProcess(self)
        proc.finished.connect(lambda *_a, p=proc: self._pacdiff_done(p))
        proc.start("pacdiff", ["--output"])

    def _pacdiff_done(self, proc):
        out = bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        proc.deleteLater()
        self._pacnew = [{"path": p, "diff": pacnew.unified_diff(p) or ""}
                        for p in pacnew.parse_pacdiff(out)]
        self.changed.emit()

    # --- Flatpak, como usuario: flatpak pide su propia autorización si hace falta ---
    @Slot()
    def updateFlatpak(self):
        if self._flatpak is not None:
            return
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        proc.readyReadStandardOutput.connect(
            lambda p=proc: [self.flatpakLine.emit(l) for l in
                            bytes(p.readAllStandardOutput()).decode("utf-8", "replace").splitlines()])
        proc.finished.connect(lambda code, _s, p=proc: self._flatpak_done(p, code))
        proc.errorOccurred.connect(lambda _e, p=proc: self._flatpak_done(p, -1))
        self._flatpak = proc
        proc.start("flatpak", ["update", "--noninteractive"])

    def _flatpak_done(self, proc, code):
        if self._flatpak is not proc:
            return
        self._flatpak = None
        proc.deleteLater()
        self.flatpakFinished.emit(code)

    @Slot()
    def reboot(self):
        QProcess.startDetached("systemctl", ["reboot"])
