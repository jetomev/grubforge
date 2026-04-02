"""
GrubForge — Backup & Restore Screen
List all backups, preview content, restore or delete them.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual import work

from grubforge.backup_manager import (
    Backup,
    list_backups,
    create_backup,
    restore_backup,
    delete_backup,
    read_backup_content,
    BACKUP_DIR,
    GRUB_CONFIG_PATH,
)
from grubforge.widgets.confirm_dialog import ConfirmDialog

class BackupScreen(Container):
    """Backup and restore manager."""

    BINDINGS = [
        Binding("b",  "create_backup",  "New Backup", show=True),
        Binding("r",  "restore_backup", "Restore",    show=True),
        Binding("d",  "delete_backup",  "Delete",     show=True),
        Binding("f5", "refresh",        "Refresh",    show=True),
    ]

    _backups: list = []
    _selected_idx: int = -1

    def compose(self) -> ComposeResult:
        with Container(id="backup-split"):
            with Vertical(id="backup-list-panel"):
                yield Static(
                    " 🗂  Backups  [dim](B new  •  R restore  •  D delete)[/dim]",
                    classes="panel-title",
                )
                yield ListView(id="backup-list")

            with Vertical(id="backup-detail-panel"):
                yield Static("", id="backup-detail-header")
                with Horizontal(id="backup-action-buttons"):
                    yield Button("↩ Restore",    id="btn-restore", classes="-success")
                    yield Button("✗ Delete",      id="btn-delete",  classes="-danger")
                    yield Button("＋ New Backup", id="btn-new",     classes="-primary")
                yield Static(" 📄 Preview", classes="panel-title", id="preview-title")
                yield Static("", id="backup-preview")

        yield Static("", id="backup-status")

    def on_mount(self) -> None:
        self._load_backups()
        self._set_status(
            f"Backups stored in {BACKUP_DIR}  •  max 20 kept", "info"
        )

    # ── List management ───────────────────────────────────────────────────────

    def _load_backups(self) -> None:
        self._backups = list_backups()
        lv = self.query_one("#backup-list", ListView)
        lv.clear()

        if not self._backups:
            lv.append(ListItem(Static("[dim]No backups found.[/dim]")))
            self._selected_idx = -1
            self._clear_detail()
            return

        for backup in self._backups:
            ts    = backup.timestamp.strftime("%Y-%m-%d  %H:%M:%S")
            label = f"  [{backup.label}]" if backup.label else ""
            text  = (
                f"[#89b4fa]{ts}[/#89b4fa]"
                f"[dim]{label}[/dim]"
                f"  [dim]{backup.size_display}[/dim]"
            )
            lv.append(ListItem(Static(text)))

        if self._backups:
            self._selected_idx = 0
            self._show_detail(0)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._backups):
            self._selected_idx = idx
            self._show_detail(idx)

    # ── Detail pane ───────────────────────────────────────────────────────────

    def _show_detail(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._backups):
            self._clear_detail()
            return

        backup = self._backups[idx]
        header = (
            f"[bold #89b4fa]Backup #{idx + 1}[/bold #89b4fa]\n"
            f"[dim]Date:[/dim]  [#cdd6f4]{backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/#cdd6f4]\n"
            f"[dim]Size:[/dim]  [#cdd6f4]{backup.size_display}[/#cdd6f4]\n"
            f"[dim]File:[/dim]  [#a6adc8]{backup.path.name}[/#a6adc8]\n"
            + (f"[dim]Note:[/dim]  [#89b4fa]{backup.label}[/#89b4fa]\n" if backup.label else "")
        )
        self.query_one("#backup-detail-header", Static).update(header)

        try:
            content = read_backup_content(backup)
            lines   = []
            for line in content.splitlines():
                s = line.strip()
                if s.startswith("#"):
                    lines.append(f"[dim]{line}[/dim]")
                elif "=" in line and not s.startswith("#"):
                    k, _, v = line.partition("=")
                    lines.append(f"[#89b4fa]{k}[/#89b4fa]=[#a6e3a1]{v}[/#a6e3a1]")
                else:
                    lines.append(line)
            self.query_one("#backup-preview", Static).update("\n".join(lines))
        except Exception as e:
            self.query_one("#backup-preview", Static).update(
                f"[red]Could not read backup: {e}[/red]"
            )

    def _clear_detail(self) -> None:
        self.query_one("#backup-detail-header", Static).update(
            "[dim]Select a backup to preview it.[/dim]"
        )
        self.query_one("#backup-preview", Static).update("")

    # ── Button handler ────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-new":
            self.run_worker(self.action_create_backup(), exclusive=True)
        elif event.button.id == "btn-restore":
            self.run_worker(self.action_restore_backup(), exclusive=True)
        elif event.button.id == "btn-delete":
            self.run_worker(self.action_delete_backup(), exclusive=True)

    # ── Actions ───────────────────────────────────────────────────────────────

    @work
    async def action_create_backup(self) -> None:
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Create Backup",
                message=(
                    "Create a new backup of\n"
                    "/etc/default/grub right now?\n\n"
                    "(This is always safe to do.)"
                ),
                confirm_label="Create",
                confirm_variant="success",
            )
        )
        if not confirmed:
            return
        try:
            backup = create_backup(label="manual")
            self._set_status(f"Backup created: {backup.path.name}", "ok")
            self._load_backups()
        except Exception as e:
            self._set_status(f"Backup failed: {e}", "error")

    @work        
    async def action_restore_backup(self) -> None:
        idx = self._selected_idx
        if idx < 0 or idx >= len(self._backups):
            self._set_status("No backup selected.", "warn")
            return

        backup    = self._backups[idx]
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Restore Backup",
                message=(
                    f"Restore backup:\n"
                    f"  {backup.display_name}\n\n"
                    f"This will overwrite /etc/default/grub.\n"
                    f"Your current config will be auto-backed-up first."
                ),
                confirm_label="Restore",
                confirm_variant="warning",
            )
        )
        if not confirmed:
            return
        try:
            restore_backup(backup)
            self._set_status(
                f"Restored: {backup.path.name} → /etc/default/grub", "ok"
            )
            self._load_backups()
        except Exception as e:
            self._set_status(f"Restore failed: {e}", "error")

    @work        
    async def action_delete_backup(self) -> None:
        idx = self._selected_idx
        if idx < 0 or idx >= len(self._backups):
            self._set_status("No backup selected.", "warn")
            return

        backup    = self._backups[idx]
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Delete Backup",
                message=(
                    f"Permanently delete:\n"
                    f"  {backup.path.name}\n\n"
                    f"This cannot be undone."
                ),
                confirm_label="Delete",
                confirm_variant="danger",
            )
        )
        if not confirmed:
            return
        try:
            delete_backup(backup)
            self._set_status(f"Deleted: {backup.path.name}", "ok")
            self._load_backups()
        except Exception as e:
            self._set_status(f"Delete failed: {e}", "error")

    def action_refresh(self) -> None:
        self._load_backups()
        self._set_status("Backup list refreshed.", "info")

    # ── Status bar ────────────────────────────────────────────────────────────

    def _set_status(self, msg: str, level: str = "info") -> None:
        color_map = {
            "ok":    "#a6e3a1",
            "info":  "#89b4fa",
            "warn":  "#f9e2af",
            "error": "#f38ba8",
        }
        icon_map = {"ok": "✓", "info": "●", "warn": "⚠", "error": "✗"}
        color = color_map.get(level, "#cdd6f4")
        icon  = icon_map.get(level, "●")
        self.query_one("#backup-status", Static).update(
            f"[{color}]{icon} {msg}[/{color}]"
        )