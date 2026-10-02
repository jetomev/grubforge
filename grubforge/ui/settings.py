"""Settings — every GRUB setting as a form with visible controls (v2.0.0).

Groups on the left (Start-up, Look, Kernel options, Other systems, Advanced),
the group's settings on the right, and an "About this setting" panel that
follows the focus. Known values are picked, not typed. A change is marked
"● changed" with the old value under it, and counted in the changes bar;
nothing is written until Save.
"""

from __future__ import annotations

import glob
from pathlib import Path

from rich.markup import escape
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import ContentSwitcher, Input, OptionList, Select, Static
from textual.widgets.option_list import Option

from forgekit import Choices, FilterPicker, Notice, NumberPresets, SettingRow, Toggle

from ..boot_entries_manager import GrubCfgUnreadable, parse_boot_entries
from ..settings_spec import (
    BY_KEY, COMMON_RESOLUTIONS, GROUPS, SETTINGS, Setting, display, switch_is_on, switch_value,
)
from ..theme_manager import list_themes
from ..system import system_name
from .controls import ColourPair, KernelOptions, default_colours

UNSET = "__unset__"
OTHER = "__other__"
SELECT_HINTS = [("Enter", "open list"), ("type", "jump to a match"), ("Tab", "next"), ("F1", "help")]
TIMEOUT_PRESETS = [("0", 0), ("3", 3), ("5", 5), ("10", 10), ("30", 30), ("forever", -1)]


def screen_resolutions() -> list[str]:
    """The connected screens' preferred sizes, read from the kernel."""
    out = []
    for status in glob.glob("/sys/class/drm/card*-*/status"):
        try:
            if Path(status).read_text().strip() != "connected":
                continue
            modes = (Path(status).parent / "modes").read_text().split()
        except OSError:
            continue
        if modes and modes[0] not in out:
            out.append(modes[0])
    return out


def background_pictures() -> list[str]:
    found = []
    for pattern in ("/boot/grub/*.png", "/boot/grub/*.jpg", "/boot/grub/*.tga", "/boot/grub2/*.png",
                    "/usr/share/backgrounds/**/*.png", "/usr/share/backgrounds/**/*.jpg",
                    "/usr/share/wallpapers/**/*.png", "/usr/share/wallpapers/**/*.jpg"):
        found += glob.glob(pattern, recursive=True)
        if len(found) > 300:
            break
    return sorted(set(found))[:300]


