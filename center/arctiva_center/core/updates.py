# SPDX-License-Identifier: GPL-3.0-or-later
"""Actualizaciones (D-08): salida de checkupdates, pacman.log, noticias de Arch y paquetes delicados."""
import fnmatch
import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

NEWS_URL = "https://archlinux.org/feeds/news/"
NEWS_TIMEOUT = 10
NEWS_FALLBACK_DAYS = 30

# Cambios que piden reiniciar: kernel, controladores y bibliotecas que usa todo el sistema.
REBOOT_PATTERNS = ("linux*", "nvidia*", "systemd", "glibc", "mesa")


@dataclass(frozen=True)
class Update:
    name: str
    old: str
    new: str


@dataclass(frozen=True)
class News:
    guid: str
    title: str
    link: str
    published: datetime
    text: str

    @property
    def manual(self):
        return "manual intervention" in (self.title + " " + self.text).lower()


_CHECKUPDATES_RE = re.compile(r"(\S+) (\S+) -> (\S+)")


def parse_checkupdates(text):
    updates = []
    for line in text.splitlines():
        m = _CHECKUPDATES_RE.fullmatch(line.strip())
        if m:
            updates.append(Update(*m.groups()))
    return updates


def parse_flatpak_updates(text):
    """Salida de `flatpak remote-ls --updates --columns=application,name,version`: [Update] con
    el nombre legible y la versión nueva (vacía si el remoto no la indica)."""
    found = []
    for line in text.splitlines():
        cols = [c.strip() for c in line.split("	")]
        if cols and cols[0]:
            found.append(Update(cols[1] if len(cols) > 1 and cols[1] else cols[0], "",
                                cols[2] if len(cols) > 2 else ""))
    return found


_LOG_RE = re.compile(r"\[([^\]]+)\] \[(PACMAN|ALPM)\] (.*)")


def last_full_upgrade(log_text):
    """Fecha de la última actualización completa que terminó una transacción.

    pacman escribe «starting full system upgrade» aunque después falle (sin espacio, conflictos),
    así que solo cuenta si le sigue «transaction completed» antes de la siguiente orden. Una
    ejecución sin nada que hacer tampoco cuenta: en el peor caso se enseñan noticias ya vistas,
    nunca se esconde una nueva.
    """
    last = None
    started = None
    for line in log_text.splitlines():
        m = _LOG_RE.match(line)
        if not m:
            continue
        stamp, source, msg = m.groups()
        if source == "PACMAN" and msg.startswith("Running "):
            started = None
        elif source == "PACMAN" and msg == "starting full system upgrade":
            started = stamp
        elif source == "ALPM" and msg == "transaction completed" and started:
            when = _parse_stamp(started)
            if when:
                last = when
            started = None
    return last


def _parse_stamp(stamp):
    try:
        when = datetime.fromisoformat(stamp)
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_PUNCT_RE = re.compile(r"\s+([,.;:!?)])")


def parse_news(xml_text):
    root = ET.fromstring(xml_text)
    items = []
    for item in root.iterfind("channel/item"):
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", ""))
        except (TypeError, ValueError):
            continue
        description = item.findtext("description", "")
        text = " ".join(html.unescape(_TAG_RE.sub(" ", description)).split())
        # Las etiquetas se cambian por espacios: los que quedan antes de la puntuación sobran.
        text = _SPACE_PUNCT_RE.sub(r"\1", text)
        guid = item.findtext("guid") or item.findtext("link", "")
        items.append(News(guid, item.findtext("title", "").strip(), item.findtext("link", ""),
                          published, text))
    return items


def news_since(news, since, now=None):
    """Noticias posteriores a la última actualización; sin ninguna, las de los últimos 30 días."""
    if since is None:
        since = (now or datetime.now(timezone.utc)) - timedelta(days=NEWS_FALLBACK_DAYS)
    return sorted((n for n in news if n.published > since), key=lambda n: n.published, reverse=True)


def blocking_news(news, read_guids):
    return [n for n in news if n.manual and n.guid not in read_guids]


def matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, p) for p in patterns)


def delicate(updates, patterns):
    return [u for u in updates if matches(u.name, patterns)]


def needs_reboot(names):
    return any(matches(n, REBOOT_PATTERNS) for n in names)


def upgraded_packages(log_text, since):
    """Paquetes actualizados en pacman.log desde `since` (para recomendar reiniciar)."""
    names = []
    for line in log_text.splitlines():
        m = _LOG_RE.match(line)
        if not m or m.group(2) != "ALPM":
            continue
        when = _parse_stamp(m.group(1))
        if when and when >= since and m.group(3).startswith("upgraded "):
            names.append(m.group(3).split()[1])
    return names


class ReadNews:
    """Noticias marcadas como leídas, por GUID, en ~/.local/state/arctiva-center/news.json."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return set()
        return {g for g in data.get("read", []) if isinstance(g, str)} if isinstance(data, dict) else set()

    def mark(self, guid):
        read = self.load()
        read.add(guid)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"read": sorted(read)}, indent=1), encoding="utf-8")
        tmp.replace(self.path)
        return read
