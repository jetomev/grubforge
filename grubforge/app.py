"""
GrubForge — Main Application
Textual TUI shell: sidebar navigation + screen router.
Catppuccin Mocha themed throughout.
"""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Static
from textual.containers import Container, Vertical

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
    "dashboard":      "GrubForge › Home",
    "config-editor":  "GrubForge › /etc/default/grub",
    "themes":         "GrubForge › Themes",
    "backup-restore": "GrubForge › Backup & Restore",
    "boot-entries":   "GrubForge › Boot Entries",
}

VERSION = "v0.1.0"


# ── App ───────────────────────────────────────────────────────────────────────

class GrubForgeApp(App):
    """GrubForge — GRUB Bootloader TUI Manager."""

    TITLE    = "GrubForge"
    CSS_PATH = Path(__file__).parent / "grubforge.css"

    BINDINGS = [
        Binding("1",      "show_dashboard",  "Dashboard",     show=False),
        Binding("2",      "show_config",     "Config Editor", show=False),
        Binding("3",      "show_themes",     "Themes",        show=False),
        Binding("4",      "show_backup",     "Backup",        show=False),
        Binding("5",      "show_boot_entries", "Boot Entries", show=False),
        Binding("q",      "quit",            "Quit",          show=True),
        Binding("?",      "show_help",       "Help",          show=True),
        Binding("ctrl+c", "quit",            "Quit",          show=False),
    ]

    _active: str = "dashboard"

    # ── Layout ────────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="sidebar"):
            yield Static(_logo(), id="sidebar-logo")
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
                _header("🏠  Dashboard", "GrubForge › Home"),
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
            "1 Dashboard  2 Config  3 Themes  4 Backup  5 Boot Entries\n"
            "E Edit value  S Save  R Refresh  Ctrl+R Regen grub.cfg\n"
            "K Move up  J Move down  B New backup  D Delete  q Quit",
            title="⚡ GrubForge Help",
            timeout=8,
        )

    def on_static_click(self, event: Static.Clicked) -> None:
        wid = getattr(event.widget, "id", "") or ""
        if wid.startswith("nav-"):
            self._switch_to(wid[4:])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _logo() -> str:
    return (
        "[bold #89b4fa]⚡ GrubForge[/bold #89b4fa]\n"
        f"[dim #6c7086]GRUB TUI Manager {VERSION}[/dim #6c7086]"
    )

def _header(label: str, crumb: str) -> str:
    crumb_part = f"  [dim #6c7086]{crumb}[/dim #6c7086]" if crumb else ""
    return f"[bold #89b4fa] {label}[/bold #89b4fa]{crumb_part}"

def _status_bar() -> str:
    return (
        "[dim #585b70]"
        "1 Dashboard  2 Config  3 Themes  4 Backup  5 Boot Entries  │  "
        "E Edit  S Save  R Refresh  Ctrl+R Regen  │  "
        "? Help  q Quit"
        "[/dim #585b70]"
    )