class SettingsScreen(Horizontal):
    FORGE_HINTS = [("Tab", "next"), ("↑↓", "groups"), ("F10", "save"), ("F9", "rebuild"), ("F1", "help"), ("?", "all keys")]

    def __init__(self, session, **kw) -> None:
        super().__init__(**kw)
        self.session = session
        self.rows: dict[str, SettingRow] = {}
        self._choices: dict[str, list] = {}

    # ── choices that come from this computer ──────────────────────────────────
    def choices_for(self, key: str) -> list:
        """(value, label) for a list setting; the current value is always one of them."""
        if key in self._choices:
            return self._choices[key]
        s, raw = BY_KEY[key], self.session.original.get(key)
        opts: list[tuple[str, str]] = []
        if key == "GRUB_DEFAULT":
            opts = [("0", "The first entry in the menu"), ("saved", "Last chosen (remembers your pick)")]
            try:
                for e in parse_boot_entries(self.session.env.grub_cfg):
                    if e.entry_type == "submenu":
                        for child in e.children:
                            opts.append((f"{e.title}>{child}", f"{e.title} ▸ {child}"))
                    else:
                        opts.append((e.title, e.title))
            except (GrubCfgUnreadable, OSError):
                pass
        elif key == "GRUB_THEME":
            opts = [(UNSET, "None")] + [(str(t.path / "theme.txt"), t.name) for t in list_themes(self.session.env.themes_dir)]
        elif key == "GRUB_GFXMODE":
            sizes = screen_resolutions()
            opts = [("auto", "Automatic")]
            opts += [(r, f"{r}  (this screen)") for r in sizes]
            opts += [(r, r) for r in COMMON_RESOLUTIONS if r not in sizes]
            opts.append((OTHER, "Other…"))
        elif key == "GRUB_GFXPAYLOAD_LINUX":
            opts = [(UNSET, "GRUB decides")] + list(s.choices) + [(r, r) for r in COMMON_RESOLUTIONS[:4]]
        elif key == "GRUB_BACKGROUND":
            opts = [(UNSET, "None"), (OTHER, "Choose a picture…")]
        elif s.choices:
            opts = [(UNSET, f"Automatic ({s.default})")] + list(s.choices)
        if raw is not None and all(v != raw for v, _l in opts):
            opts.insert(0 if key != "GRUB_DEFAULT" else 2, (raw, f"{raw}  (current)"))
        self._choices[key] = opts
        return opts

    # ── building the form ─────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        groups = OptionList(*(Option(label, id=gid) for gid, label, _d in GROUPS), id="gf-groups")
        groups.FORGE_HINTS = [("↑↓", "choose a group"), ("Tab", "its settings"), ("F10", "save"), ("?", "all keys")]
        yield groups
        with Vertical(id="gf-settings-right"):
            if self.session.read_only:
                yield Notice("Read-only: nothing can be changed here",
                             [escape(self.session.read_only_reason)], level="warn", id="gf-readonly")
            with ContentSwitcher(initial=f"grp-{GROUPS[0][0]}", id="gf-groupforms"):
                for gid, label, desc in GROUPS:
                    with VerticalScroll(id=f"grp-{gid}", classes="gf-group", can_focus=False):
                        yield Static(f"[b $forge-title-accent]{label}[/]   [$forge-muted]{escape(desc)}[/]",
                                     classes="gf-group-title")
                        for s in SETTINGS:
                            if s.group == gid:
                                row = self._row(s)
                                self.rows[s.key] = row
                                yield row
            yield Static("", id="gf-about")

    def _row(self, s: Setting) -> SettingRow:
        raw = self.session.value(s.key)
        disabled = self.session.read_only
        if s.control == "list":
            opts = self.choices_for(s.key)
            value = UNSET if raw is None else raw
            if all(v != value for v, _l in opts):
                value = opts[0][0]
            ctrl = Select([(l, v) for v, l in opts], value=value, allow_blank=False, disabled=disabled)
            ctrl.FORGE_HINTS = SELECT_HINTS
        elif s.control == "file":
            opts = self.choices_for(s.key)
            if raw:
                opts = [(raw, Path(raw).name + "  (current)")] + [o for o in opts if o[0] != raw]
                self._choices[s.key] = opts
            ctrl = Select([(l, v) for v, l in opts], value=raw or UNSET, allow_blank=False, disabled=disabled)
            ctrl.FORGE_HINTS = SELECT_HINTS
        elif s.control == "switch":
            ctrl = Toggle(switch_is_on(s, raw), disabled=disabled)
        elif s.control == "number":
            try:
                n = int(raw) if raw is not None else 5
            except ValueError:
                n = 5
            ctrl = NumberPresets(n, TIMEOUT_PRESETS, unit="seconds", minimum=-1, disabled=disabled)
        elif s.control == "choices":
            ctrl = Choices(s.choices, raw if raw in {v for v, _l in s.choices} else "menu", disabled=disabled)
        elif s.control == "kernel":
            ctrl = KernelOptions(raw, disabled=disabled)
        elif s.control == "colours":
            ctrl = ColourPair(raw, default=default_colours(s.key), disabled=disabled)
        else:  # text
            ctrl = Input(raw or "", placeholder=system_name(), disabled=disabled)
            ctrl.FORGE_HINTS = [("type", "a name"), ("Tab", "next"), ("F1", "help")]
        ctrl.setting_key = s.key
        return SettingRow(s.label, ctrl, note=s.note, help=s.help, setting=s.key, id=f"row-{s.key}",
                          stacked=s.control == "kernel")

    def on_mount(self) -> None:
        self.query_one("#gf-groups", OptionList).highlighted = 0
        for key in self.session.pending:
            self._mark(key)
        self._cursors_home()

    def _cursors_home(self) -> None:
        # a field not being typed in shows its text from the first letter: with
        # the cursor parked after the last one, a value as long as the field
        # scrolled out of sight and the field looked empty
        for inp in self.query(Input):
            if not inp.has_focus:
                inp.cursor_position = 0

    # ── moving around ─────────────────────────────────────────────────────────
    @on(OptionList.OptionHighlighted, "#gf-groups")
    def _group(self, e: OptionList.OptionHighlighted) -> None:
        self.query_one("#gf-groupforms", ContentSwitcher).current = f"grp-{e.option.id}"

    def show_group(self, gid: str) -> None:
        ids = [g for g, _l, _d in GROUPS]
        self.query_one("#gf-groups", OptionList).highlighted = ids.index(gid)

    def on_descendant_focus(self, e) -> None:
        row = next((a for a in e.widget.ancestors_with_self if isinstance(a, SettingRow)), None)
        about = self.query_one("#gf-about", Static)
        if row is None:
            about.update("")
            return
        s = BY_KEY[row.setting]
        about.update(
            f"[$forge-muted]{'─' * 3} About this setting {'─' * 40}[/]\n"
            f"{escape(s.help)}\n"
            f"[$forge-muted]GRUB name: {s.key}  ·  when not set: {escape(s.default)}  ·  F1 opens the manual[/]")

    # ── changes ───────────────────────────────────────────────────────────────
    def _stage(self, key: str, value) -> None:
        self.session.set(key, value)
        self._mark(key)
        self.app.refresh_state()

    def _mark(self, key: str) -> None:
        row = self.rows.get(key)
        if row is None:
            return
        if key in self.session.pending:
            row.mark_changed(display(BY_KEY[key], self.session.original.get(key), self.choices_for(key)
                                     if BY_KEY[key].control in ("list", "file") else None))
        else:
            row.mark_unchanged()

    @on(Select.Changed)
    def _select(self, e: Select.Changed) -> None:
        key = getattr(e.select, "setting_key", None)
        if key is None:
            return
        e.stop()
        if e.value == OTHER:
            self._other(key, e.select)
            return
        self._stage(key, None if e.value == UNSET else e.value)

    def _other(self, key: str, select: Select) -> None:
        s = BY_KEY[key]
        if key == "GRUB_BACKGROUND":
            options, hint = background_pictures(), "Pictures found on this computer, or type a full path"
        else:
            options, hint = COMMON_RESOLUTIONS, "Type a size like 1600x900, or several: 1920x1080,auto"

        def done(value: str | None) -> None:
            if not value:
                prev = self.session.value(key)
                with select.prevent(Select.Changed):
                    select.value = UNSET if prev is None else prev
                return
            opts = self.choices_for(key)
            if all(v != value for v, _l in opts):
                label = Path(value).name if key == "GRUB_BACKGROUND" else value
                opts.insert(1, (value, label))
                select.set_options([(l, v) for v, l in opts])
            with select.prevent(Select.Changed):
                select.value = value
            self._stage(key, value)

        self.app.push_screen(FilterPicker(s.label, options, current=self.session.value(key) or "",
                                          allow_custom=True, hint=hint), done)

    @on(Toggle.Changed)
    def _toggle(self, e: Toggle.Changed) -> None:
        key = getattr(e.toggle, "setting_key", None)
        if key:
            e.stop()
            self._stage(key, switch_value(BY_KEY[key], e.value))

    @on(NumberPresets.Changed)
    def _number(self, e: NumberPresets.Changed) -> None:
        key = getattr(e.number, "setting_key", None)
        if key:
            e.stop()
            self._stage(key, str(e.value))

    @on(Choices.Changed)
    def _choices(self, e: Choices.Changed) -> None:
        key = getattr(e.choices, "setting_key", None)
        if key:
            e.stop()
            self._stage(key, e.value)

    @on(KernelOptions.Changed)
    def _kernel(self, e: KernelOptions.Changed) -> None:
        key = getattr(e.kernel, "setting_key", None)
        if key and not e.problem:
            e.stop()
            # the same options in another order are no change: keep the file's text
            orig = self.session.original.get(key)
            if sorted((orig or "").split()) == sorted(e.value.split()):
                self._stage(key, orig)
            else:
                self._stage(key, e.value)

    @on(ColourPair.Changed)
    def _colours(self, e: ColourPair.Changed) -> None:
        key = getattr(e.pair, "setting_key", None)
        if key:
            e.stop()
            # GRUB's own colours, chosen while the line is absent, stay "not set"
            if self.session.original.get(key) is None and e.value == default_colours(key):
                self._stage(key, None)
            else:
                self._stage(key, e.value)

    @on(Input.Changed)
    def _text(self, e: Input.Changed) -> None:
        key = getattr(e.input, "setting_key", None)
        if key:
            e.stop()
            self._stage(key, e.value)

    # ── after save / discard / reload ─────────────────────────────────────────
    def sync(self) -> None:
        """Put every control back to the session's values and marks."""
        self._choices.clear()
        for key, row in self.rows.items():
            s, raw, ctrl = BY_KEY[key], self.session.value(key), row.control
            if isinstance(ctrl, Select):
                opts = self.choices_for(key)
                value = UNSET if raw is None else raw
                if all(v != value for v, _l in opts):
                    opts.insert(0, (value, value))
                with ctrl.prevent(Select.Changed):
                    ctrl.set_options([(l, v) for v, l in opts])
                    ctrl.value = value
            elif isinstance(ctrl, Toggle):
                ctrl.set_value(switch_is_on(s, raw), announce=False)
            elif isinstance(ctrl, NumberPresets):
                try:
                    ctrl.set_value(int(raw) if raw is not None else 5, announce=False)
                except ValueError:
                    pass
            elif isinstance(ctrl, Choices):
                ctrl.set_value(raw if raw in {v for v, _l in s.choices} else "menu", announce=False)
            elif isinstance(ctrl, (KernelOptions, ColourPair)):
                ctrl.set_raw(raw)
            elif isinstance(ctrl, Input):
                with ctrl.prevent(Input.Changed):
                    ctrl.value = raw or ""
            self._mark(key)
        self._cursors_home()
