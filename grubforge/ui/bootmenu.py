"""Boot menu — the entries shown when the computer starts (v2.0.0).

The list is the screen; actions are buttons underneath, and the bigger jobs
(adding an entry, finding other systems) open their own windows. Changes are a
draft, counted in the changes bar and saved with the same review as settings.
Entries made by other tools are fixed in place (#20).
"""

from __future__ import annotations

from rich.markup import escape
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, DataTable, Input, Select, Static, TextArea

from forgekit import ConfirmDialog, ForgeModal, Notice, glyph

from .. import probe
from ..boot_entries_manager import BootEntry
from ..bootorder import Item

SOURCE_WORDS = {
    "10_linux": None, "20_linux_xen": "Xen", "30_os-prober": "Other systems",
    "30_uefi-firmware": "UEFI", "40_custom": "Added by you", "41_snapshots-btrfs": "Snapshot tool",
}


def rich_colours(markup: str, app) -> str:
    """DataTable cells use Rich markup, which doesn't know forgekit's
    ``$forge-*`` roles: put the real colour (window or console) in their place."""
    import re
    vars_ = app.get_css_variables()

    def one(m):
        v = vars_.get(m.group(1), "default")
        return v.removeprefix("ansi_") if v.startswith("ansi_") else v
    return re.sub(r"\$(forge-[a-z-]+)", one, markup)


def source_label(item: Item, system: str) -> str:
    src = item.entry.source
    if item.original_index is None:
        return "Added by you"
    word = SOURCE_WORDS.get(src, src)
    if word is None:
        word = system
    if item.entry.source_guessed:
        word += " (guessed)"
    return word


