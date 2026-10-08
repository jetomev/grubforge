"""Themes — pick a theme and see roughly how your menu will look (v2.0.0).

The preview draws your real entries in the theme's colours. "Use This Theme"
is a change like any other (Save, then Rebuild); it also sets the two things a
theme needs — the menu drawn as graphics, and a resolution — and those show
in the review too. Installing a downloaded theme goes through the helper.
"""

from __future__ import annotations

import base64
import io
import os
import re
import tarfile
import tempfile
from pathlib import Path

from rich.markup import escape
from textual import on, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from forgekit import FilterPicker, ForgeModal, Notice, glyph

from .. import privilege
from ..theme_manager import get_color_palette, list_themes

WHERE_TO_GET = (
    "Themes are folders with a [b]theme.txt[/] inside. Some well-made ones:\n\n"
    "  · Catppuccin  [u]https://github.com/catppuccin/grub[/]\n"
    "  · Vimix, Tela, Stylish, WhiteSur  [u]https://github.com/vinceliuice/grub2-themes[/]\n"
    "  · More on gnome-look  [u]https://www.gnome-look.org/browse?cat=109[/]\n\n"
    "Download one (a folder, or a .tar.gz / .zip of it), then use [b]Install a Theme (i)[/]. "
    "grubForge copies it into place; nothing runs from it.")

COLOUR_KEYS = ("desktop-color", "item_color", "selected_item_color", "message-color", "text_color")


def short_name(name: str) -> str:
    """"catppuccin-frappe-grub-theme" → "catppuccin-frappe": the folder name
    without the words every theme folder repeats."""
    for cut in ("-grub-theme", "-grub2-theme", "-grub", "-theme"):
        if name.lower().endswith(cut) and len(name) > len(cut) + 2:
            return name[: -len(cut)]
    return name


def _colour(theme, *keys: str, fallback: str) -> str:
    for k in keys:
        v = theme.colors.get(k)
        if v and re.fullmatch(r"#[0-9a-fA-F]{6}", v):
            return v
    return fallback


def preview_markup(theme, entries: list[str], timeout: str) -> str:
    """A rough picture of the menu in the theme's colours."""
    bg = _colour(theme, "desktop-color", "bg_color", fallback="#000000")
    item = _colour(theme, "item_color", "text_color", "fg_color", fallback="#cccccc")
    sel = _colour(theme, "selected_item_color", fallback="#ffffff")
    msg = _colour(theme, "message-color", "text_color", fallback=item)
    width = 46
    rows = [f"[on {bg}]{' ' * width}[/]"]
    for n, title in enumerate(entries[:5]):
        t = (" " * 6 + title)[:width - 2].ljust(width - 2)
        if n == 1:
            rows.append(f"[on {bg}] [{bg} on {sel}]{escape(t)}[/] [/]")
        else:
            rows.append(f"[{item} on {bg}] {escape(t)} [/]")
    rows.append(f"[{msg} on {bg}]{escape(('      Starting in ' + timeout).ljust(width))}[/]")
    rows.append(f"[on {bg}]{' ' * width}[/]")
    return "\n".join(rows)


