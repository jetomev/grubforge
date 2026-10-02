"""One run of grubForge: what is on disk, what you changed, what happened (v2.0.0).

Screens read and change the session; they never write files themselves.

* ``original`` — the values in /etc/default/grub when it was last read
  (``None`` = not set).
* ``pending`` — your changes that are not saved yet (key → new value or None).
* ``save(rebuild)`` — backup, write, and optionally rebuild, through the
  privileged helper; ``rebuild()`` alone runs grub-mkconfig.
* ``events`` — what happened this run, for the closing note in the terminal.

Javier's rulings (2 Oct 2026): Save and Rebuild are separate; what is saved stays
saved; "saved but not rebuilt" is always visible and is said again on quit.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable
from dataclasses import dataclass, field

from . import config_manager, grubenv, privilege
from .backup_manager import list_backups
from .settings_spec import BY_KEY, SETTINGS, display

Step = Callable[[int, str, str], None]     # (index, state, detail)
Line = Callable[[str], None]


@dataclass
class Event:
    when: dt.datetime
    what: str            # "saved" | "rebuilt" | "rebuild-failed" | "save-failed" | "restored"
    detail: str = ""


@dataclass
class Session:
    env: grubenv.GrubEnv
    capability: privilege.Capability
    config: config_manager.GrubConfig
    original: dict = field(default_factory=dict)
    pending: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    started: dt.datetime = field(default_factory=dt.datetime.now)

    # ── loading ──────────────────────────────────────────────────────────────
    @classmethod
    def load(cls) -> "Session":
        env = grubenv.detect()
        s = cls(env=env, capability=privilege.detect(), config=config_manager.parse_grub_config(grubenv.GRUB_DEFAULT_FILE))
        s._read_originals()
        return s

    def reload(self) -> None:
        """Re-read the file; your unsaved changes stay (they are yours)."""
        self.config = config_manager.parse_grub_config(grubenv.GRUB_DEFAULT_FILE)
        self._read_originals()
        self.pending = {k: v for k, v in self.pending.items() if v != self.original.get(k)}

    def _read_originals(self) -> None:
        self.original = {}
        for s in SETTINGS:
            e = self.config.entries.get(s.key)
            self.original[s.key] = None if (e is None or e.commented) else e.value

    # ── reading ──────────────────────────────────────────────────────────────
    def value(self, key: str):
        return self.pending[key] if key in self.pending else self.original.get(key)

    @property
    def read_only(self) -> bool:
        return not self.capability.can_write or not self.env.uses_grub or self.config.is_mock

    @property
    def read_only_reason(self) -> str:
        if not self.env.uses_grub:
            return self.env.note
        if self.config.is_mock:
            return "There is no /etc/default/grub on this computer, so grubForge is showing an example."
        return self.capability.reason

    @property
    def not_rebuilt(self) -> bool:
        return grubenv.saved_but_not_rebuilt(self.env)

    def last_saved(self) -> dt.datetime | None:
        saves = [e.when for e in self.events if e.what == "saved"]
        if saves:
            return saves[-1]
        try:
            return dt.datetime.fromtimestamp(grubenv.GRUB_DEFAULT_FILE.stat().st_mtime)
        except OSError:
            return None

    # ── changing ─────────────────────────────────────────────────────────────
    def set(self, key: str, value) -> bool:
        """Stage a change. Returns True when it differs from the file."""
        if value == self.original.get(key):
            self.pending.pop(key, None)
            return False
        self.pending[key] = value
        return True

    def discard(self) -> None:
        self.pending.clear()

    def changes(self, choices_for: Callable[[str], list] | None = None) -> list[tuple[str, str, str]]:
        """(label, old, new) for the review, in the order settings are shown."""
        out = []
        for s in SETTINGS:
            if s.key in self.pending:
                ch = choices_for(s.key) if choices_for else None
                out.append((s.label, display(s, self.original.get(s.key), ch),
                            display(s, self.pending[s.key], ch)))
        return out

    def problems(self) -> list[str]:
        """Why the pending changes can't be saved, in plain words."""
        result = config_manager.validate_changes(self.pending)
        out = []
        for e in result.errors:
            key = e.split()[0]
            label = BY_KEY[key].label if key in BY_KEY else key
            out.append(e.replace(key, f'"{label}"', 1))
        return out

    # ── saving and rebuilding (through the privileged helper) ────────────────
    async def save(self, rebuild: bool, step: Step, line: Line) -> bool:
        """Backup, write, [rebuild]. Steps: 0 backup, 1 write, 2 rebuild."""
        step(0, "working", "")
        r = await privilege.run_async("backup-create", "pre-edit", capability=self.capability)
        if not r.ok:
            step(0, "failed", r.message)
            self.events.append(Event(dt.datetime.now(), "save-failed", r.message))
            return False
        step(0, "done", (r.output.strip().splitlines() or [""])[-1])
        step(1, "working", "")
        content = "".join(config_manager.write_grub_config(self.config, self.pending))
        r = await privilege.run_async("write-config", content=content, capability=self.capability)
        if not r.ok:
            step(1, "failed", r.message)
            self.events.append(Event(dt.datetime.now(), "save-failed", r.message))
            return False
        n = len(self.pending)
        step(1, "done", f"{n} change{'s' if n != 1 else ''}")
        self.events.append(Event(dt.datetime.now(), "saved", f"{n} change{'s' if n != 1 else ''}"))
        self.pending.clear()
        self.reload()
        if rebuild:
            return await self.rebuild(step, line, index=2)
        return True

    async def rebuild(self, step: Step, line: Line, index: int = 0) -> bool:
        step(index, "working", self.env.mkconfig)
        r = await privilege.run_async("regenerate", capability=self.capability)
        for l in (r.output or "").splitlines():
            if l.strip():
                line(l.strip())
        if not r.ok:
            step(index, "failed", "")
            self.events.append(Event(dt.datetime.now(), "rebuild-failed", r.message))
            return False
        step(index, "done", "")
        self.events.append(Event(dt.datetime.now(), "rebuilt"))
        return True

    # ── the run, summed up for the closing note ──────────────────────────────
    def summary(self) -> tuple[str, list[str], str]:
        """(heading, lines, level) for the closing note."""
        saves = [e for e in self.events if e.what == "saved"]
        lines = [f"Saved {e.detail} at {e.when:%I:%M %p}." for e in saves]
        if any(e.what == "rebuilt" for e in self.events):
            last = [e for e in self.events if e.what == "rebuilt"][-1]
            lines.append(f"Boot menu rebuilt at {last.when:%I:%M %p}.")
        backups = list_backups()
        if saves and backups:
            lines.append(f"Newest backup: {backups[0].path.name}.")
        if self.pending:
            lines.append(f"{len(self.pending)} change(s) were left unsaved.")
        if self.not_rebuilt:
            lines.append(f"Saved changes are not in the boot menu yet: run grubForge and press F9 "
                         f"(or: sudo {self.env.mkconfig} -o {self.env.grub_cfg}).")
            return "Closed · saved, not rebuilt", lines, "warn"
        if self.pending:
            return "Closed · changes left unsaved", lines, "warn"
        if not lines:
            return "Closed · nothing was changed", ["Everything is as it was."], "ok"
        return "Closed · everything saved is in the boot menu", lines, "ok"