class BootMenuScreen(Vertical, can_focus=False):
    BINDINGS = [
        Binding("shift+up", "move(-1)", show=False), Binding("shift+down", "move(1)", show=False),
        Binding("f2", "rename", show=False), Binding("plus", "add", show=False),
        Binding("f", "others", show=False),
    ]

    def __init__(self, session, **kw) -> None:
        super().__init__(**kw)
        self.session = session
        self._rows: list[Item] = []

    def compose(self) -> ComposeResult:
        yield Static("[b $forge-title-accent]Boot menu[/]   [$forge-muted]the entries shown when the computer "
                     "starts, top to bottom[/]", classes="gf-group-title")
        yield Notice(id="bm-notice")
        with Horizontal(id="bm-stale", classes="forge-buttons gf-box-buttons"):
            yield Button("Drop the old copy", id="bm-drop", variant="primary")
        with Horizontal(id="bm-read", classes="forge-buttons gf-box-buttons"):
            yield Button("Read the boot menu (asks for your password)", id="bm-read-btn", variant="primary")
        table = DataTable(id="bm-table", cursor_type="row", zebra_stripes=False)
        table.FORGE_HINTS = [("↑↓", "pick"), ("Shift+↑↓", "move"), ("F2", "rename"), ("+", "add"),
                             ("Tab", "buttons"), ("F10", "save"), ("?", "all keys")]
        yield table
        with Horizontal(classes="forge-buttons gf-box-buttons", id="bm-actions"):
            yield Button("Move up  Shift+↑", id="bm-up")
            yield Button("Move down  Shift+↓", id="bm-down")
            yield Button("Rename  F2", id="bm-rename")
            yield Button("Start this first", id="bm-default")
            yield Button(f"Remove{glyph('ellipsis')}", id="bm-remove")
        with Horizontal(classes="forge-buttons gf-box-buttons", id="bm-more"):
            yield Button(f"Add an entry{glyph('ellipsis')}  +", id="bm-add")
            yield Button(f"Find other systems{glyph('ellipsis')}  F", id="bm-others")
            yield Button(f"Back to the original order{glyph('ellipsis')}", id="bm-restore")

    def on_mount(self) -> None:
        t = self.query_one("#bm-table", DataTable)
        t.add_columns("#", "Entry", "Comes from", "Notes")
        self.refresh_view()

    # ── drawing ──────────────────────────────────────────────────────────────
    def refresh_view(self, keep: Item | None = None) -> None:
        s = self.session
        notice = self.query_one("#bm-notice", Notice)
        read = self.query_one("#bm-read")
        table = self.query_one("#bm-table", DataTable)
        actions_ok = s.boot is not None and not s.read_only and not s.env.bls
        for bid in ("bm-actions", "bm-more"):
            self.query_one(f"#{bid}").display = actions_ok
        read.display = s.boot_unreadable and not s.read_only
        if s.env.bls:
            notice.show("This system keeps its entries as separate files", [
                "Fedora-style systems order their entries by version, and grubForge 2.0 shows them as they are.",
                "To choose which one starts, use Settings ▸ Start-up ▸ Start this entry."], level="info")
            self._fill_bls(table)
            return
        if s.boot_unreadable:
            notice.show("The boot menu is readable only by an administrator", [
                "This computer protects grub.cfg. grubForge can read it through its helper,",
                "which asks for your password once."], level="info")
            table.clear()
            return
        stale = s.boot.stale_copies if s.boot else []
        self.query_one("#bm-stale").display = bool(stale) and not s.boot.drop_stale and not s.read_only
        if stale:
            names = ", ".join(sorted({f'"{it.entry.title}"' for it in stale}))
            notice.show("An old copy is stuck in your saved order", [
                f"{escape(names)} appears twice: once from its own tool, once copied into your order by an",
                "older grubForge (#20). Drop it and save; the live entry stays."
                if not s.boot.drop_stale else "older grubForge (#20). It will be dropped when you save."], level="warn")
        elif self.session.custom_order_in_use:
            notice.show("Your own order is in use", [
                "GRUB stops adding new kernels by itself while it is. A kernel update won't show here",
                "until you go back to the original order. F1 explains why."], level="warn")
        else:
            notice.hide()
        self._fill(table, keep)

    def _fill(self, table: DataTable, keep: Item | None) -> None:
        table.clear()
        s = self.session
        if s.boot is None:
            return
        self._rows = s.boot.visible()
        default = s.value("GRUB_DEFAULT")
        orig_pos = {it.original_index: n for n, it in enumerate(
            [x for x in s.boot.__class__.from_entries(s.boot.original).items if x.movable])}
        mine = [it for it in self._rows if it.movable]
        for n, it in enumerate(self._rows, 1):
            notes = []
            e = it.entry
            if (default == "0" and n == 1) or default == e.title:
                notes.append(f"[$forge-ok]{glyph('default')} starts first[/]")
            if it.original_index is None:
                notes.append(f"[$forge-changed]{glyph('changed')} new[/]")
            elif it.movable and it in mine and orig_pos.get(it.original_index) is not None \
                    and orig_pos[it.original_index] != mine.index(it):
                notes.append(f"[$forge-changed]{glyph('changed')} moved[/]")
            if it.renamed:
                notes.append(f"[$forge-changed]{glyph('changed')} renamed[/]")
            if it.stale_copy:
                notes.append(f"[$forge-changed]{glyph('changed')} old copy · dropped when you save[/]"
                             if s.boot.changed else f"[$forge-warn]{glyph('warn')} old copy (#20)[/]")
            elif not it.movable:
                notes.append(f"[$forge-muted]{glyph('fixed')} fixed · its tool places it[/]")
            title = escape(e.title) + (" ▸" if e.entry_type == "submenu" else "")
            table.add_row(str(n), title, escape(source_label(it, s.env.distro)),
                          rich_colours("  ".join(notes), self.app))
        if keep in self._rows:
            table.move_cursor(row=self._rows.index(keep))

    def _fill_bls(self, table: DataTable) -> None:
        table.clear()
        for n, (eid, title, version) in enumerate(probe.bls_entries(), 1):
            table.add_row(str(n), escape(title), "Entry file",
                          rich_colours(f"[$forge-muted]{escape(version)}[/]", self.app))

    def current(self) -> Item | None:
        t = self.query_one("#bm-table", DataTable)
        if not self._rows or t.cursor_row is None or t.cursor_row >= len(self._rows):
            return None
        return self._rows[t.cursor_row]

    def _changed(self, keep: Item | None = None) -> None:
        self.refresh_view(keep)
        self.app.refresh_state()

    def _can_edit(self) -> bool:
        s = self.session
        if s.read_only:
            self.app.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return False
        return s.boot is not None and not s.env.bls

    # ── actions ──────────────────────────────────────────────────────────────
    def action_move(self, step: int) -> None:
        it = self.current()
        if not self._can_edit() or it is None:
            return
        if not it.movable:
            self.app.notify("This entry is fixed: the tool that makes it decides where it goes.", timeout=6)
            return
        if self.session.boot.move(it, step):
            self._changed(keep=it)

    def action_rename(self) -> None:
        it = self.current()
        if not self._can_edit() or it is None:
            return
        if not it.movable:
            self.app.notify("This entry is fixed; its tool names it.", timeout=6)
            return

        def done(title: str | None) -> None:
            if title and title != it.entry.title:
                self.session.boot.rename(it, title)
                self._changed(keep=it)
        self.app.push_screen(RenameDialog(it.entry.title), done)

    def action_add(self) -> None:
        if not self._can_edit():
            return

        def done(entry: BootEntry | None) -> None:
            if entry:
                it = self.session.boot.add(entry)
                self._changed(keep=it)
        self.app.push_screen(AddEntryDialog(), done)

    def action_others(self) -> None:
        self.app.push_screen(OtherSystemsDialog(self.session))

    @work
    async def remove(self) -> None:
        it = self.current()
        if not self._can_edit() or it is None:
            return
        if not it.movable:
            self.app.notify("This entry is fixed; remove it with the tool that makes it.", timeout=6)
            return
        msg = (f"Remove \"{it.entry.title}\" from your boot menu?\n\nNothing is deleted from the disk. "
               "Going back to the original order brings it back.")
        if await self.app.push_screen_wait(ConfirmDialog(msg, "Remove", danger=True)):
            self.session.boot.remove(it)
            self._changed()

    def drop_stale(self) -> None:
        if not self._can_edit():
            return
        self.session.boot.drop_stale = True
        self._changed()

    def start_first(self) -> None:
        it = self.current()
        if not self._can_edit() or it is None:
            return
        if it.entry.entry_type == "submenu":
            self.app.notify("Pick an entry inside the submenu in Settings ▸ Start this entry.", timeout=6)
            return
        self.session.set("GRUB_DEFAULT", it.entry.title)
        self.app.settings_changed_elsewhere("GRUB_DEFAULT")
        self._changed(keep=it)

    @work
    async def restore(self) -> None:
        if not self._can_edit():
            return
        msg = ("Go back to the original order?\n\nGRUB makes the menu by itself again: new kernels "
               "appear on their own. Your own order, names and added entries are dropped. A backup is not "
               "needed: nothing else changes.")
        if not await self.app.push_screen_wait(ConfirmDialog(msg, "Go back")):
            return
        await self.app.run_restore_original()

    @work
    async def read_privileged(self) -> None:
        r = await self.session.load_boot_privileged()
        if not r.ok:
            self.app.notify(r.message, title="Not read", severity="error", timeout=8)
        self.refresh_view()

    @on(Button.Pressed)
    def _buttons(self, e: Button.Pressed) -> None:
        handlers = {"bm-up": lambda: self.action_move(-1), "bm-down": lambda: self.action_move(1),
                    "bm-rename": self.action_rename, "bm-default": self.start_first,
                    "bm-remove": self.remove, "bm-add": self.action_add, "bm-others": self.action_others,
                    "bm-restore": self.restore, "bm-read-btn": self.read_privileged,
                    "bm-drop": self.drop_stale}
        h = handlers.get(e.button.id or "")
        if h:
            e.stop()
            h()