class ThemesScreen(Horizontal, can_focus=False):
    BINDINGS = [Binding("i", "install", show=False)]

    def __init__(self, session, **kw) -> None:
        super().__init__(**kw)
        self.session = session
        self.themes = []

    def compose(self) -> ComposeResult:
        with Vertical(id="th-left"):
            yield Static("[b $forge-title-accent]Themes[/]", classes="gf-group-title")
            lst = OptionList(id="th-list")
            lst.FORGE_HINTS = [("↑↓", "pick"), ("Enter", "use this theme"), ("I", "install"),
                               ("Tab", "buttons"), ("F10", "save"), ("?", "all keys")]
            yield lst
            yield Static("", id="th-where")
        with VerticalScroll(id="th-right", can_focus=False):
            yield Notice(id="th-notice")
            yield Static("", id="th-preview-title")
            yield Static("", id="th-preview")
            yield Static("", id="th-info")
            with Horizontal(classes="forge-buttons gf-box-buttons th-actions", id="th-actions"):
                yield Button("Use This Theme", id="th-use", variant="primary")
                yield Button("Stop Using a Theme", id="th-none")
            with Horizontal(classes="forge-buttons gf-box-buttons th-actions", id="th-more"):
                yield Button("Install a Theme (i)", id="th-install")
                yield Button("Where to Get Themes", id="th-get")

    def on_mount(self) -> None:
        self.refresh_view()

    def current_path(self) -> str:
        return self.session.value("GRUB_THEME") or ""

    def refresh_view(self) -> None:
        env = self.session.env
        self.themes = list_themes(env.themes_dir)
        lst = self.query_one("#th-list", OptionList)
        keep = lst.highlighted
        lst.clear_options()
        cur, saved = self.current_path(), self.session.original.get("GRUB_THEME") or ""
        for t in self.themes:
            path = str(t.theme_txt)
            mark = ""
            if path == cur and cur != saved:
                mark = f"  [$forge-changed]{glyph('changed')} chosen, not saved[/]"
            elif path == saved:
                mark = f"  [$forge-ok]{glyph('on')} in use[/]"
            lst.add_option(Option(f"{escape(short_name(t.name))}{mark}", id=path))
        self.query_one("#th-where", Static).update(
            f"[$forge-muted]{len(self.themes)} theme{'s' if len(self.themes) != 1 else ''} · {env.themes_dir}[/]")
        notice = self.query_one("#th-notice", Notice)
        if not self.themes:
            notice.show("No themes installed yet",
                        ["Download one and use Install a Theme (i), or see Where to Get Themes."], level="info")
        else:
            notice.hide()
        self.query_one("#th-actions").display = True
        if self.themes:
            lst.highlighted = keep if keep is not None and keep < len(self.themes) else 0
            self._show(self.themes[lst.highlighted])
        else:
            for wid in ("#th-preview-title", "#th-preview", "#th-info"):
                self.query_one(wid, Static).update("")

    def _entries(self) -> list[str]:
        b = self.session.boot
        if b is not None:
            return [it.entry.title for it in b.visible()][:5]
        return [self.session.env.distro, f"Advanced options for {self.session.env.distro}", "UEFI Firmware Settings"]

    def _show(self, theme) -> None:
        from ..settings_spec import BY_KEY, display
        timeout = display(BY_KEY["GRUB_TIMEOUT"], self.session.value("GRUB_TIMEOUT"))
        self.query_one("#th-preview-title", Static).update(
            f"[b $forge-title-accent]{escape(theme.name)}[/]\n"
            f"[b $forge-accent]Preview[/] [$forge-muted]· approximate colours, your real entries[/]")
        self.query_one("#th-preview", Static).update(preview_markup(theme, self._entries(), timeout))
        swatches = "  ".join(f"[on {c}]  [/] [$forge-muted]{escape(k.replace('_', ' ').replace('-', ' '))}[/]"
                             for k, c in get_color_palette(theme)[:5] if re.fullmatch(r"#[0-9a-fA-F]{6}", c))
        info = [f"[$forge-muted]{'Colours':<9}[/] {swatches or 'none set'}",
                f"[$forge-muted]{'Picture':<9}[/] {escape(theme.background_file) if theme.has_background else 'none'}",
                f"[$forge-muted]{'Fonts':<9}[/] {escape(', '.join(theme.fonts[:3])) or 'GRUB default'}",
                f"[$forge-muted]{'Folder':<9}[/] {escape(str(theme.path))}"]
        self.query_one("#th-info", Static).update("\n".join(info))

    @on(OptionList.OptionHighlighted, "#th-list")
    def _highlight(self, e: OptionList.OptionHighlighted) -> None:
        self._show(self.themes[e.option_index])

    @on(OptionList.OptionSelected, "#th-list")
    def _selected(self, e: OptionList.OptionSelected) -> None:
        self.use(self.themes[e.option_index])

    def use(self, theme) -> None:
        s = self.session
        if s.read_only:
            self.app.notify(s.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return
        s.set("GRUB_THEME", str(theme.theme_txt))
        also = []
        if s.value("GRUB_TERMINAL_OUTPUT") not in ("gfxterm",):
            s.set("GRUB_TERMINAL_OUTPUT", "gfxterm")
            also.append("the menu drawn as graphics")
        if s.value("GRUB_GFXMODE") is None:
            s.set("GRUB_GFXMODE", "auto")
            also.append("an automatic resolution")
        for k in ("GRUB_THEME", "GRUB_TERMINAL_OUTPUT", "GRUB_GFXMODE"):
            self.app.settings_changed_elsewhere(k)
        self.refresh_view()
        self.app.refresh_state()
        extra = f" It also needs {' and '.join(also)}; those are in your changes too." if also else ""
        self.app.notify(f"{theme.name} chosen. Save (F10), then rebuild (F9).{extra}", timeout=10)

    def action_install(self) -> None:
        if self.session.read_only:
            self.app.notify(self.session.read_only_reason, title="Read-only", severity="warning", timeout=8)
            return
        self.app.push_screen(InstallThemeDialog(self.session), lambda ok: self.refresh_view() if ok else None)

    @on(Button.Pressed)
    def _buttons(self, e: Button.Pressed) -> None:
        bid = e.button.id or ""
        lst = self.query_one("#th-list", OptionList)
        if bid == "th-use" and self.themes and lst.highlighted is not None:
            e.stop()
            self.use(self.themes[lst.highlighted])
        elif bid == "th-none":
            e.stop()
            self.session.set("GRUB_THEME", None)
            self.app.settings_changed_elsewhere("GRUB_THEME")
            self.refresh_view()
            self.app.refresh_state()
        elif bid == "th-install":
            e.stop()
            self.action_install()
        elif bid == "th-get":
            e.stop()
            from ..app import FieldHelp
            self.app.push_screen(FieldHelp("Where to get themes", WHERE_TO_GET))


# ── installing a theme ─────────────────────────────────────────────────────────

def find_theme_root(folder: Path) -> Path | None:
    """The folder holding theme.txt: the folder itself, or the first one inside."""
    if (folder / "theme.txt").is_file():
        return folder
    for p in sorted(folder.rglob("theme.txt")):
        if len(p.relative_to(folder).parts) <= 4:
            return p.parent
    return None


def pack_theme(root: Path) -> bytes:
    """The theme's files as a tar.gz with theme.txt at the top: plain files and
    folders only (links and anything else are left out)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for p in sorted(root.rglob("*")):
            if p.is_symlink() or not (p.is_file() or p.is_dir()):
                continue
            tar.add(p, arcname=str(p.relative_to(root)), recursive=False)
    return buf.getvalue()


def candidates() -> list[str]:
    """Downloaded themes: folders with a theme.txt and archives, in Downloads."""
    out = []
    for base in (Path.home() / "Downloads", Path.home()):
        if not base.is_dir():
            continue
        for p in base.iterdir():
            if p.suffix in (".zip",) or p.name.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar")):
                out.append(str(p))
            elif p.is_dir() and find_theme_root(p):
                out.append(str(p))
    return sorted(set(out))


def unpack_download(path: Path, into: Path) -> Path:
    """Unpack a downloaded archive in your own space (never as root)."""
    if path.suffix == ".zip":
        import zipfile
        with zipfile.ZipFile(path) as z:
            for n in z.namelist():
                if n.startswith("/") or ".." in Path(n).parts:
                    raise ValueError(f"{n}: unsafe path in the archive")
            z.extractall(into)
    else:
        with tarfile.open(path) as t:
            t.extractall(into, filter="data")
    return into


class InstallThemeDialog(ForgeModal[bool]):
    BINDINGS = [Binding("escape", "cancel", "", show=False)]

    def __init__(self, session) -> None:
        super().__init__()
        self.session = session

    def compose(self) -> ComposeResult:
        with Vertical(classes="forge-panel gf-small"):
            yield Static("Install a theme", classes="forge-panel-title")
            yield Static("[$forge-muted]A downloaded theme: its folder, or the .tar.gz / .zip it came in. "
                         "Installing asks for your password.[/]")
            with Horizontal(classes="gf-add-line"):
                yield Static("Theme", classes="gf-add-label")
                yield Input(placeholder="choose, or type a path", id="ti-path")
            with Horizontal(classes="gf-add-line"):
                yield Static("Name", classes="gf-add-label")
                yield Input(placeholder="the folder name under themes/", id="ti-name")
            yield Static("", id="ti-status")
            with Horizontal(classes="forge-buttons forge-panel-footer"):
                yield Button("Choose", id="ti-choose")
                yield Button("Install", id="ti-ok", variant="primary")
                yield Button("Cancel (Esc)", id="ti-cancel")

    def on_mount(self) -> None:
        self.query_one("#ti-choose", Button).focus()

    def _set_path(self, value: str | None) -> None:
        if not value:
            return
        self.query_one("#ti-path", Input).value = value
        name = Path(value).name
        for ext in (".tar.gz", ".tgz", ".tar.xz", ".tar", ".zip"):
            name = name.removesuffix(ext)
        self.query_one("#ti-name", Input).value = re.sub(r"[^A-Za-z0-9._-]", "-", name)[:64].strip("-.") or "theme"

    def on_button_pressed(self, e: Button.Pressed) -> None:
        e.stop()
        if e.button.id == "ti-choose":
            self.app.push_screen(FilterPicker("A downloaded theme", candidates(), allow_custom=True,
                                              hint="Found in Downloads and your home folder, or type a path"),
                                 self._set_path)
        elif e.button.id == "ti-ok":
            self.install()
        else:
            self.dismiss(False)

    @work
    async def install(self) -> None:
        status = self.query_one("#ti-status", Static)
        path = Path(os.path.expanduser(self.query_one("#ti-path", Input).value.strip()))
        name = self.query_one("#ti-name", Input).value.strip()
        if not path.exists():
            status.update("[$forge-danger]That path doesn't exist.[/]")
            return
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", name):
            status.update("[$forge-danger]The name may only use letters, digits, '.', '_' and '-'.[/]")
            return
        try:
            with tempfile.TemporaryDirectory() as tmp:
                folder = path if path.is_dir() else unpack_download(path, Path(tmp))
                root = find_theme_root(folder)
                if root is None:
                    status.update("[$forge-danger]No theme.txt inside: this isn't a GRUB theme.[/]")
                    return
                payload = base64.b64encode(pack_theme(root)).decode()
        except Exception as exc:
            status.update(f"[$forge-danger]Couldn't read it: {escape(str(exc))}[/]")
            return
        status.update(f"[$forge-warn]{glyph('pointer')}[/] Installing{glyph('ellipsis')}")
        r = await privilege.run_async("theme-install", argument=name, content=payload,
                                      capability=self.session.capability)
        if not r.ok:
            status.update(f"[$forge-danger]{escape(r.message)}[/]")
            return
        self.app.notify(f"{name} installed. Pick it and choose Use This Theme.", title="Theme installed", timeout=8)
        self.dismiss(True)

    def action_cancel(self) -> None:
        self.dismiss(False)
