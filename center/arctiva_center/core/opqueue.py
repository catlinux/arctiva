# SPDX-License-Identifier: GPL-3.0-or-later
"""Cola de operaciones de «Aplicaciones»: instalar y quitar se acumulan y se ejecutan de una en una.

Sin Qt, para poder probarla sola. Cada elemento guarda su estado, su registro y el progreso que se
deduce de la salida de pacman («(n/m) paquete») o de Flatpak (pasos tratados)."""
import re
from dataclasses import dataclass, field

QUEUED, RUNNING, DONE, FAILED, BLOCKED = "queued", "running", "done", "failed", "blocked"
ACTIVE = (QUEUED, RUNNING)
MAX_LINES = 400

_PACMAN = re.compile(r"^\((\d+)/(\d+)\)\s*(.*)$")
_STEP = re.compile(r"^(Instalando|Installing|Instal·lant|Actualizando|Updating|Actualitzant|"
                   r"Desinstalando|Uninstalling|Desinstal·lant)\s")


@dataclass
class Item:
    app_id: str
    kind: str
    action: str
    name: str = ""
    state: str = QUEUED
    code: int = 0
    fraction: float = -1.0              # < 0: sin porcentaje
    step: str = ""
    steps: int = 0
    lines: list = field(default_factory=list)

    def feed(self, text):
        self.lines.append(text)
        if len(self.lines) > MAX_LINES:
            del self.lines[:len(self.lines) - MAX_LINES]
        m = _PACMAN.match(text)
        if m and int(m.group(2)) > 0:
            self.fraction, self.step = int(m.group(1)) / int(m.group(2)), m.group(3)
        elif _STEP.match(text):
            self.steps += 1
            self.step = text
        elif text.startswith(":: "):
            self.step = text[3:]

    def summary(self):
        return {"id": self.app_id, "kind": self.kind, "action": self.action, "name": self.name or self.app_id,
                "state": self.state, "code": self.code, "fraction": self.fraction, "step": self.step,
                "steps": self.steps}


class OpQueue:
    def __init__(self):
        self.items = []

    def add(self, app_id, kind, action, name=""):
        """Añade una operación; None si esa misma ya está en cola o en curso."""
        if any(i.app_id == app_id and i.kind == kind and i.state in ACTIVE for i in self.items):
            return None
        # Lo terminado de la misma app y fuente se sustituye: solo importa el último resultado.
        self.items = [i for i in self.items if not (i.app_id == app_id and i.kind == kind)]
        item = Item(app_id, kind, action, name)
        self.items.append(item)
        return item

    def running(self):
        return next((i for i in self.items if i.state == RUNNING), None)

    def next_queued(self):
        return next((i for i in self.items if i.state == QUEUED), None)

    def start(self, item):
        item.state = RUNNING

    def finish(self, item, code):
        item.state, item.code = (DONE if code == 0 else FAILED), code
        if code == 0:
            item.fraction = 1.0

    def block(self, item):
        item.state = BLOCKED

    def discard(self, app_id, kind):
        """Quita un elemento que aún no ha empezado (en cola o bloqueado); False si ya no se puede."""
        for i in self.items:
            if i.app_id == app_id and i.kind == kind and i.state in (QUEUED, BLOCKED):
                self.items.remove(i)
                return True
        return False

    def clear_finished(self):
        self.items = [i for i in self.items if i.state in (*ACTIVE, BLOCKED)]

    def has_work(self):
        return any(i.state in ACTIVE for i in self.items)

    def counts(self):
        """(posición del elemento en curso, total de la tanda) para «Instalando 2 de 5»."""
        batch = [i for i in self.items if i.state in (*ACTIVE, DONE, FAILED)]
        done = sum(1 for i in batch if i.state in (DONE, FAILED))
        return min(done + 1, len(batch)), len(batch)

    def latest(self, app_id):
        return next((i for i in reversed(self.items) if i.app_id == app_id), None)

    def summaries(self):
        return [i.summary() for i in self.items]
