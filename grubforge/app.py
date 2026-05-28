"""
grubForge — Main Application
Textual TUI shell: sidebar navigation + screen router.
Catppuccin Mocha themed throughout.
"""

import os
from pathlib import Path

from textual import events, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from textual.containers import Container, Vertical

from grubforge.config_manager import regenerate_grub
from grubforge.widgets.confirm_dialog import ConfirmDialog
from grubforge.screens.dashboard     import DashboardScreen
from grubforge.screens.config_editor import ConfigEditorScreen
from grubforge.screens.themes        import ThemesScreen
from grubforge.screens.backup        import BackupScreen
from grubforge.screens.boot_entries  import BootEntriesScreen


# ── Navigation config ─────────────────────────────────────────────────────────

NAV_ITEMS = [
    ("1", "dashboard",       "🏠  Dashboard"),
    ("2", "config-editor",   "🔧  Config Editor"),
    ("3", "themes",          "🎨  Themes"),
    ("4", "backup-restore",  "🗂  Backup & Restore"),
    ("5", "boot-entries",    "🖥  Boot Entries"),
]

SCREEN_WIDGET_IDS = {
    "dashboard":      "screen-dashboard",
    "config-editor":  "screen-config-editor",
    "themes":         "screen-themes",
    "backup-restore": "screen-backup-restore",
    "boot-entries":   "screen-boot-entries",
}

BREADCRUMBS = {
    "dashboard":      "grubForge › Home",
    "config-editor":  "grubForge › /etc/default/grub",
    "themes":         "grubForge › Themes",
    "backup-restore": "grubForge › Backup & Restore",
    "boot-entries":   "grubForge › Boot Entries",
}

VERSION = "v1.0.1"


# ── App ───────────────────────────────────────────────────────────────────────

