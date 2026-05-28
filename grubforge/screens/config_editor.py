"""
grubForge — Config Editor Screen
Browse, view, and edit all /etc/default/grub settings.
Left panel: key table. Right panel: detail + inline editor.
Bottom: raw file preview.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.widgets import DataTable, Static, Input, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual import work

from grubforge.config_manager import (
    GRUB_CONFIG_PATH,
    MANAGED_KEYS,
    KEY_DESCRIPTIONS,
    parse_grub_config,
    write_grub_config,
    validate_changes,
    GrubConfig,
    GrubEntry,
)
from grubforge.backup_manager import create_backup
from grubforge.widgets.confirm_dialog import ConfirmDialog
from grubforge.widgets.status import StatusMixin

class ConfigEditorScreen(StatusMixin, Container):
    """Full config editor: table + detail pane + raw view."""

    STATUS_WIDGET_ID = "editor-status"

    BINDINGS = [
        # Edit / Save / Refresh / Ctrl+R live as universal app-level bindings;
        # this screen exposes the action methods that the global dispatcher calls.
    ]

    _selected_key: Optional[str] = None
    _pending: dict = {}
    _config: Optional[GrubConfig] = None

    def compose(self) -> ComposeResult:
        with Container(id="config-split"):
            with Vertical(id="config-keys-panel"):
                yield Static(
                    " 🔧  GRUB Keys  [dim](↑↓ navigate  •  E edit)[/dim]",
                    id="config-keys-title",
                    classes="panel-title",
                )
                yield DataTable(id="config-table", cursor_type="row")

            with Vertical(id="config-detail-panel"):
                yield Static("", id="detail-key",         classes="detail-key")
                yield Static("", id="detail-description", classes="detail-description")
                yield Static("", id="detail-current",     classes="detail-current")
                yield Static("", id="detail-pending",     classes="detail-pending")
                yield Input(placeholder="New value…", id="edit-input")
                yield Static("", id="edit-validation")
                with Horizontal(id="editor-buttons"):
                    yield Button("Apply Edit",    id="btn-apply-edit",  classes="-primary")
                    yield Button("Clear Pending", id="btn-clear-edit",  classes="-warning")
                yield Static(
                    "\n[dim]Pending edits are saved together when you press [bold]S[/bold][/dim]",
                    id="editor-hint",
                )

        with Vertical(id="raw-config-panel"):
            yield Static(
                " 📄  Raw /etc/default/grub  [dim](read-only preview)[/dim]",
                id="raw-config-title",
                classes="panel-title",
            )
            yield Static("", id="raw-view")

        yield Static("", id="editor-status")

    def on_mount(self) -> None:
        self._load_config()
        self._build_table()
        self._update_raw_view()
        # Passive mount-time hint — status line only, no startup popup.
        self._set_status("Config loaded. Select a key to view details.", "info", popup=False)

    # ── Config loading ────────────────────────────────────────────────────────

    def _load_config(self) -> None:
        self._config = parse_grub_config(GRUB_CONFIG_PATH)

    def _build_table(self) -> None:
        table = self.query_one("#config-table", DataTable)
        table.clear(columns=True)
        table.add_columns("Key", "Value", "Status")

        for key in MANAGED_KEYS:
            entry   = self._config.entries.get(key) if self._config else None
            pending = self._pending.get(key)

            if pending is not None:
                value_display = f"[yellow]{pending}[/yellow]"
                status        = "[yellow]● pending[/yellow]"
            elif entry and not entry.commented:
                value_display = entry.value or "[dim](empty)[/dim]"
                status        = "[green]● set[/green]"
            elif entry and entry.commented:
                value_display = f"[dim]{entry.value}[/dim]"
                status        = "[dim]○ commented[/dim]"
            else:
                value_display = "[dim](not set)[/dim]"
                status        = "[dim]○ absent[/dim]"

            table.add_row(key, value_display, status, key=key)

    def _update_raw_view(self) -> None:
        if not self._config:
            return
        lines = []
        for line in self._config.raw_lines:
            stripped = line.rstrip()
            if stripped.startswith("#"):
                lines.append(f"[dim]{stripped}[/dim]")
            elif "=" in stripped:
                k, _, v = stripped.partition("=")
                lines.append(f"[#89b4fa]{k}[/#89b4fa]=[#a6e3a1]{v}[/#a6e3a1]")
            else:
                lines.append(stripped)
        self.query_one("#raw-view", Static).update("\n".join(lines))

    # ── Row selection ─────────────────────────────────────────────────────────

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value if event.row_key else None
        if not key:
            return
        self._selected_key = key
        self._show_detail(key)

    def _show_detail(self, key: str) -> None:
        entry   = self._config.entries.get(key) if self._config else None
        pending = self._pending.get(key)

        description = KEY_DESCRIPTIONS.get(key, "No description available.")
        current_val = (
            entry.value if entry and not entry.commented
            else f"(commented: {entry.value})" if entry
            else "(not set)"
        )

        self.query_one("#detail-key",         Static).update(f"[bold #89b4fa]{key}[/bold #89b4fa]")
        self.query_one("#detail-description", Static).update(f"[#a6adc8]{description}[/#a6adc8]")
        self.query_one("#detail-current",     Static).update(f"Current: [bold #a6e3a1]{current_val}[/bold #a6e3a1]")

        if pending is not None:
            self.query_one("#detail-pending", Static).update(f"Pending: [bold #f9e2af]{pending}[/bold #f9e2af]")
        else:
            self.query_one("#detail-pending", Static).update("")

        inp       = self.query_one("#edit-input", Input)
        inp.value = pending if pending is not None else (
            entry.value if entry and not entry.commented else ""
        )
        self.query_one("#edit-validation", Static).update("")

    # ── Edit actions ──────────────────────────────────────────────────────────

    def action_start_edit(self) -> None:
        self.query_one("#edit-input", Input).focus()

    def action_apply_edit(self) -> None:
        # Mirror the "Apply Edit" button so the global `A` binding stages the
        # edit here too (F13: keyboard A previously rejected while the button
        # worked — the dispatcher only looked for action_apply_theme).
        self._stage_edit()

    def on_input_changed(self, event: Input.Changed) -> None:
        if not self._selected_key:
            return
        result = validate_changes({self._selected_key: event.value})
        widget = self.query_one("#edit-validation", Static)
        if result.errors:
            widget.update(f"[red]✗ {result.errors[0]}[/red]")
        elif result.warnings:
            widget.update(f"[yellow]⚠ {result.warnings[0]}[/yellow]")
        else:
            widget.update("[green]✓ Valid[/green]" if event.value else "")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply-edit":
            self._stage_edit()
        elif event.button.id == "btn-clear-edit":
            self._clear_pending()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._stage_edit()

    def _stage_edit(self) -> None:
        if not self._selected_key:
            self._set_status("No key selected.", "warn")
            return

        val = self.query_one("#edit-input", Input).value.strip()

        result = validate_changes({self._selected_key: val})
        if not result.valid:
            self._set_status(f"Validation failed: {result.errors[0]}", "error")
            return

        self._pending[self._selected_key] = val
        self._build_table()
        self._show_detail(self._selected_key)
        display_val = val if val else "(cleared)"
        msg = f"Staged: {self._selected_key}={display_val}"
        if result.warnings:
            msg += f" — ⚠ {result.warnings[0]}"
        self._set_status(msg, "warn" if result.warnings else "info")

    def _clear_pending(self) -> None:
        self._pending.clear()
        self._build_table()
        if self._selected_key:
            self._show_detail(self._selected_key)
        self._set_status("All pending edits cleared.", "info")

    # ── Save ──────────────────────────────────────────────────────────────────
    
    @work
    async def action_save_changes(self) -> None:
        if not self._pending:
            self._set_status("No pending changes to save.", "info")
            return
        if self.app.read_only_mode:
            self._set_status("Read-only mode — relaunch with sudo to save config changes.", "warn")
            return

        changes_summary = "\n".join(
            f"  {k} = {v}" for k, v in self._pending.items()
        )
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Apply GRUB Config Changes",
                message=(
                    f"These changes will be written to\n"
                    f"/etc/default/grub:\n\n"
                    f"{changes_summary}\n\n"
                    f"A backup will be created first."
                ),
                confirm_label="Apply",
                confirm_variant="primary",
            )
        )
        if not confirmed:
            self._set_status("Changes cancelled.", "info")
            return

        await self._write_changes()

    async def _write_changes(self) -> None:
        try:
            try:
                create_backup(label="pre-edit")
                self._set_status("Backup created…", "info")
            except Exception as e:
                self._set_status(f"Backup failed: {e} — aborting.", "error")
                return

            if not self._config:
                return

            new_lines = write_grub_config(self._config, self._pending)

            if GRUB_CONFIG_PATH.exists():
                GRUB_CONFIG_PATH.write_text("".join(new_lines), encoding="utf-8")
            else:
                self.app.notify(
                    "Demo mode: config not written (no /etc/default/grub).",
                    severity="warning",
                )

            self._pending.clear()
            self._load_config()
            self._build_table()
            self._update_raw_view()
            if self._selected_key:
                self._show_detail(self._selected_key)

            self._set_status(
                "Changes applied. Press Ctrl+R to regenerate grub.cfg.",
                "ok",
            )

        except PermissionError:
            self._set_status(
                "Permission denied — run grubForge with sudo.", "error"
            )
        except Exception as e:
            self._set_status(f"Error: {e}", "error")

    # grub.cfg regeneration (Ctrl+R) is handled app-level for every screen —
    # see GrubForgeApp.action_global_regen (v1.0.3 F7). It used to live here as
    # a screen-local action_regen_grub that only this screen implemented.

    # ── Refresh ───────────────────────────────────────────────────────────────

    # Silent re-read used by the app when this screen is shown (F8). Pending
    # staged edits are preserved — only the on-disk config is re-read.
    def _reload_view(self) -> None:
        self._load_config()
        self._build_table()
        self._update_raw_view()
        if self._selected_key:
            self._show_detail(self._selected_key)

    def action_refresh(self) -> None:
        self._reload_view()
        self._set_status("Config reloaded from disk.", "info")

    # _set_status is provided by StatusMixin (v1.0.3 F9 — unified feedback:
    # persistent status line + app-level notify popup).