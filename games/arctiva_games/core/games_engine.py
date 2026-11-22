# SPDX-License-Identifier: GPL-3.0-or-later
"""Arctiva Games: motor de instalación por pasos (D-G4, D-G5, D-G7).

Cada paso pasa por `pending → running → done | failed | skipped`. Un fallo detiene el motor en ese paso
hasta que se llame a `retry()`, `skip()` o `stop()`; nada sigue solo. Un paso con `wait_user` (D-G5) lanza
el proceso sin esperarlo ni matarlo y queda en espera hasta `continue_()`. El estado se guarda en
`<base>/<slug>.state.json` y el registro en `<base>/logs/<slug>-<AAAAMMDD-HHMMSS>.log`.

Cómo se convierte un paso en una orden lo decide `command_for(step, engine)`: devuelve un `Command` o
`None` para los pasos que el motor hace él mismo en Python (`write_file`, `write_json`, `chmodx`). Las
pruebas lo sustituyen por órdenes falsas. La orden por defecto usa el `wine` del sistema; la elección de
Proton/umu (D-G8) y la descarga de `files` quedan para la interfaz, que pasa `files` ya resueltos."""
import hashlib
import json
import os
import re
import shlex
import subprocess
import time
from collections import namedtuple
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

PENDING, RUNNING, DONE, FAILED, SKIPPED = "pending", "running", "done", "failed", "skipped"
NATIVE = ("write_file", "write_json", "chmodx")

Command = namedtuple("Command", "program args env cwd")
Command.__new__.__defaults__ = ({}, None)

_OVERRIDE = {"native": "n", "builtin": "b", "native,builtin": "n,b", "builtin,native": "b,n",
             "disabled": "", "": ""}


class StepError(Exception):
    """Fallo de un paso que el motor hace él mismo; el mensaje va al registro."""


def dll_overrides(overrides):
    return ";".join(f"{dll}={_OVERRIDE.get(str(v).strip().lower(), v)}" for dll, v in overrides.items())