class GrubForgeApp(App):
    """grubForge — GRUB Bootloader TUI Manager."""

    TITLE    = "grubForge"
    CSS_PATH = Path(__file__).parent / "grubforge.css"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.read_only_mode = os.geteuid() != 0

    BINDINGS = [
        Binding("1",      "show_dashboard",  "Dashboard",     show=False),
        Binding("2",      "show_config",     "Config Editor", show=False),
        Binding("3",      "show_themes",     "Themes",        show=False),
        Binding("4",      "show_backup",     "Backup",        show=False),
        Binding("5",      "show_boot_entries", "Boot Entries", show=False),
        Binding("q",      "quit",            "Quit",          show=True),
        Binding("?",      "show_help",       "Help",          show=True),
        Binding("ctrl+c", "quit",            "Quit",          show=False),
        # Universal action bindings — dispatched to the active screen
        Binding("e",      "global_edit",    "Edit",            show=False),
        Binding("s",      "global_save",    "Save",            show=False),
        Binding("a",      "global_apply",   "Apply",           show=False),
        Binding("r",      "global_refresh", "Refresh",         show=False),
        Binding("ctrl+r", "global_regen",   "Regen grub.cfg",  show=False),
    ]

    _active: str = "dashboard"

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Static(_logo(self.read_only_mode), id="sidebar-logo")
            with Vertical(id="nav-list"):
                for key, sid, label in NAV_ITEMS:
                    active_cls = "nav-item active" if sid == "dashboard" else "nav-item"
                    yield Static(
                        f" [dim]{key}[/dim]  {label}",
                        id=f"nav-{sid}",
                        classes=active_cls,
                    )
            yield Static("[dim]? help  •  q quit[/dim]", id="sidebar-footer")

        with Vertical(id="content-area"):
            yield Static(
                _header("🏠  Dashboard", "grubForge › Home"),
                id="screen-header",
                classes="screen-header",
            )
            yield DashboardScreen(id="screen-dashboard")
            yield ConfigEditorScreen(
                id="screen-config-editor", classes="hidden-screen"
            )
            yield ThemesScreen(
                id="screen-themes", classes="hidden-screen"
            )
            yield BackupScreen(
                id="screen-backup-restore", classes="hidden-screen"
            )
            yield BootEntriesScreen(
                id="screen-boot-entries", classes="hidden-screen"
            )
            yield Static(_status_bar(), id="status-bar")

    def on_mount(self) -> None:
        self._switch_to("dashboard")

    # ── Screen switching ──────────────────────────────────────────────────────

    def _switch_to(self, screen_id: str) -> None:
        if screen_id not in SCREEN_WIDGET_IDS:
            return

        for _, sid, _ in NAV_ITEMS:
            nav = self.query_one(f"#nav-{sid}", Static)
            if sid == screen_id:
                nav.set_classes("nav-item active")
            else:
                nav.set_classes("nav-item")

        for sid, wid in SCREEN_WIDGET_IDS.items():
            w = self.query_one(f"#{wid}")
            w.display = (sid == screen_id)

        # F4/F5/F8: re-read disk state every time a screen is shown, so changes
        # made on another screen (a Config Editor save, a new backup, a theme
        # apply) are reflected without a manual R. The hook is silent — only an
        # explicit R press (action_refresh) emits feedback.
        shown = self.query_one(f"#{SCREEN_WIDGET_IDS[screen_id]}")
        reload_view = getattr(shown, "_reload_view", None)
        if callable(reload_view):
            reload_view()

        label = next(lbl for _, sid, lbl in NAV_ITEMS if sid == screen_id)
        crumb = BREADCRUMBS.get(screen_id, "")
        self.query_one("#screen-header", Static).update(
            _header(label, crumb)
        )

        self._active = screen_id

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_show_dashboard(self) -> None:
        self._switch_to("dashboard")

    def action_show_config(self) -> None:
        self._switch_to("config-editor")

    def action_show_themes(self) -> None:
        self._switch_to("themes")

    def action_show_backup(self) -> None:
        self._switch_to("backup-restore")
        
    def action_show_boot_entries(self) -> None:
        self._switch_to("boot-entries")

    def action_show_help(self) -> None:
        self.notify(
            "1 Dashboard  2 Config  3 Themes  4 Backup  5 Boot Entries  q Quit\n"
            "Universal: E Edit  S Save  A Apply  R Refresh  Ctrl+R Regen grub.cfg\n"
            "Boot Entries: K up  J down  N rename  X restore original\n"
            "Backup: N new  X restore  D delete\n"
            "Themes: H install help\n"
            "[dim]Press Esc to close (auto-dismisses in 8s)[/dim]",
            title="⚡ grubForge Help",
            timeout=8,
        )

    # ── Universal action dispatchers ──────────────────────────────────────────

    def _dispatch(self, methods: list, action_label: str) -> None:
        """Try each method name on the active screen widget; notify if none match."""
        sid = SCREEN_WIDGET_IDS.get(self._active)
        if not sid:
            return
        screen_widget = self.query_one(f"#{sid}")
        for method_name in methods:
            fn = getattr(screen_widget, method_name, None)
            if callable(fn):
                fn()
                return
        self.notify(
            f"{action_label} isn't available on this screen.",
            severity="information",
            timeout=3,
        )

    def action_global_edit(self) -> None:
        self._dispatch(["action_start_edit"], "Edit")

    def action_global_save(self) -> None:
        self._dispatch(["action_save_changes", "action_save_order"], "Save")

    def action_global_apply(self) -> None:
        # F13: include the Config Editor's apply method so keyboard `A` mirrors
        # its "Apply Edit" button (previously only action_apply_theme was tried,
        # so A was rejected on the Config Editor while the button worked).
        self._dispatch(["action_apply_edit", "action_apply_theme"], "Apply")

    def action_global_refresh(self) -> None:
        self._dispatch(["action_refresh"], "Refresh")

    # F7/F11: grub.cfg regeneration is a universal app action, not a screen-
    # local one. Run grub-mkconfig directly at app level so Ctrl+R works from
    # ANY screen (previously it dispatched to a screen-local action_regen_grub
    # that only the Config Editor implemented — silent/no-op elsewhere, and the
    # Dashboard's own Sync prompt told users to press Ctrl+R but nothing fired).
    @work
    async def action_global_regen(self) -> None:
        if self.read_only_mode:
            self.notify(
                "Read-only mode — relaunch with sudo to regenerate grub.cfg.",
                severity="warning", timeout=4,
            )
            return
        confirmed = await self.push_screen_wait(
            ConfirmDialog(
                title="Regenerate grub.cfg",
                message=(
                    "This will run:\n"
                    "  grub-mkconfig -o /boot/grub/grub.cfg\n\n"
                    "Make sure all changes are saved first."
                ),
                confirm_label="Regenerate",
                confirm_variant="warning",
            )
        )
        if not confirmed:
            return

        self.notify("Running grub-mkconfig…", severity="information", timeout=4)
        success, output = regenerate_grub()
        if success:
            self.notify(
                "grub-mkconfig succeeded! Boot menu updated.",
                severity="information", timeout=4,
            )
        else:
            self.notify(
                f"grub-mkconfig failed: {output[:80]}",
                severity="error", timeout=6,
            )
        # Reflect the regen on whatever screen is active (e.g. Dashboard sync).
        self._reload_active()

    def _reload_active(self) -> None:
        """Silently re-read the active screen's view (post global action)."""
        sid = SCREEN_WIDGET_IDS.get(self._active)
        if not sid:
            return
        fn = getattr(self.query_one(f"#{sid}"), "_reload_view", None)
        if callable(fn):
            fn()

    # Textual 8.x removed `Static.Clicked` (the v1.0.1 F16 break — see GitHub
    # Issue #1). Use the generic `events.Click` and filter by widget id; this
    # works in both old and new Textual since `Click` is the underlying event
    # type the now-removed `Static.Clicked` was a subclass of.
    def on_click(self, event: events.Click) -> None:
        wid = getattr(event.widget, "id", "") or ""
        if wid.startswith("nav-"):
            self._switch_to(wid[4:])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _logo(read_only: bool = False) -> str:
    badge = (
        "\n[bold #f38ba8 reverse] DEMO [/bold #f38ba8 reverse] [dim #6c7086]read-only[/dim #6c7086]"
        if read_only else ""
    )
    return (
        "[bold #89b4fa]⚡ grubForge[/bold #89b4fa]\n"
        f"[dim #6c7086]GRUB TUI Manager {VERSION}[/dim #6c7086]"
        f"{badge}"
    )

def _header(label: str, crumb: str) -> str:
    crumb_part = f"  [dim #6c7086]{crumb}[/dim #6c7086]" if crumb else ""
    return f"[bold #89b4fa] {label}[/bold #89b4fa]{crumb_part}"

def _status_bar() -> str:
    return (
        "[dim #585b70]"
        "1-5 nav  │  "
        "E Edit  S Save  A Apply  R Refresh  Ctrl+R Regen  │  "
        "? Help  q Quit"
        "[/dim #585b70]"
    )