class RenameDialog(ForgeModal[str | None]):
    BINDINGS = [Binding("escape", "cancel", "", show=False)]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(classes="forge-panel gf-small"):
            yield Static("Rename this entry", classes="forge-panel-title")
            yield Static("[$forge-muted]The name shown in the boot menu. Only the name changes.[/]")
            yield Input(self._title, id="rn-input")
            yield Static("", id="rn-problem")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                yield Button("Rename", id="rn-ok", variant="primary")
                yield Button("Cancel", id="rn-cancel")

    def on_mount(self) -> None:
        self.query_one("#rn-input", Input).focus()

    def _ok(self) -> None:
        v = self.query_one("#rn-input", Input).value.strip()
        if not v:
            self.query_one("#rn-problem", Static).update("[$forge-danger]A name can't be empty.[/]")
            return
        self.dismiss(v)

    def on_input_submitted(self, e: Input.Submitted) -> None:
        self._ok()

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        self._ok() if e.button.id == "rn-ok" else self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


KINDS = [("linux", "Another Linux kernel on this computer"), ("other", "Another operating system (EFI)"),
         ("memtest", "Memory test"), ("firmware", "Firmware (UEFI) settings"),
         ("empty", "An empty entry I write myself")]


class AddEntryDialog(ForgeModal[BootEntry | None]):
    """Choices first, text only for the name; the entry GRUB will read, shown
    and checked before it is added."""

    BINDINGS = [Binding("escape", "cancel", "", show=False)]

    def compose(self) -> ComposeResult:
        self._kernels, self._images = probe.kernels(), probe.images()
        self._loaders = probe.esp_loaders()
        with Vertical(classes="forge-panel gf-add"):
            yield Static("Add a boot entry", classes="forge-panel-title")
            with VerticalScroll(classes="forge-panel-body"):
                yield self._line("What kind", Select([(l, v) for v, l in KINDS], value="linux", allow_blank=False, id="ae-kind"))
                yield self._line("Name in the menu", Input(placeholder="the name shown in the boot menu", id="ae-title"))
                yield self._line("Kernel", Select([(k, k) for k in self._kernels] or [("none found", "")],
                                                  value=(self._kernels[-1] if self._kernels else ""), allow_blank=False, id="ae-kernel"), "ae-l-kernel")
                yield self._line("Start-up image", Select([(i, i) for i in self._images] + [("none", "")],
                                                          value=probe.image_for(self._kernels[-1], self._images) if self._kernels else "",
                                                          allow_blank=False, id="ae-image"), "ae-l-image")
                yield self._line("Kernel options", Input("quiet", id="ae-options"), "ae-l-options")
                loader_opts = [(f"{l}", f"{u}|{l}") for u, l in self._loaders] or [("no other system's loader found", "")]
                yield self._line("System to start", Select(loader_opts, value=loader_opts[0][1], allow_blank=False, id="ae-loader"), "ae-l-loader")
                yield Static("", id="ae-why")
                yield Static("[$forge-muted]─ What GRUB will read ─────────────────────────────────────[/]", classes="gf-add-sep")
                yield TextArea("", id="ae-block", read_only=True, soft_wrap=True)
                yield Static("", id="ae-problem")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                yield Button("Edit by hand", id="ae-hand")
                yield Button("Add entry", id="ae-ok", variant="primary")
                yield Button("Cancel", id="ae-cancel")

    def _line(self, label: str, control, line_id: str | None = None) -> Horizontal:
        return Horizontal(Static(label, classes="gf-add-label"), control, classes="gf-add-line", id=line_id)

    def on_mount(self) -> None:
        self.query_one("#ae-kind", Select).focus()
        self._kind_changed()

    def _kind(self) -> str:
        return self.query_one("#ae-kind", Select).value

    def _kind_changed(self) -> None:
        k = self._kind()
        for line, kinds in (("ae-l-kernel", {"linux"}), ("ae-l-image", {"linux"}), ("ae-l-options", {"linux"}),
                            ("ae-l-loader", {"other"})):
            self.query_one(f"#{line}").display = k in kinds
        title = self.query_one("#ae-title", Input)
        defaults = {"memtest": "Memory test", "firmware": "UEFI Firmware Settings"}
        if not title.value and k in defaults:
            title.value = defaults[k]
        why = ""
        if k == "memtest" and not probe.memtest_path():
            why = "memtest86+ isn't installed. Install it first (KognogOS: nog install memtest86+-efi)."
        if k == "firmware" and not probe.is_efi():
            why = "This computer didn't start in UEFI mode, so there are no firmware settings to open."
        if k == "other" and not self._loaders:
            why = ("No other system's loader is visible. To find Windows and others on other disks, "
                   "use Find other systems instead.")
        self.query_one("#ae-why", Static).update(f"[$forge-warn]{escape(why)}[/]" if why else "")
        area = self.query_one("#ae-block", TextArea)
        area.read_only = k != "empty"
        self._rebuild()

    def _rebuild(self) -> None:
        k = self._kind()
        title = self.query_one("#ae-title", Input).value.strip() or "New entry"
        if k == "linux":
            kernel = self.query_one("#ae-kernel", Select).value
            image = self.query_one("#ae-image", Select).value
            block = probe.linux_entry(title, kernel, image, self.query_one("#ae-options", Input).value.strip()) if kernel else ""
        elif k == "other":
            v = self.query_one("#ae-loader", Select).value
            block = probe.chainload_entry(title, *v.split("|", 1)) if v else ""
        elif k == "memtest":
            p = probe.memtest_path()
            block = probe.memtest_entry(title, p) if p else ""
        elif k == "firmware":
            block = probe.firmware_entry(title)
        else:
            area = self.query_one("#ae-block", TextArea)
            if area.text.strip():
                return
            block = probe.empty_entry(title)
        self.query_one("#ae-block", TextArea).text = block
        self.query_one("#ae-problem", Static).update("")

    @on(Select.Changed)
    def _select(self, e: Select.Changed) -> None:
        if e.select.id == "ae-kind":
            self._kind_changed()
            return
        if e.select.id == "ae-kernel" and e.value:
            img = probe.image_for(e.value, self._images)
            s = self.query_one("#ae-image", Select)
            with s.prevent(Select.Changed):
                s.value = img
        self._rebuild()

    @on(Input.Changed)
    def _typed(self, e: Input.Changed) -> None:
        if self._kind() != "empty" or e.input.id != "ae-title":
            self._rebuild()

    def _ok(self) -> None:
        title = self.query_one("#ae-title", Input).value.strip()
        block = self.query_one("#ae-block", TextArea).text.strip()
        problem = ("Give the entry a name." if not title else
                   "There is nothing to add for this kind of entry." if not block else probe.check_entry(block))
        if problem:
            self.query_one("#ae-problem", Static).update(f"[$forge-danger]{escape(problem)}[/]")
            return
        self.dismiss(BootEntry(title=title, entry_type="menuentry", source="40_custom", raw_block=block))

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        if e.button.id == "ae-ok":
            self._ok()
        elif e.button.id == "ae-hand":
            area = self.query_one("#ae-block", TextArea)
            area.read_only = False
            area.focus()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)