def accepted_codes(step):
    """Códigos de salida válidos de un paso: `return_code` (lista separada por comas) o solo 0.
    Los scripts antiguos de Lutris multiplicaban el código por 256 (768 = 3): se aceptan ambos."""
    raw = step.args.get("return_code")
    if raw is None:
        return {0}
    codes = set()
    for part in str(raw).split(","):
        try:
            c = int(part)
        except ValueError:
            continue
        codes.add(c)
        if c > 255 and c % 256 == 0:
            codes.add(c // 256)
    return codes or {0}


def default_command(step, engine):
    """Orden de Wine para un paso, con el ejecutor del motor (`wine` del sistema o Proton con umu)."""
    a = step.args
    res = engine.resolve
    runner = engine.runner
    proton = bool(runner and runner.get("path"))
    # Con Proton todo pasa por umu-run, que usa WINEPREFIX y PROTONPATH del entorno.
    wine = (lambda *args, cwd=None: Command(runner["umu"], list(args), {"PROTONPATH": runner["path"],
                                                                       "GAMEID": "umu-0"}, cwd)) if proton \
        else (lambda *args, cwd=None: Command("wine", list(args), cwd=cwd))
    if step.kind == "create_prefix":
        return wine("wineboot", "-u") if proton else Command("wineboot", ["--init"])
    if step.kind == "wineexec":
        return wine(res(a["executable"]), *shlex.split(res(_s(a.get("args")))), cwd=a.get("working_dir"))
    if step.kind == "winetricks":
        return wine("winetricks", "-q", *_s(a.get("app")).split()) if proton else \
            Command("winetricks", ["-q", *_s(a.get("app")).split()])
    if step.kind == "winekill":
        return stop_command_for(runner)
    if step.kind == "set_regedit":
        return wine("reg", "add", _s(a.get("path")), "/v", _s(a.get("key")), "/t",
                    _s(a.get("type") or "REG_SZ"), "/d", _s(a.get("value")), "/f")
    if step.kind == "delete_registry_key":
        return wine("reg", "delete", _s(a.get("key")), "/f")
    if step.kind == "execute":
        if a.get("file"):
            return Command(res(a["file"]), shlex.split(res(_s(a.get("args")))))
        return Command("sh", ["-c", res(_s(a.get("command")))])
    raise StepError(f"la orden «{step.kind}» aún no está implementada")


def stop_command_for(runner):
    """`wineserver -k` del ejecutor: con Proton, el de su carpeta; si no, el del sistema."""
    if runner and runner.get("path"):
        return Command(str(Path(runner["path"]) / "files" / "bin" / "wineserver"), ["-k"])
    return Command("wineserver", ["-k"])


def _s(v):
    return "" if v is None else str(v)


class GameEngine(QObject):
    stepChanged = Signal(int, str)
    logLine = Signal(str)
    waitingForUser = Signal(int, str)
    finished = Signal(bool)

    def __init__(self, plan, base_dir, command_for=None, detailed=False, files=None, stop_command=None,
                 runner=None, parent=None):
        super().__init__(parent)
        self.plan = plan
        self.base = Path(base_dir)
        self.command_for = command_for or default_command
        self.detailed = detailed
        self.files = dict(files or {})
        # `{"path": carpeta de Proton, "umu": ruta de umu-run}` o None para el wine del sistema.
        self.runner = runner
        # Parar deja el prefijo como está pero cierra sus procesos (D-G4).
        self.stop_command = stop_command if stop_command is not None else stop_command_for(runner)
        self.states = [PENDING] * len(plan.steps)
        self._i = -1
        self._proc = None          # proceso del paso en curso
        self._background = []      # procesos de pasos con espera del usuario
        self._waiting = False
        self._bufs = {}            # resto de línea por proceso: un lanzador sigue escribiendo tras Continuar
        self._log = None
        self.log_path = None
        self.state_path = self.base / f"{plan.slug or 'juego'}.state.json"

    # --- API ---
    def resolve(self, value):
        """Sustituye el id de un archivo (`setup` o `$setup`) por su ruta."""
        value = _s(value)
        if value in self.files:
            return str(self.files[value])
        return re.sub(r"\$\{?(\w+)\}?", lambda m: str(self.files.get(m.group(1), m.group(0))), value)

    def fingerprint(self):
        """Huella de los pasos: un estado guardado solo se reanuda con el mismo plan."""
        raw = json.dumps([[s.kind, s.args] for s in self.plan.steps] + [self.plan.prefix], sort_keys=True,
                         default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def has_saved_state(self):
        return self._load_state() is not None

    def start(self):
        if self._log is not None:
            return
        saved = self._load_state()
        if saved:
            # Lo que quedó en curso o fallido se repite; lo hecho y lo saltado se respeta.
            self.states = [s if s in (DONE, SKIPPED) else PENDING for s in saved]
        self._open_log()
        for i, s in enumerate(self.states):
            self.stepChanged.emit(i, s)
        self._advance()

    def retry(self):
        if self._i >= 0 and self.states[self._i] == FAILED:
            self._run_step()

    def skip(self):
        if self._i >= 0 and self.states[self._i] == FAILED:
            self._set(self._i, SKIPPED)
            self._advance()

    def continue_(self):
        if self._waiting:
            self._waiting = False
            self._set(self._i, DONE)
            self._advance()

    def stop(self):
        if self._log is None:
            return
        self._waiting = False
        procs = ([self._proc] if self._proc else []) + self._background
        self._proc, self._background = None, []
        for p in procs:
            p.blockSignals(True)
            if p.state() != QProcess.ProcessState.NotRunning:
                p.kill()
                p.waitForFinished(2000)
        self._write("=== Instalación detenida; se cierran los procesos del prefijo ===")
        if self.stop_command:
            try:
                subprocess.run([self.stop_command.program, *self.stop_command.args], timeout=30,
                               env={**os.environ, **self._env(None)}, capture_output=True)
            except (OSError, subprocess.SubprocessError) as e:
                self._write(f"No se pudo cerrar el prefijo: {e}")
        if 0 <= self._i < len(self.states) and self.states[self._i] == RUNNING:
            self.states[self._i] = PENDING
            self.stepChanged.emit(self._i, PENDING)
        self._save_state()
        self._close_log()
        self.finished.emit(False)

    # --- motor ---
    def _advance(self):
        nxt = next((i for i, s in enumerate(self.states) if s == PENDING), None)
        if nxt is None:
            self._write("=== Instalación terminada ===")
            self._clear_state()
            self._close_log()
            self.finished.emit(True)
            return
        self._i = nxt
        self._run_step()

    def _set(self, i, state):
        self.states[i] = state
        self._save_state()
        self.stepChanged.emit(i, state)

    def _fail(self, message):
        self._write(message)
        self._proc = None
        self._set(self._i, FAILED)

    def _run_step(self):
        i, step = self._i, self.plan.steps[self._i]
        self._set(i, RUNNING)
        self._write(f"=== [{i + 1}/{len(self.states)}] {step.description} ===")
        try:
            if step.kind in NATIVE:
                _native(step, self.plan.game_dir)
                self._write("hecho")
                self._set(i, DONE)
                self._advance()
                return
            cmd = self.command_for(step, self)
        except (StepError, OSError, ValueError) as e:
            self._fail(f"Error: {e}")
            return
        proc = QProcess(self)
        proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        qenv = proc.processEnvironment()
        qenv.clear()
        for k, v in {**os.environ, **cmd.env, **self._env(step)}.items():
            qenv.insert(k, v)
        proc.setProcessEnvironment(qenv)
        Path(self.plan.game_dir).mkdir(parents=True, exist_ok=True)
        proc.setWorkingDirectory(cmd.cwd or self.plan.game_dir)
        proc.readyReadStandardOutput.connect(lambda: self._read(proc))
        proc.errorOccurred.connect(lambda e: self._on_error(proc, e))
        proc.finished.connect(lambda code, st: self._on_finished(proc, step, code, st))
        self._write("$ " + shlex.join([cmd.program, *cmd.args]))
        if step.wait_user:
            # D-G5: no se espera ni se mata; el paso termina al pulsar Continuar.
            self._background.append(proc)
            self._waiting = True
        else:
            self._proc = proc
        proc.start(cmd.program, list(cmd.args))
        if step.wait_user and self._waiting:
            self._write(step.wait_message)
            self.waitingForUser.emit(i, step.wait_message)

    def _env(self, step):
        env = {"WINEPREFIX": self.plan.prefix, **self.plan.env}
        if self.plan.overrides:
            env["WINEDLLOVERRIDES"] = dll_overrides(self.plan.overrides)
        if step is not None:
            env.update(step.env)
        if not self.detailed:
            env["WINEDEBUG"] = "-all"
        return env

    def _on_error(self, proc, error):
        if error != QProcess.ProcessError.FailedToStart:
            return
        if proc in self._background:
            self._background.remove(proc)
            self._waiting = False
            self._fail(f"No se pudo lanzar la orden: {proc.program()}")
        elif proc is self._proc:
            self._fail(f"No se pudo lanzar la orden: {proc.program()}")

    def _on_finished(self, proc, step, code, status):
        self._read(proc)
        rest = self._bufs.pop(proc, "")
        if rest:
            self._write(rest)
        proc.deleteLater()
        crashed = status != QProcess.ExitStatus.NormalExit
        if proc in self._background:
            self._write(f"El proceso «{proc.program()}» terminó con código {'?' if crashed else code}.")
            self._background.remove(proc)
            return
        if proc is not self._proc:
            return
        if not crashed and code in accepted_codes(step):
            self._write(f"hecho (código {code})")
            self._proc = None
            self._set(self._i, DONE)
            self._advance()
        else:
            self._fail("El proceso se cerró de forma anormal." if crashed else
                       f"Falló con código de salida {code}.")

    def _read(self, proc):
        buf = self._bufs.get(proc, "") + bytes(proc.readAllStandardOutput()).decode("utf-8", "replace")
        *lines, self._bufs[proc] = buf.split("\n")
        for line in lines:
            self._write(line.rstrip("\r"))

    # --- registro y estado ---
    def _write(self, text):
        if self._log:
            self._log.write(text + "\n")
        self.logLine.emit(text)

    def _open_log(self):
        logs = self.base / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        self.log_path = logs / f"{self.plan.slug or 'juego'}-{time.strftime('%Y%m%d-%H%M%S')}.log"
        self._log = open(self.log_path, "a", buffering=1, encoding="utf-8")

    def _close_log(self):
        if self._log:
            self._log.close()
            self._log = None

    def _load_state(self):
        try:
            data = json.loads(self.state_path.read_text())
            states = [s["state"] for s in data["steps"]]
            fingerprint = data["plan"]
        except (OSError, ValueError, KeyError, TypeError):
            return None
        if fingerprint != self.fingerprint() or len(states) != len(self.plan.steps) or any(
                s not in (PENDING, RUNNING, DONE, FAILED, SKIPPED) for s in states):
            return None
        return states

    def _save_state(self):
        self.base.mkdir(parents=True, exist_ok=True)
        data = {"slug": self.plan.slug, "plan": self.fingerprint(), "steps": [{"id": s.id, "state": st}
                                                  for s, st in zip(self.plan.steps, self.states)]}
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data))
        os.replace(tmp, self.state_path)

    def _clear_state(self):
        try:
            self.state_path.unlink()
        except OSError:
            pass


def _inside(game_dir, path):
    root = Path(os.path.realpath(game_dir))
    real = Path(os.path.realpath(path))
    if real != root and root not in real.parents:
        raise StepError(f"la ruta {path} queda fuera de la carpeta del juego")
    return real


def _native(step, game_dir):
    a = step.args
    if step.kind == "chmodx":
        p = _inside(game_dir, a["path"])
        p.chmod(p.stat().st_mode | 0o111)
        return
    p = _inside(game_dir, a["file"])
    p.parent.mkdir(parents=True, exist_ok=True)
    if step.kind == "write_file":
        with open(p, "a" if a.get("mode") == "a" else "w", encoding="utf-8") as f:
            f.write(_s(a.get("content")))
        return
    data = a.get("data") or {}
    if a.get("merge") and p.is_file():
        try:
            old = json.loads(p.read_text())
        except ValueError:
            old = {}
        if isinstance(old, dict) and isinstance(data, dict):
            data = {**old, **data}
    p.write_text(json.dumps(data, indent=2))
