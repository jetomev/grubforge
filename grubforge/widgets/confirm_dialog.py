"""
GrubForge — ConfirmDialog Widget
A modal confirmation dialog used before any destructive or system-level action.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Label, Static
from textual.containers import Container, Horizontal


class ConfirmDialog(ModalScreen):
    """
    A modal confirmation dialog.
    Returns True if confirmed, False if cancelled.
    """

    DEFAULT_CSS = """
    ConfirmDialog {
        align: center middle;
        background: $background 60%;
    }

    #confirm-dialog-container {
        background: #181825;
        border: solid #313244;
        width: 62;
        height: auto;
        padding: 2 3;
    }

    #confirm-dialog-title {
        color: #f9e2af;
        text-style: bold;
        margin-bottom: 1;
        width: 100%;
        text-align: center;
    }

    #confirm-dialog-body {
        color: #cdd6f4;
        margin-bottom: 2;
        width: 100%;
        text-align: center;
    }

    #confirm-dialog-buttons {
        layout: horizontal;
        align: center middle;
        height: 3;
        width: 100%;
    }

    #confirm-dialog-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        ("escape", "cancel",  "Cancel"),
        ("enter",  "confirm", "Confirm"),
    ]

    def __init__(
        self,
        title:           str = "Confirm",
        message:         str = "Are you sure?",
        confirm_label:   str = "Confirm",
        cancel_label:    str = "Cancel",
        confirm_variant: str = "primary",
    ) -> None:
        super().__init__()
        self._title           = title
        self._message         = message
        self._confirm_label   = confirm_label
        self._cancel_label    = cancel_label
        self._confirm_variant = confirm_variant

    def compose(self) -> ComposeResult:
        with Container(id="confirm-dialog-container"):
            yield Label(f"⚠  {self._title}", id="confirm-dialog-title")
            yield Static(self._message, id="confirm-dialog-body")
            with Horizontal(id="confirm-dialog-buttons"):
                yield Button(
                    self._confirm_label,
                    id="btn-confirm",
                    classes=f"-{self._confirm_variant}",
                )
                yield Button(self._cancel_label, id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-confirm")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm(self) -> None:
        self.dismiss(True)