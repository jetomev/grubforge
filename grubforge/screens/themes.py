# -*- coding: utf-8 -*-
"""
GrubForge - Theme Browser Screen
Scan, preview, and apply installed GRUB themes.
"""

from textual.app import ComposeResult
from textual.widgets import ListView, ListItem, Static, Button
from textual.containers import Container, Vertical, Horizontal
from textual.binding import Binding
from textual import work

from grubforge.theme_manager import (
    GrubTheme,
    list_themes,
    apply_theme,
    get_color_palette,
    THEMES_DIR,
)
from grubforge.widgets.confirm_dialog import ConfirmDialog


class ThemesScreen(Container):
    """Theme browser - scan, preview, and apply GRUB themes."""

    BINDINGS = [
        Binding("a",  "apply_theme", "Apply Theme", show=True),
        Binding("f5", "refresh",     "Refresh",     show=True),
        Binding("h",  "show_help",   "Help",        show=True),
    ]

    _themes: list = []
    _selected_idx: int = -1
    _showing_help: bool = False

    def compose(self) -> ComposeResult:
        with Container(id="backup-split"):
            # Left: theme list
            with Vertical(id="backup-list-panel"):
                yield Static(
                    " Themes  [dim](A apply  F5 refresh  H help)[/dim]",
                    classes="panel-title",
                )
                yield ListView(id="theme-list")

            # Right: detail + preview + help
            with Vertical(id="backup-detail-panel"):
                yield Static("", id="theme-detail-header")
                with Horizontal(id="backup-action-buttons"):
                    yield Button("Apply Theme", id="btn-apply",   classes="-success")
                    yield Button("Refresh",     id="btn-refresh", classes="-primary")
                    yield Button("? Help",      id="btn-help",    classes="-primary")
                yield Static(" Color Palette", classes="panel-title")
                yield Static("", id="theme-palette")
                yield Static(" theme.txt Preview", classes="panel-title")
                yield Static("", id="theme-preview")
                yield Static("", id="theme-help", classes="hidden-screen")

        yield Static("", id="backup-status")

    def on_mount(self) -> None:
        self._load_themes()

    # Load themes

    def _load_themes(self) -> None:
        self._themes = list_themes()
        lv = self.query_one("#theme-list", ListView)
        lv.clear()

        if not self._themes:
            lv.append(ListItem(Static(
                f"[dim]No themes found in {THEMES_DIR}[/dim]\n"
                f"[dim]Press H for help installing themes.[/dim]"
            )))
            self._selected_idx = -1
            self._clear_detail()
            self._set_status(f"No themes found in {THEMES_DIR} -- press H for help", "warn")
            return

        for theme in self._themes:
            active      = " [green]active[/green]" if theme.is_active else ""
            color_count = len(theme.colors)
            text = (
                f" [#cdd6f4]{theme.name}[/#cdd6f4]{active}\n"
                f"  [dim]{color_count} colors detected[/dim]"
            )
            lv.append(ListItem(Static(text)))

        self._selected_idx = 0
        self._show_detail(0)
        self._set_status(
            f"Found {len(self._themes)} theme(s) in {THEMES_DIR}", "info"
        )

    # List selection

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = event.list_view.index
        if idx is not None and 0 <= idx < len(self._themes):
            self._selected_idx = idx
            self._show_detail(idx)
            self._hide_help()

    # Detail pane

    def _show_detail(self, idx: int) -> None:
        if idx < 0 or idx >= len(self._themes):
            self._clear_detail()
            return

        theme  = self._themes[idx]
        active = " [green]currently active[/green]" if theme.is_active else ""

        header = (
            f"[bold #89b4fa]{theme.name}[/bold #89b4fa]{active}\n"
            f"[dim]Path:[/dim]   [#a6adc8]{theme.path}[/#a6adc8]\n"
            f"[dim]Config:[/dim] [#a6adc8]{theme.theme_txt}[/#a6adc8]\n"
            + (f"[dim]BG:[/dim]    [#a6adc8]{theme.background_file}[/#a6adc8]\n"
               if theme.has_background else "")
            + f"[dim]Fonts:[/dim] [#a6adc8]{', '.join(theme.fonts[:3]) or 'none detected'}[/#a6adc8]\n"
        )
        self.query_one("#theme-detail-header", Static).update(header)

        # Color palette
        palette = get_color_palette(theme)
        if palette:
            lines = []
            for label, hex_color in palette[:10]:
                swatch = self._color_swatch(hex_color)
                lines.append(
                    f"  {swatch}  [dim]{label:30s}[/dim]  [#a6adc8]{hex_color}[/#a6adc8]"
                )
            self.query_one("#theme-palette", Static).update("\n".join(lines))
        else:
            self.query_one("#theme-palette", Static).update(
                "[dim]  No colors detected in theme.txt[/dim]"
            )

        # Raw theme.txt preview
        if theme.raw_txt:
            lines = []
            for line in theme.raw_txt.splitlines()[:40]:
                s = line.strip()
                if s.startswith("#"):
                    lines.append(f"[dim]{line}[/dim]")
                elif "color" in s.lower() and (":" in s or "=" in s):
                    lines.append(f"[#f5c2e7]{line}[/#f5c2e7]")
                elif "font" in s.lower():
                    lines.append(f"[#89b4fa]{line}[/#89b4fa]")
                elif s.startswith("+"):
                    lines.append(f"[#a6e3a1]{line}[/#a6e3a1]")
                else:
                    lines.append(f"[#cdd6f4]{line}[/#cdd6f4]")
            self.query_one("#theme-preview", Static).update("\n".join(lines))
        else:
            self.query_one("#theme-preview", Static).update(
                "[dim]  Could not read theme.txt[/dim]"
            )

        self.query_one("#theme-help", Static).update("")
        self.query_one("#theme-help").display = False

    def _clear_detail(self) -> None:
        self.query_one("#theme-detail-header", Static).update(
            "[dim]Select a theme to preview it.[/dim]"
        )
        self.query_one("#theme-palette", Static).update("")
        self.query_one("#theme-preview", Static).update("")

    def _color_swatch(self, hex_color: str) -> str:
        try:
            color = hex_color.lstrip("#")
            return f"[on #{color}]   [/on #{color}]"
        except Exception:
            return "   "

    # Help

    def action_show_help(self) -> None:
        if self._showing_help:
            self._hide_help()
        else:
            self._show_help()

    def _show_help(self) -> None:
        self._showing_help = True
        help_text = """\
[bold #89b4fa]How to Install and Use GRUB Themes[/bold #89b4fa]

[bold #a6adc8]Where themes must be saved:[/bold #a6adc8]

  [#cdd6f4]/boot/grub/themes/[/#cdd6f4]

  Each theme lives in its own subfolder. Example:

  [dim]/boot/grub/themes/
    catppuccin-mocha/
      theme.txt        <- required
      background.png   <- optional
      *.pf2            <- font files
    starfield/
      theme.txt
      ...[/dim]

[bold #a6adc8]How to install a theme:[/bold #a6adc8]

  1. Download the theme (usually a .tar.gz or zip)
  2. Extract it to /boot/grub/themes/
     Example:
     [dim]sudo tar -xzf catppuccin-mocha.tar.gz -C /boot/grub/themes/[/dim]
  3. Press F5 in GrubForge to refresh the theme list
  4. Select the theme and press A to apply
  5. Go to Config Editor (press 2) and press Ctrl+R to regenerate grub.cfg

[bold #a6adc8]Where to find themes:[/bold #a6adc8]

  [#89b4fa]Catppuccin Mocha[/#89b4fa] (recommended):
  [dim]https://github.com/catppuccin/grub[/dim]

  [#89b4fa]Vimix:[/#89b4fa]
  [dim]https://github.com/vinceliuice/grub2-themes[/dim]

  [#89b4fa]Sleek:[/#89b4fa]
  [dim]https://github.com/sandesh236/sleek--themes[/dim]

  [#89b4fa]Many more:[/#89b4fa]
  [dim]https://www.gnome-look.org/browse?cat=109[/dim]

[bold #a6adc8]Tips:[/bold #a6adc8]

  - Themes require GRUB_TERMINAL_OUTPUT=gfxterm to display
  - Set GRUB_GFXMODE to your screen resolution (e.g. 1920x1080)
  - Both settings can be changed in Config Editor (press 2)
  - After applying a theme, always regenerate grub.cfg with Ctrl+R

[dim]Press H again or select a theme to close this help.[/dim]
"""
        help_widget = self.query_one("#theme-help", Static)
        help_widget.update(help_text)
        help_widget.display = True

        # Hide detail panels while showing help
        self.query_one("#theme-detail-header", Static).update("")
        self.query_one("#theme-palette", Static).update("")
        self.query_one("#theme-preview", Static).update("")

        self._set_status("Theme installation help -- press H to close", "info")

    def _hide_help(self) -> None:
        self._showing_help = False
        self.query_one("#theme-help").display = False
        if self._selected_idx >= 0:
            self._show_detail(self._selected_idx)

    # Buttons

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-apply":
            self.run_worker(self.action_apply_theme(), exclusive=True)
        elif event.button.id == "btn-refresh":
            self.action_refresh()
        elif event.button.id == "btn-help":
            self.action_show_help()

    # Apply theme

    @work
    async def action_apply_theme(self) -> None:
        idx = self._selected_idx
        if idx < 0 or idx >= len(self._themes):
            self._set_status("No theme selected.", "warn")
            return

        theme     = self._themes[idx]
        confirmed = await self.app.push_screen_wait(
            ConfirmDialog(
                title="Apply GRUB Theme",
                message=(
                    f"Apply theme: {theme.name}\n\n"
                    f"This will set GRUB_THEME in /etc/default/grub.\n"
                    f"A backup will be created first.\n\n"
                    f"Go to Config Editor and press Ctrl+R\n"
                    f"to regenerate grub.cfg after applying."
                ),
                confirm_label="Apply",
                confirm_variant="success",
            )
        )
        if not confirmed:
            return

        try:
            apply_theme(theme)
            self._set_status(
                f"Theme '{theme.name}' applied. Go to Config Editor and press Ctrl+R.",
                "ok",
            )
            self._load_themes()
        except PermissionError:
            self._set_status(
                "Permission denied - run GrubForge with sudo.", "error"
            )
        except Exception as e:
            self._set_status(f"Failed to apply theme: {e}", "error")

    def action_refresh(self) -> None:
        self._load_themes()
        self._set_status("Theme list refreshed.", "info")

    # Status bar

    def _set_status(self, msg: str, level: str = "info") -> None:
        color_map = {
            "ok":    "#a6e3a1",
            "info":  "#89b4fa",
            "warn":  "#f9e2af",
            "error": "#f38ba8",
        }
        icon_map = {"ok": "ok", "info": ">>", "warn": "!!", "error": "xx"}
        color = color_map.get(level, "#cdd6f4")
        icon  = icon_map.get(level, ">>")
        self.query_one("#backup-status", Static).update(
            f"[{color}]{icon} {msg}[/{color}]"
        )