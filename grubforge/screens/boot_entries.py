"""
GrubForge — Boot Entries Screen
View, reorder, rename, and group GRUB boot entries.
Writes custom order to /etc/grub.d/40_custom.
"""

from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Static, Button, Input
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding

from grubforge.boot_entries_manager import (
    BootEntry,
    parse_boot_entries,
    write_custom_order,
    disable_script,
    enable_script,
    get_script_status,
    restore_original_order,
    rename_entry,
    GRUB_CFG_PATH,
    MANAGED_SCRIPTS,
)
from grubforge.config_manager import regenerate_grub
from grubforge.widgets.confirm_dialog import ConfirmDialog


class BootEntriesScreen(Container):
    """Boot entry reorder, rename, and grouping screen."""

    BINDINGS = [
        Binding("k",      "move_up",       "Move Up",          show=True),
        Binding("j",      "move_down",      "Move Down",        show=True),
        Binding("s",      "save_order",     "Save Order",       show=True),
        Binding("n",      "start_rename",   "Rename",           show=True),
        Binding("r",      "restore_order",  "Restore Original", show=True),
        Binding("f5",     "refresh",        "Refresh",          show=True),
    ]

    _entries: list = []
    _selected_idx: int = 0

    def compose(self) -> ComposeResult:
        with Container(id="backup-split"):
            # Left: entry list
            with Vertical(id="backup-list-panel"):
                yield Static(
                    " 🖥  Boot Entries  [dim](K up  •  J down  •  N rename  •  S save)[/dim]",
                    classes="panel-title",
                )
                yield ListView(id="entries-list")

            # Right: detail + actions
            with Vertical(id="backup-detail-panel"):
                yield Static("", id="entry-detail-header")

                # ── Move / Save buttons ──
                with Horizontal(id="backup-action-buttons"):
                    yield Button("▲ Move Up",    id="btn-up",    classes="-primary")
                    yield Button("▼ Move Down",  id="btn-down",  classes="-primary")
                    yield Button("💾 Save Order", id="btn-save", classes="-success")

                # ── Restore / Refresh buttons ──
                with Horizontal(id="entry-action-buttons-2"):
                    yield Button("↺ Restore Original", id="btn-restore", classes="-warning")
                    yield Button("↺ Refresh",           id="btn-refresh", classes="-primary")

                # ── Rename section ──
                yield Static(" ✏  Rename Entry", classes="panel-title")
                yield Static(
                    "[dim]Select an entry then type a new name below.[/dim]",
                    id="rename-hint",
                )
                yield Input(placeholder="New entry name…", id="rename-input")
                with Horizontal(id="rename-buttons"):
                    yield Button("✏ Rename", id="btn-rename", classes="-success")
                    yield Button("✗ Clear",  id="btn-rename-clear", classes="-warning")

                # ── Script status ──
                yield Static(" 🔧 Script Status", classes="panel-title")
                yield Static("", id="script-status")

                # ── How it works ──
                yield Static(" ℹ  How it works", classes="panel-title")
                yield Static(
                    "\n"
                    "[dim]1. Use [bold]K/J[/bold] to reorder entries\n"
                    "2. Press [bold]N[/bold] to rename selected entry\n"
                    "3. Press [bold]S[/bold] to save your order\n"
                    "   Writes to [bold]/etc/grub.d/40_custom[/bold]\n"
                    "   and disables auto-generate scripts\n"
                    "4. grub-mkconfig runs automatically\n\n"
                    "Press [bold]R[/bold] to restore original order.[/dim]",
                    id="entry-hint",
                )

        yield Static("", id="backup-status")

    def on_mount(self) -> None:
        self._load_entries()

    # ── Load entries ──────────────────────────────────────────────────────────

    def _load_entries(self) -> None:
        self._entries = parse_boot_entries()
        self._rebuild_list()
        self._update_script_status()
        self._set_status(
            f"Loaded {len(self._entries)} boot entries from {GRUB_CFG_PATH}", "info"
        )
        if self._entries:
            self._show_detail(0)

    def _rebuild_list(self) -> None:
        lv = self.query_one("#entries-list", ListView)
        lv.clear()

        if not self._entries:
            lv.append(ListItem(Static("[dim]No boot entries found.[/dim]")))
            return

        for i, entry in enumerate(self._entries):
            source_color = self._source_color(entry.source)
            text = (
                f" {entry.display_title}\n"
                f"   [dim]source:[/dim] [{source_color}]{entry.source_label}[/{source_color}]"
            )
            lv.append(ListItem(Static(text)))

    def _update_script_status(self) -> None:
        status = get_script_status()
        lines  = []
        for name, executable in status.items():
            if executable is None:
                lines.append(f"  [dim]{name:25s} not installed[/dim]")
            elif executable:
                lines.append(
                    f"  [green]●[/green] [dim]{name:25s}[/dim] [green]enabled[/green]"
                )
            else:
                lines.append(
                    f"  [yellow]●[/yellow] [dim]{name:25s}[/dim] [yellow]disabled[/yellow]"
                )
        self.query_one("#script-status", Static).update("\n".join(lines))

    # ── Selection ─────────────────────────────────────────────────────────────

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._entries):
            self._selected_idx = idx
            self._show_detail(idx)
            # Pre-fill rename input with current title
            self.query_one("#rename-input", Input).value = \
                self._entries[idx].title

    def _show_detail(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._entries):
            return

        entry        = self._entries[idx]
        source_color = self._source_color(entry.source)

        header = (
            f"[bold #89b4fa]{entry.title}[/bold #89b4fa]\n"
            f"[dim]Type:  [/dim][#cdd6f4]{entry.entry_type}[/#cdd6f4]\n"
            f"[dim]Source:[/dim] [{source_color}]{entry.source_label}[/{source_color}]\n"
            f"[dim]Order: [/dim][#cdd6f4]{idx + 1} of {len(self._entries)}[/#cdd6f4]\n"
            + (
                f"[dim]Children ({len(entry.children)}):[/dim]\n"
                + "\n".join(f"  [dim]• {c}[/dim]" for c in entry.children[:5])
                if entry.children else ""
            )
        )
        self.query_one("#entry-detail-header", Static).update(header)

    def _source_color(self, source: str) -> str:
        colors = {
            "10_linux":           "#89b4fa",
            "30_os-prober":       "#f9e2af",
            "30_uefi-firmware":   "#a6e3a1",
            "41_snapshots-btrfs": "#f5c2e7",
            "40_custom":          "#cba6f7",
        }
        return colors.get(source, "#a6adc8")

    # ── Move up / down ────────────────────────────────────────────────────────

    def action_move_up(self) -> None:
        idx = self._selected_idx
        if idx <= 0 or idx >= len(self._entries):
            return
        self._entries[idx], self._entries[idx - 1] = \
            self._entries[idx - 1], self._entries[idx]
        self._selected_idx = idx - 1
        self._rebuild_list()
        self._show_detail(self._selected_idx)
        self._set_status(
            f"Moved '{self._entries[self._selected_idx].title}' up.", "info"
        )

    def action_move_down(self) -> None:
        idx = self._selected_idx
        if idx < 0 or idx >= len(self._entries) - 1:
            return
        self._entries[idx], self._entries[idx + 1] = \
            self._entries[idx + 1], self._entries[idx]
        self._selected_idx = idx + 1
        self._rebuild_list()
        self._show_detail(self._selected_idx)
        self._set_status(
            f"Moved '{self._entries[self._selected_idx].title}' down.", "info"
        )

    # ── Rename ────────────────────────────────────────────────────────────────

    def action_start_rename(self) -> None:
        self.query_one("#rename-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "rename-input":
            self._do_rename()

    def _do_rename(self) -> None:
        idx = self._selected_idx
        if idx < 0 or idx >= len(self._entries):
            self._set_status("No entry selected.", "warn")
            return

        new_title = self.query_one("#rename-input", Input).value.strip()
        if not new_title:
            self._set_status("Name cannot be empty.", "warn")
            return

        old_title = self._entries[idx].title
        if new_title == old_title:
            self._set_status("Name is unchanged.", "info")
            return

        try:
            self._entries[idx] = rename_entry(self._entries[idx], new_title)
            self._rebuild_list()
            self._show_detail(idx)
            self._set_status(
                f"Renamed: '{old_title}' → '{new_title}'  —  Press S to save.", "info"
            )
        except Exception as e:
            self._set_status(f"Rename failed: {e}", "error")

    # ── Buttons ───────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-up":
                self.action_move_up()
            case "btn-down":
                self.action_move_down()
            case "btn-save":
                self.action_save_order()
            case "btn-restore":
                self.action_restore_order()
            case "btn-refresh":
                self.action_refresh()
            case "btn-rename":
                self._do_rename()
            case "btn-rename-clear":
                self.query_one("#rename-input", Input).value = ""

    # ── Save order ────────────────────────────────────────────────────────────

    def action_save_order(self) -> None:
        self.app.run_worker(self._save_order_worker(), exclusive=True)

    async def _save_order_worker(self) -> None:
        if not self._entries:
            self._set_status("No entries to save.", "warn")
            return

        order_summary = "\n".join(
            f"  {i+1}. {e.title}" for i, e in enumerate(self._entries)
        )
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Save Custom Boot Order",
                message=(
                    f"Save this boot order:\n\n"
                    f"{order_summary}\n\n"
                    f"This will:\n"
                    f"• Write order to /etc/grub.d/40_custom\n"
                    f"• Disable auto-generate scripts\n"
                    f"• Regenerate grub.cfg"
                ),
                confirm_label="Save & Apply",
                confirm_variant="success",
            )
        )
        if not confirmed:
            return

        try:
            write_custom_order(self._entries)
            self._set_status("Written to 40_custom…", "info")

            scripts_to_disable = set(
                e.source for e in self._entries
                if e.source in MANAGED_SCRIPTS
            )
            for script in scripts_to_disable:
                disable_script(script)
            self._set_status("Scripts disabled…", "info")

            success, output = regenerate_grub()
            if success:
                self._set_status(
                    "Boot order saved and grub.cfg regenerated successfully!", "ok"
                )
            else:
                self._set_status(
                    f"grub-mkconfig failed: {output[:80]}", "error"
                )

            self._update_script_status()

        except PermissionError:
            self._set_status(
                "Permission denied — run GrubForge with sudo.", "error"
            )
        except Exception as e:
            self._set_status(f"Error: {e}", "error")

    # ── Restore original order ────────────────────────────────────────────────

    def action_restore_order(self) -> None:
        self.app.run_worker(self._restore_order_worker(), exclusive=True)

    async def _restore_order_worker(self) -> None:
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Restore Original Boot Order",
                message=(
                    "This will:\n"
                    "• Re-enable all auto-generate scripts\n"
                    "• Clear your custom 40_custom order\n"
                    "• Regenerate grub.cfg automatically\n\n"
                    "Your current custom order will be lost."
                ),
                confirm_label="Restore",
                confirm_variant="warning",
            )
        )
        if not confirmed:
            return

        try:
            restore_original_order()
            self._set_status("Scripts restored…", "info")

            success, output = regenerate_grub()
            if success:
                self._set_status(
                    "Original order restored and grub.cfg regenerated!", "ok"
                )
            else:
                self._set_status(
                    f"grub-mkconfig failed: {output[:80]}", "error"
                )

            self._load_entries()

        except PermissionError:
            self._set_status(
                "Permission denied — run GrubForge with sudo.", "error"
            )
        except Exception as e:
            self._set_status(f"Error: {e}", "error")

    # ── Refresh ───────────────────────────────────────────────────────────────

    def action_refresh(self) -> None:
        self._load_entries()
        self._set_status("Boot entries refreshed.", "info")

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