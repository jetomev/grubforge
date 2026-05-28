"""grubForge — Help modal screen.

v1.0.3 F2: the help "overlay" used to be a ``self.notify(...)`` toast — it
stacked instead of toggling, auto-dismissed after 8s, and the "Press Esc to
close" hint it advertised did nothing (a toast has no dismiss action). This is
a real ``ModalScreen``: it toggles, stays until dismissed, and Esc / q / ?
close it. ``q`` is bound here so it shadows the app-level quit binding while the
help is open (screen bindings are checked before app bindings).
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Static
from textual.containers import Container, VerticalScroll


_HELP_TEXT = """\
[bold #89b4fa]Navigation[/bold #89b4fa]
  [#cdd6f4]1[/#cdd6f4] Dashboard    [#cdd6f4]2[/#cdd6f4] Config Editor    [#cdd6f4]3[/#cdd6f4] Themes
  [#cdd6f4]4[/#cdd6f4] Backup & Restore    [#cdd6f4]5[/#cdd6f4] Boot Entries

[bold #89b4fa]Universal actions[/bold #89b4fa] [dim](work on any screen)[/dim]
  [#cdd6f4]E[/#cdd6f4] Edit    [#cdd6f4]S[/#cdd6f4] Save    [#cdd6f4]A[/#cdd6f4] Apply
  [#cdd6f4]R[/#cdd6f4] Refresh    [#cdd6f4]Ctrl+R[/#cdd6f4] Regenerate grub.cfg

[bold #89b4fa]Boot Entries[/bold #89b4fa]
  [#cdd6f4]K[/#cdd6f4] move up    [#cdd6f4]J[/#cdd6f4] move down    [#cdd6f4]N[/#cdd6f4] rename    [#cdd6f4]X[/#cdd6f4] restore original

[bold #89b4fa]Backup & Restore[/bold #89b4fa]
  [#cdd6f4]N[/#cdd6f4] new    [#cdd6f4]X[/#cdd6f4] restore    [#cdd6f4]D[/#cdd6f4] delete

[bold #89b4fa]Themes[/bold #89b4fa]
  [#cdd6f4]H[/#cdd6f4] installation help

[bold #89b4fa]General[/bold #89b4fa]
  [#cdd6f4]?[/#cdd6f4] toggle this help    [#cdd6f4]q[/#cdd6f4] quit
"""


class HelpScreen(ModalScreen):
    """Toggleable, dismissible help overlay (F2)."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: $background 60%;
    }

    #help-dialog-container {
        background: #181825;
        border: solid #45475a;
        width: 66;
        height: auto;
        max-height: 90%;
        padding: 1 3;
    }

    #help-dialog-title {
        color: #89b4fa;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }

    #help-dialog-body {
        height: auto;
        max-height: 22;
    }

    #help-dialog-footer {
        color: #6c7086;
        margin-top: 1;
        width: 100%;
        text-align: center;
    }
    """

    BINDINGS = [
        ("escape",        "dismiss_help", "Close"),
        ("q",             "dismiss_help", "Close"),
        ("question_mark", "dismiss_help", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="help-dialog-container"):
            yield Static("⚡ grubForge — Help", id="help-dialog-title")
            with VerticalScroll(id="help-dialog-body"):
                yield Static(_HELP_TEXT)
            yield Static(
                "[dim]Press Esc, q, or ? to close[/dim]", id="help-dialog-footer"
            )

    def action_dismiss_help(self) -> None:
        self.dismiss(None)
