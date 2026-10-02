"""Backups — copies of your settings, and what restoring one would change (v2.0.0).

Every save makes one first. The list says why each was made in plain words;
the right side shows, setting by setting, what restoring it would change from
today's file. A restore is a save like any other: the changes bar then offers
Rebuild, so you decide when the boot menu changes.
"""

from __future__ import annotations

import datetime as dt

from rich.markup import escape
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Static

from forgekit import ConfirmDialog, ForgePanelScreen, Notice, glyph

from .. import config_manager, privilege
from ..backup_manager import BACKUP_DIR, list_backups, read_backup_content
from ..settings_spec import BY_KEY, display
from .bootmenu import rich_colours


def why_made(label: str) -> str:
    """A backup's label in plain words."""
    if not label:
        return "Saved (no note)"
    if label == "pre-edit":
        return "Before a save"
    if label.startswith("pre-theme-"):
        return f"Before using a theme ({label.removeprefix('pre-theme-')})"
    return {"manual": "Made by you", "auto (pre-restore)": "Before restoring a backup",
            "pre-os-prober-enable": "Before finding other systems"}.get(label, label)


def when(t: dt.datetime) -> tuple[str, str]:
    today = dt.date.today()
    day = "Today" if t.date() == today else ("Yesterday" if t.date() == today - dt.timedelta(days=1)
                                             else f"{t:%b %d}")
    return day, f"{t:%I:%M %p}"


def parse_values(text: str) -> dict:
    """KEY → value (None = not set) from a file's text, for every key in it."""
    import tempfile
    from pathlib import Path
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        f.write(text)
        name = f.name
    try:
        cfg = config_manager.parse_grub_config(Path(name))
    finally:
        Path(name).unlink()
    return {k: (None if e.commented else e.value) for k, e in cfg.entries.items()}


def differences(backup_text: str, current_text: str) -> list[tuple[str, str, str]]:
    """(name, now, after restoring) for every setting that would change."""
    b, c = parse_values(backup_text), parse_values(current_text)
    out = []
    for key in sorted(set(b) | set(c)):
        if b.get(key) == c.get(key):
            continue
        s = BY_KEY.get(key)
        if s:
            out.append((s.label, display(s, c.get(key)), display(s, b.get(key))))
        else:
            out.append((key, c.get(key) if c.get(key) is not None else "not set",
                        b.get(key) if b.get(key) is not None else "not set"))
    return out