class OtherSystemsDialog(ForgeModal[None]):
    """Windows and other systems: is the search on, is the tool installed,
    and what it finds."""

    BINDINGS = [Binding("escape", "close", "", show=False)]

    def __init__(self, session) -> None:
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        from ..settings_spec import BY_KEY, switch_is_on
        s = self.session
        on = switch_is_on(BY_KEY["GRUB_DISABLE_OS_PROBER"], s.value("GRUB_DISABLE_OS_PROBER"))
        installed = probe.shutil.which("os-prober") is not None
        lines = [
            f"{glyph('ok') if installed else glyph('error')} os-prober is {'installed' if installed else 'not installed'}"
            + ("" if installed else f"   [$forge-muted]{escape(probe.os_prober_install_hint(s.env.family))}[/]"),
            f"{glyph('ok') if on else glyph('off')} \"Find other systems\" is {'on' if on else 'off'}"
            + ("" if on else "   [$forge-muted]turning it on is a setting: save, then rebuild[/]"),
        ]
        with Vertical(classes="forge-panel gf-small"):
            yield Static("Find other systems", classes="forge-panel-title")
            yield Static("[$forge-muted]When the search is on, rebuilding the boot menu adds Windows and other "
                         "systems it finds on your disks.[/]")
            yield Static("\n".join(lines), id="os-status")
            yield Static("", id="os-results")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                if not on:
                    yield Button("Turn the search on", id="os-on")
                if installed:
                    yield Button("Search now (asks for your password)", id="os-scan", variant="primary")
                yield Button("Close", id="os-close")

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        if e.button.id == "os-close":
            self.dismiss(None)
        elif e.button.id == "os-on":
            self.session.set("GRUB_DISABLE_OS_PROBER", "false")
            self.app.settings_changed_elsewhere("GRUB_DISABLE_OS_PROBER")
            self.app.refresh_state()
            self.app.notify("Turned on in your settings. Save (F10), then rebuild (F9).", timeout=8)
            self.dismiss(None)
        elif e.button.id == "os-scan":
            self.scan()

    @work
    async def scan(self) -> None:
        from ..boot_entries_manager import parse_os_prober_output, run_os_prober
        box = self.query_one("#os-results", Static)
        box.update(f"[$forge-warn]{glyph('pointer')}[/] Searching the disks{glyph('ellipsis')}")
        result, lines = await run_os_prober(capability=self.session.capability)
        if not result.ok:
            box.update(f"[$forge-danger]{escape(result.message)}[/]")
            return
        found = parse_os_prober_output(lines)
        if not found:
            box.update("Nothing found: no other operating system on these disks.")
            return
        box.update("Found:\n" + "\n".join(f"  {glyph('bullet')} [b]{escape(f['label'])}[/]  "
                                          f"[$forge-muted]{escape(f['device'])}[/]" for f in found)
                   + "\n\n[$forge-muted]They appear in the menu after the next rebuild, while the search is on.[/]")

    def action_close(self) -> None:
        self.dismiss(None)
