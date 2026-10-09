"""grubForge v2.0.0 — the app shell, on forgekit.

The frame is forgekit's (title bar, menu bar, changes bar, hint bar); the
screens are grubForge's. All file work goes through the Session and the
privileged helper. Javier's rulings for v2.0.0 (2 Oct 2026, design page
docs/design/v2.0.0-screens.html):

* Settings is a form with visible controls; known values are picked.
* Save (F10) and Rebuild (F9) are separate; what is saved stays saved, and
  "saved, not rebuilt" shows in the changes bar until the boot menu is rebuilt.
* Quitting with unsaved or unrebuilt work asks first; the terminal gets a
  closing note after the app closes (main.py).
"""

from __future__ import annotations

import os

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from forgekit import (
    FORGE_CSS, GPL3_NOTICE, MENU_HINT, ChangeGroup, ForgeApp, ForgeModal, ForgePanelScreen, Notice,
    ProgressDialog, ReviewDialog, load_pages,
)

from . import privilege
from . import __version__
from .session import Session
from .settings_spec import BY_KEY, GROUPS
from .ui.backups import BackupsScreen
from .ui.bootmenu import BootMenuScreen
from .ui.themes import ThemesScreen
from .ui.overview import OverviewScreen
from .ui.settings import SettingsScreen

MANUAL_DIR = os.path.join(os.path.dirname(__file__), "manual")

GF_CSS = FORGE_CSS + """
/* grubForge's own sections, coloured only through forgekit's roles */
#gf-groups { width: 20; height: 1fr; border: none; border-right: solid $forge-border; background: $forge-bg; padding: 1 1 0 0; }
#gf-settings-right { width: 1fr; height: 1fr; padding: 0 0 0 2; }
#gf-groupforms { height: 1fr; }
.gf-group { height: 1fr; padding: 0 1 0 0; }
.gf-group-title { height: auto; margin: 0 0 1 0; }
#gf-about { height: auto; min-height: 4; max-height: 7; padding: 1 0 0 0; color: $forge-text; }
.gf-kernel { height: auto; width: 1fr; }
.gf-kernel-known { width: 1fr; max-width: 80; }
.gf-kernel-other-line { height: auto; }
.gf-kernel-other-label { width: auto; height: 3; padding: 0 2 0 0; content-align: left middle; color: $forge-muted; }
.gf-kernel-other { width: 1fr; max-width: 64; }
.gf-kernel-problem { height: auto; }
.gf-colours { height: 3; width: auto; }
.gf-colours > Select { width: 20; }
.gf-colour-on { width: auto; height: 3; padding: 0 1; content-align: center middle; color: $forge-muted; }
.gf-colour-sample { width: auto; height: 3; padding: 0 0 0 1; content-align: left middle; }
#gf-overview { grid-size: 2 2; grid-columns: 1fr 1fr; grid-rows: auto auto; grid-gutter: 1 2; height: auto; padding: 0 2 0 0; }
.gf-box { height: auto; border: round $forge-border; border-title-color: $forge-accent; border-title-style: bold; padding: 0 1; }
.gf-attention { border: round $forge-warn; border-title-color: $forge-warn; }
.gf-box-buttons, .gf-task-row { padding: 1 0 0 0; align-horizontal: left; }
.forge-buttons.gf-task-row Button { margin: 0 2 0 0; width: 1fr; min-width: 0; padding: 0 1; }
.forge-buttons.gf-task-row Button:last-child { margin: 0; }
.gf-box-buttons Button { margin: 0 2 0 0; }
#ov-attention { height: auto; }
.gf-att-head { height: auto; }
.gf-att-body { height: auto; padding: 0 0 0 3; margin: 0 0 1 0; }
.gf-att-body:last-child { margin: 0; }
.gf-soon { padding: 1 0; }
#gf-quit-msg { height: auto; padding: 0 0 1 0; }
#sec-boot { padding: 0 2 0 0; }
#bm-table { height: auto; max-height: 20; margin: 1 0 0 0; border: solid $forge-field-border; background: $forge-bg; }
#bm-table:focus { border: solid $forge-accent; }
#bm-actions, #bm-more, #bm-undo { padding: 1 0 0 0; align-horizontal: left; height: auto; }
#bm-actions Button, #bm-more Button, #bm-undo Button { margin: 0 2 0 0; }
#bm-read, #bm-stale { align-horizontal: left; height: auto; }
.gf-small { width: 76; }
.gf-add { width: 96; }
.gf-add-line { height: 3; }
.gf-add-label { width: 18; height: 3; content-align: left middle; color: $forge-text; }
.gf-add-line > Select, .gf-add-line > Input { width: 1fr; }
#ae-block { height: 9; margin: 0 0 1 0; }
.gf-add-sep { margin: 1 0 0 0; }
#os-status { padding: 1 0; }
#os-results { height: auto; padding: 0 0 1 0; }
#sec-themes, #sec-backups { padding: 0 2 0 0; }
#th-left { width: 34; height: 1fr; }
#th-list { height: 1fr; max-height: 20; }
#th-where { height: auto; padding: 1 0 0 0; }
#th-right { width: 1fr; height: 1fr; padding: 0 0 0 3; }
#th-preview-title { height: auto; margin: 1 0 1 0; }
#th-preview { height: auto; width: auto; }
#th-info { height: auto; margin: 1 0 0 0; }
.th-actions { padding: 1 0 0 0; align-horizontal: left; height: auto; }
.th-actions Button { margin: 0 2 0 0; }
#bk-left { width: 1fr; min-width: 46; height: 1fr; }
#bk-table { height: auto; max-height: 14; border: solid $forge-field-border; background: $forge-bg; }
#bk-table:focus { border: solid $forge-accent; }
#bk-where { height: auto; padding: 1 0 0 0; }
.bk-actions { padding: 1 0 0 0; align-horizontal: left; height: auto; }
.forge-buttons.bk-actions Button { margin: 0 2 0 0; width: 1fr; min-width: 0; padding: 0 1; }
.forge-buttons.bk-actions Button:last-child { margin: 0; }
#bk-right { width: 1fr; max-width: 64; height: auto; max-height: 1fr; margin: 2 0 0 2; }
"""