class BackupsScreen(Horizontal, can_focus=False):
    BINDINGS = [Binding("n", "new", show=False), Binding("r", "restore", show=False),
                Binding("d", "delete", show=False)]

    def __init__(self, session, **kw) -> None:
        super().__init__(**kw)
        self.session = session
        self.backups = []

    def compose(self) -> ComposeResult:
        with Vertical(id="bk-left"):
            yield Static("[b $forge-title-accent]Backups[/]   [$forge-muted]newest first · last 10 kept[/]",
                         classes="gf-group-title")
            t = DataTable(id="bk-table", cursor_type="row")
            t.FORGE_HINTS = [("↑↓", "pick"), ("N", "back up"), ("R", "restore"), ("D", "delete"),
                             ("Tab", "buttons"), ("?", "all keys")]
            yield t
            yield Static("", id="bk-where")
            with Horizontal(classes="forge-buttons gf-box-buttons bk-actions", id="bk-actions"):
                yield Button(f"Restore{glyph('ellipsis')}  R", id="bk-restore", variant="primary")
                yield Button("Back up now  N", id="bk-new")
            with Horizontal(classes="forge-buttons gf-box-buttons bk-actions", id="bk-more"):
                yield Button("Show whole file", id="bk-show")
                yield Button(f"Delete{glyph('ellipsis')}  D", id="bk-delete")
        with VerticalScroll(id="bk-right", classes="gf-box", can_focus=False):
            yield Static("", id="bk-diff")
            yield Notice(id="bk-note")

    def on_mount(self) -> None:
        self.query_one("#bk-right").border_title = "Restoring this would change"
        self.refresh_view()

    def on_resize(self) -> None:
        self.call_after_refresh(self.refresh_view)

    def refresh_view(self) -> None:
        t = self.query_one("#bk-table", DataTable)
        keep = t.cursor_row
        # columns rebuilt each time: clear() alone keeps widths from longer text
        # One "When" column and no size: at 100 columns four needed a sideways scroll.
        t.clear(columns=True)
        t.add_columns("When", "Why it was made")
        self.backups = list_backups()
        rows = []
        for b in self.backups:
            day, clock = when(b.timestamp)
            order = b.path.with_name(b.path.name + ".40_custom").exists()
            rows.append((f"{day} {clock}", why_made(b.label), order))
        # a long reason ("Before using a theme (…)") is cut to the list's width, so
        # the list never needs a sideways scroll; it is refilled when the window resizes
        widest = max((len(w) for w, _r, _o in rows), default=0)
        room = t.size.width - 2 - (widest + 2) - 2 - 1 if t.size.width else 0
        for w, why, order in rows:
            tail = "  + boot order" if order else ""
            if room and len(why) + len(tail) > room:
                why = why[:max(room - len(tail) - 1, 8)].rstrip() + glyph("ellipsis")
            t.add_row(w, rich_colours(escape(why) + (f"[$forge-muted]{tail}[/]" if tail else ""), self.app))
        self.query_one("#bk-where", Static).update(
            f"[$forge-muted]{len(self.backups)} backup{'s' if len(self.backups) != 1 else ''} · {BACKUP_DIR}[/]")
        if self.backups:
            t.move_cursor(row=min(keep or 0, len(self.backups) - 1))
            self._show(self.backups[t.cursor_row])
        else:
            self.query_one("#bk-diff", Static).update("No backups yet. One is made before every save.")

    def current(self):
        t = self.query_one("#bk-table", DataTable)
        if not self.backups or t.cursor_row is None or t.cursor_row >= len(self.backups):
            return None
        return self.backups[t.cursor_row]

    def _show(self, b) -> None:
        try:
            text = read_backup_content(b)
            now = config_manager.GRUB_CONFIG_PATH.read_text(encoding="utf-8")
        except OSError as exc:
            self.query_one("#bk-diff", Static).update(f"[$forge-danger]Can't read it: {escape(str(exc))}[/]")
            return
        diff = differences(text, now)
        if not diff:
            body = f"[$forge-ok]{glyph('ok')} Nothing: it is the same as today's settings.[/]"
        else:
            lines = []
            for name, cur, after in diff:
                lines += [f"[b]{escape(name)}[/]", f"  [$forge-danger]− {escape(cur)}[/]",
                          f"  [$forge-ok]+ {escape(after)}[/]"]
            lines.append("[$forge-muted]Everything else is the same.[/]")
            body = "\n".join(lines)
        self.query_one("#bk-diff", Static).update(body)
        note = self.query_one("#bk-note", Notice)
        if b.path.with_name(b.path.name + ".40_custom").exists():
            note.show("Your boot order file was saved with it", [
                "Restoring puts back the settings. The boot order is changed on the Boot menu screen; "
                "the saved copy is kept beside the backup for recovery."], level="muted")
        else:
            note.hide()

    @on(DataTable.RowHighlighted, "#bk-table")
    def _row(self, e: DataTable.RowHighlighted) -> None:
        if 0 <= e.cursor_row < len(self.backups):
            self._show(self.backups[e.cursor_row])

    def _can_write(self) -> bool:
        s = self.session
        if s.read_only:
            self.app.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return False
        return True

    @work(group="gf-write", exclusive=True)
    async def action_new(self) -> None:
        if not self._can_write():
            return
        r = await privilege.run_async("backup-create", "manual", capability=self.session.capability)
        self.refresh_view()
        self.app.notify("Backup saved." if r.ok else r.message, severity="information" if r.ok else "error")

    @work(group="gf-write", exclusive=True)
    async def action_restore(self) -> None:
        b = self.current()
        if b is None or not self._can_write():
            return
        if self.session.pending:
            self.app.notify("Save or discard your changes first: a restore would mix with them.",
                            severity="warning", timeout=8)
            return
        day, clock = when(b.timestamp)
        msg = (f"Restore the backup from {day.lower()} {clock}?\n\nThe settings shown on the right are put back. "
               "Today's settings are backed up first, so this can be undone. The boot menu changes only when "
               "you rebuild.")
        if not await self.app.push_screen_wait(ConfirmDialog(msg, "Restore", default_no=True)):
            return
        r = await privilege.run_async("backup-restore", b.path.name, capability=self.session.capability)
        if r.ok:
            self.session.record_restore(f"{day.lower()} {clock}")
        self.app.after_files_changed()
        self.app.notify("Restored. Rebuild (F9) to put it in the boot menu." if r.ok else r.message,
                        title="Restored" if r.ok else "Not restored", severity="information" if r.ok else "error",
                        timeout=8)

    @work(group="gf-write", exclusive=True)
    async def action_delete(self) -> None:
        b = self.current()
        if b is None or not self._can_write():
            return
        day, clock = when(b.timestamp)
        if not await self.app.push_screen_wait(ConfirmDialog(
                f"Delete the backup from {day.lower()} {clock}?\n\nThis can't be undone.", "Delete",
                danger=True, default_no=True)):
            return
        r = await privilege.run_async("backup-delete", b.path.name, capability=self.session.capability)
        self.refresh_view()
        self.app.notify("Deleted." if r.ok else r.message, severity="information" if r.ok else "error")

    @on(Button.Pressed)
    def _buttons(self, e: Button.Pressed) -> None:
        bid = e.button.id or ""
        if bid == "bk-new":
            e.stop(); self.action_new()
        elif bid == "bk-restore":
            e.stop(); self.action_restore()
        elif bid == "bk-delete":
            e.stop(); self.action_delete()
        elif bid == "bk-show":
            e.stop()
            b = self.current()
            if b:
                self.app.push_screen(WholeFile(b))


class WholeFile(ForgePanelScreen):
    def __init__(self, backup) -> None:
        super().__init__()
        day, clock = when(backup.timestamp)
        self.panel_title = f"The backup from {day.lower()} {clock}"
        self._b = backup

    def compose_body(self) -> ComposeResult:
        try:
            text = read_backup_content(self._b)
        except OSError as exc:
            text = f"Can't read it: {exc}"
        yield Static(escape(text))
