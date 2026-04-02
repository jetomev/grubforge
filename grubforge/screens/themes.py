"""
GrubForge — Themes Screen (Placeholder)
Full theme browser, preview, and download coming in the next iteration.
"""

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import ScrollableContainer


class ThemesScreen(ScrollableContainer):
    """Theme browser placeholder — coming soon."""

    def compose(self) -> ComposeResult:
        yield Static(
            """\
[bold #89b4fa]╔═══════════════════════════════════════════════╗
║              Theme Browser                     ║
╚═══════════════════════════════════════════════╝[/bold #89b4fa]

[dim]This screen is coming in the next iteration.[/dim]

[bold #a6adc8]Planned features:[/bold #a6adc8]

  [#89b4fa]●[/#89b4fa]  Browse locally installed GRUB themes
  [#89b4fa]●[/#89b4fa]  Live ASCII preview of theme colors
  [#89b4fa]●[/#89b4fa]  One-click apply (updates GRUB_THEME in config)
  [#89b4fa]●[/#89b4fa]  Download themes from a curated list:
       – Catppuccin Mocha
       – Vimix
       – Sleek
       – Poly Dark
       – CyberRe

[bold #a6adc8]Where GRUB themes live:[/bold #a6adc8]

  [dim]/boot/grub/themes/[/dim]

[bold #a6adc8]Currently configured theme:[/bold #a6adc8]

  [dim]Set GRUB_THEME in Config Editor (screen 2)[/dim]

[dim italic]  Press 2 to go to Config Editor[/dim italic]
"""
        )