class QuitDialog(ForgeModal[str | None]):
    """Before you go: unsaved changes, or saved ones not in the boot menu yet."""

    BINDINGS = [Binding("escape", "stay", "", show=False)]

    def __init__(self, heading: str, lines: list[str], buttons: list[tuple[str, str, bool]]) -> None:
        super().__init__()
        self._heading, self._lines, self._buttons = heading, lines, buttons

    def compose(self) -> ComposeResult:
        with Vertical(classes="forge-panel gf-quit"):
            yield Static("Before you go", classes="forge-panel-title")
            yield Notice(self._heading, self._lines, level="warn", id="gf-quit-msg")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                for label, bid, primary in self._buttons:
                    yield Button(label, id=bid, variant="primary" if primary else "default")
                yield Button("Stay (Esc)", id="stay")

    def on_mount(self) -> None:
        self.query_one(f"#{self._buttons[0][1]}", Button).focus()

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        self.dismiss(None if e.button.id == "stay" else e.button.id)

    def action_stay(self) -> None:
        self.dismiss(None)


class FieldHelp(ForgePanelScreen):
    CLOSE_KEYS = ("f1",)

    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.panel_title = title
        self._text = text

    def compose_body(self) -> ComposeResult:
        yield Static(self._text)


class GrubForgeApp(ForgeApp):
    APP_NAME = f"grubForge {__version__} · GRUB boot menu manager"
    SHOW_HINT_BAR = True
    SHOW_CHANGES_BAR = True
    CSS = GF_CSS
    LICENSE_NOTICE = GPL3_NOTICE
    MENU = [
        {"id": "overview", "title": "Overview", "kind": "section"},
        {"id": "settings", "title": "Settings", "kind": "section"},
        {"id": "boot", "title": "Boot Menu", "kind": "section"},   # F-7 (#39)
        {"id": "themes", "title": "Themes", "kind": "section"},
        {"id": "backups", "title": "Backups", "kind": "section"},
        {"id": "help", "title": "Help", "kind": "menu", "items": [
            ("Manual", "m", "manual"), ("Keys", "k", "shortcuts"),
            ("License", "l", "license"), ("About", "a", "about")]},
        {"id": "quit", "title": "Quit", "kind": "action", "action": "quit"},
    ]
    SHORTCUTS = [
        ("Tab / Shift+Tab", "next / previous field or button"),
        ("Enter", "open a list, press a button, confirm"),
        ("Space", "flip a switch, tick a box"),
        ("Esc", "close a window, or leave About / License"),
        ("1-6, Ctrl+letter", "go to a menu entry (Help is 6)"),
        ("F10 or S", "save, with a review first"),
        ("F9 or Ctrl+R", "rebuild the boot menu"),
        ("R", "read the files again"),
        ("F1", "help on what is selected"),
        ("M", "the manual (Backspace: its previous page)"),
        ("?", "this list"),
        ("Q or Ctrl+Q", "quit (asks first if something isn't finished)"),
        ("", "not there inside hypeForge Settings"),
    ]
    # 2.2.0 (F-6, #38): "1-6 menu". The numbers 1-6 (Help is 6) and Ctrl + each underlined
    # letter come from forgekit 0.10.0, made from MENU; grubForge no longer binds its own
    HINTS = [("Tab", "next"), MENU_HINT, ("F10", "save"), ("F9", "rebuild"), ("F1", "help"), ("?", "all keys")]
    BINDINGS = [
        Binding("f10", "save", show=False, priority=True), Binding("s", "save", show=False),
        Binding("f9", "rebuild", show=False, priority=True), Binding("ctrl+r", "rebuild", show=False, priority=True),
        Binding("r", "reload", show=False),
        Binding("f1", "field_help", show=False, priority=True),
        Binding("m", "act('manual')", show=False),
        Binding("question_mark", "act('shortcuts')", show=False),
        Binding("q", "act('quit')", show=False),
    ]

    def __init__(self, session: Session | None = None, **kw) -> None:
        self.session = session or Session.load()
        self.ABOUT = {
            "name": "grubForge", "version": __version__,
            "tagline": "The GRUB boot menu, without editing files by hand",
            "description": "Part of the Forge Suite for KognogOS. Works on every major Linux distribution.",
            "authors": "jetomev (Javier) · Claude (Anthropic), co-developer",
            "license": "GPL-3.0-or-later",
            "links": [("Code", "https://github.com/jetomev/grubforge")],
        }
        super().__init__(**kw)

    def compose_sections(self) -> ComposeResult:
        yield OverviewScreen(self.session, id="sec-overview")
        yield SettingsScreen(self.session, id="sec-settings")
        yield BootMenuScreen(self.session, id="sec-boot")
        yield ThemesScreen(self.session, id="sec-themes")
        yield BackupsScreen(self.session, id="sec-backups")

    PASSWORD_TITLE = "grubForge needs your password"

    def on_mount(self) -> None:
        super().on_mount()
        # v2.1 (Javier, 4 Oct 2026): polkit's password question is asked in
        # grubForge's own box, on a desktop and on a text console alike —
        # grubForge becomes polkit's password asker for its own process only
        if self.session.capability.level.value == "polkit":
            agent = self.polkit_agent()
            privilege.IN_APP_AGENT = agent.active
            if not agent.active:
                self.notify(f"The password will be asked the usual way: {agent.reason}.",
                            title="Password", severity="warning", timeout=10)
        user = os.environ.get("USER", "")
        mode = {"root": "no password needed", "polkit": "password at save",
                "none": "read-only"}[self.session.capability.level.value]
        self.set_title_status(f"{self.session.env.distro} · {user} · {mode}")
        self.refresh_state()

    # ── navigation (the keys to each menu entry are forgekit's, from MENU) ──
    def on_section_shown(self, section_id: str) -> None:
        # the files may have changed outside grubForge (#17): read them again;
        # unsaved changes stay
        self.session.reload()
        self.query_one(SettingsScreen).sync()
        self.query_one(SettingsScreen).frozen_notice()
        self.refresh_state()
        if section_id == "overview":
            self.query_one(OverviewScreen).refresh_view()
        if section_id == "settings":
            self.query_one("#gf-groups").focus()
        if section_id == "themes":
            self.query_one(ThemesScreen).refresh_view()
            self.query_one("#th-list").focus()
        if section_id == "backups":
            self.query_one(BackupsScreen).refresh_view()
            self.query_one("#bk-table").focus()
        if section_id == "boot":
            self.query_one(BootMenuScreen).refresh_view()
            self.query_one("#bm-table").focus()

    def on_action(self, action_id: str) -> None:
        if action_id == "manual":
            self.open_manual()

    def open_manual(self, page: str | None = None) -> None:
        pages = load_pages(MANUAL_DIR) if os.path.isdir(MANUAL_DIR) else []
        if not pages:
            self.notify("The manual isn't installed here.", severity="warning")
            return
        # 2.2.0 (Javier, 10-08): a page in the main area, Help lit; Esc goes back where you were
        self.show_manual("grubForge manual", pages, start=page)

    def action_field_help(self) -> None:
        from forgekit import SettingRow
        w = self.focused
        chain = list(w.ancestors_with_self) if w is not None else []
        pages = load_pages(MANUAL_DIR) if os.path.isdir(MANUAL_DIR) else []
        for screen, page in ((BootMenuScreen, "boot-menu"), (ThemesScreen, "themes"),
                             (BackupsScreen, "backups"), (OverviewScreen, "start")):
            if pages and any(isinstance(a, screen) for a in chain):
                self.open_manual(page=page)
                return
        if w is not None and any(isinstance(a, BootMenuScreen) for a in w.ancestors_with_self):
            self.push_screen(FieldHelp("Your own boot order", (
                "GRUB normally builds the menu by itself every time it is rebuilt, and new kernels appear on "
                "their own.\n\nSaving your own order writes the entries, as you arranged them, to "
                "[b]/etc/grub.d/40_custom[/] and turns off the scripts that made them. That keeps your order, "
                "but those scripts no longer add anything new: a kernel update won't appear until you go "
                "[b]Back to the Original Order[/].\n\nEntries made by other tools (snapshots) are fixed: "
                "their tool keeps placing them, and grubForge never copies them into your order.")))
            return
        row = next((a for a in (w.ancestors_with_self if w else []) if isinstance(a, SettingRow)), None)
        if row is None:
            self.action_act("shortcuts")
            return
        s = BY_KEY[row.setting]
        pages = load_pages(MANUAL_DIR) if os.path.isdir(MANUAL_DIR) else []
        if pages:
            self.open_manual(page=s.group)
            return
        self.push_screen(FieldHelp(s.label, f"{escape(s.help)}\n\n[$forge-muted]GRUB name: {s.key}[/]"))

    # ── state: the changes bar ───────────────────────────────────────────────
    def refresh_state(self) -> None:
        s, bar = self.session, self.changes_bar
        n = s.change_count()
        if n:
            bar.show(f"{n} change{'s' if n != 1 else ''} not saved yet", "changed",
                     [("Save Changes (s)", "gf-save", True), ("Discard Changes", "gf-discard", False)])
        elif s.not_rebuilt and not s.read_only:
            when = s.last_saved()
            bar.show(f"Saved{f' at {when:%I:%M %p}' if when else ''} · not in the boot menu yet", "warn",
                     [("Rebuild Boot Menu (F9)", "gf-rebuild", True), ("Why?", "gf-why", False)])
        else:
            bar.hide()

    def on_button_pressed(self, e: Button.Pressed) -> None:
        bid = e.button.id or ""
        if bid in ("gf-save",):
            self.action_save()
        elif bid == "gf-discard":
            self.session.discard()
            self.query_one(SettingsScreen).sync()
            self.query_one(BootMenuScreen).refresh_view()
            self.refresh_state()
            self.notify("Changes discarded. Nothing was written.")
        elif bid in ("gf-rebuild", "ov-rebuild"):
            self.action_rebuild()
        elif bid in ("gf-why", "ov-why"):
            self.push_screen(FieldHelp(
                "Saved, not rebuilt",
                "GRUB doesn't read your settings while the computer starts. It reads the boot menu "
                f"([b]{self.session.env.grub_cfg}[/]), which is built from your settings by "
                f"[b]{self.session.env.mkconfig}[/].\n\nSaving writes your settings. Rebuilding makes the "
                "boot menu from them. Until you rebuild, the computer starts with the old menu.\n\n"
                "Press [b]Rebuild Boot Menu (F9)[/] when you're ready."))
        elif bid == "task-default":
            self._switch_section("settings")
            self.query_one(SettingsScreen).show_group("startup")
            self.query_one("#row-GRUB_DEFAULT").control.focus()
        elif bid == "task-timeout":
            self._switch_section("settings")
            self.query_one(SettingsScreen).show_group("startup")
            self.query_one("#row-GRUB_TIMEOUT").control.query_one("Input").focus()
        elif bid == "task-theme":
            self._switch_section("themes")
        elif bid == "task-backup":
            self.action_backup_now()

    # ── save, rebuild, reload ────────────────────────────────────────────────
    @work(exclusive=True, group="gf-write")
    async def action_save(self) -> None:
        s = self.session
        if s.read_only:
            self.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return
        if not s.pending and not s.boot_changed:
            self.notify("Nothing to save: no changes.")
            return
        problems = s.problems()
        if problems:
            self.notify("\n".join(problems), title="Can't save yet", severity="error", timeout=10)
            return
        settings = self.query_one(SettingsScreen)
        groups = []
        if s.pending:
            groups.append(ChangeGroup("Settings", "/etc/default/grub", s.changes(
                lambda k: settings.choices_for(k) if BY_KEY[k].control in ("list", "file") else None)))
        if s.boot_changed:
            groups.append(ChangeGroup("Boot order", "/etc/grub.d/40_custom", s.boot.changes()))
        steps = ["A backup of your settings is saved", "The changes are written"]
        if s.boot_changed and s.boot.scripts_to_turn_off():
            steps.append("The scripts that made these entries are turned off, so your order stays")
        steps.append('Rebuild the boot menu: now with "Save and Rebuild", or later with F9')
        note = s.capability.prompt_note or ""
        choice = await self.push_screen_wait(ReviewDialog(
            "Review before saving", groups, steps=steps,
            note=note,
            buttons=[("Save", "save", True), ("Save and Rebuild", "both", False)]))
        if choice is None:
            return
        rebuild = choice == "both"
        dlg = ProgressDialog("Saving" if not rebuild else "Saving and rebuilding", s.save_steps(rebuild))
        self.push_screen(dlg)
        ok = await s.save(rebuild, dlg.set_step, dlg.add_line)
        dlg.finish()
        settings.sync()
        self.query_one(BootMenuScreen).refresh_view()
        self.refresh_state()
        self.query_one(OverviewScreen).refresh_view()
        if ok and not rebuild:
            self.notify("Saved. Not in the boot menu yet: press F9 to rebuild.", title="Saved", timeout=8)
        elif ok:
            self.notify("Saved and rebuilt. The new menu shows at the next start.", title="Done", timeout=8)
        else:
            self.notify("Something didn't complete. The window shows which step and why.",
                        title="Not finished", severity="error", timeout=10)

    @work(exclusive=True, group="gf-write")
    async def action_rebuild(self) -> None:
        s = self.session
        if s.read_only:
            self.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return
        if s.pending:
            self.notify("You have unsaved changes; they won't be in the rebuilt menu. Save first (F10).",
                        severity="warning", timeout=8)
        dlg = ProgressDialog("Rebuilding the boot menu", [f"Rebuild the boot menu ({s.env.mkconfig})"])
        self.push_screen(dlg)
        ok = await s.rebuild(dlg.set_step, dlg.add_line)
        dlg.finish()
        self.refresh_state()
        self.query_one(OverviewScreen).refresh_view()
        self.notify("The new menu shows at the next start." if ok else "The boot menu is unchanged.",
                    title="Rebuilt" if ok else "Rebuild failed", severity="information" if ok else "error")

    @work(exclusive=True, group="gf-write")
    async def action_backup_now(self) -> None:
        from . import privilege
        s = self.session
        if s.read_only:
            self.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return
        r = await privilege.run_async("backup-create", "manual", capability=s.capability)
        self.query_one(OverviewScreen).refresh_view()
        self.notify("Backup saved." if r.ok else r.message, severity="information" if r.ok else "error")

    def action_reload(self) -> None:
        self.session.reload()
        self.query_one(SettingsScreen).sync()
        self.query_one(OverviewScreen).refresh_view()
        self.refresh_state()
        self.notify("Read the files again. Your unsaved changes are kept.")

    # ── quitting ─────────────────────────────────────────────────────────────
    # ── shared between screens ───────────────────────────────────────────────
    def after_files_changed(self) -> None:
        """Something wrote the files (a restore): re-read and redraw everything."""
        self.session.reload()
        self.query_one(SettingsScreen).sync()
        self.query_one(BackupsScreen).refresh_view()
        self.query_one(ThemesScreen).refresh_view()
        self.query_one(OverviewScreen).refresh_view()
        self.refresh_state()

    def settings_changed_elsewhere(self, key: str) -> None:
        """A setting changed from another screen (Boot Menu, Find Other Systems)."""
        self.query_one(SettingsScreen).sync()

    async def run_restore_original(self) -> None:
        s = self.session
        dlg = ProgressDialog("Going back to the original order", ["Hand the boot menu back to GRUB"])
        self.push_screen(dlg)
        ok = await s.restore_original(dlg.set_step)
        dlg.finish()
        self.query_one(BootMenuScreen).refresh_view()
        self.refresh_state()
        self.query_one(OverviewScreen).refresh_view()
        self.notify("Saved. Rebuild (F9) to see the original order in the menu." if ok else
                    "Not finished; the window shows why.", severity="information" if ok else "error", timeout=8)

    def before_quit(self) -> bool:
        s = self.session
        if s.pending or s.boot_changed:
            n = s.change_count()
            self.push_screen(QuitDialog(
                f"{n} change{'s are' if n != 1 else ' is'} not saved",
                ["Quitting now loses them."],
                [("Save First", "save", True), ("Quit Without Saving", "quit", False)]), self._after_quit_choice)
            return False
        if s.not_rebuilt and not s.read_only:
            self.push_screen(QuitDialog(
                "Saved changes are not in the boot menu yet",
                ["The computer will start with the old menu until you rebuild it."],
                [("Rebuild and Quit", "rebuild", True), ("Quit Anyway", "quit", False)]), self._after_quit_choice)
            return False
        return True

    def _after_quit_choice(self, choice: str | None) -> None:
        if choice == "quit":
            self.exit()
        elif choice == "save":
            self.action_save()
        elif choice == "rebuild":
            self._rebuild_then_quit()

    @work(exclusive=True, group="gf-write")
    async def _rebuild_then_quit(self) -> None:
        s = self.session
        dlg = ProgressDialog("Rebuilding the boot menu", [f"Rebuild the boot menu ({s.env.mkconfig})"])
        self.push_screen(dlg)
        ok = await s.rebuild(dlg.set_step, dlg.add_line)
        dlg.finish()
        if ok:
            self.exit()
        else:
            self.refresh_state()
