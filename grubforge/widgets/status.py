"""Shared status-feedback mixin for grubForge screens.

Before v1.0.3, feedback diverged across screens (finding F9): each screen had
its own near-identical ``_set_status`` writing to an in-screen status line,
while the app-level global-binding dispatcher used toast popups. So pressing
``R`` (refresh) on a screen wrote blue text at the bottom, but pressing a key
the screen didn't handle fired a bottom-right popup — same keystroke, two
different feedback locations.

This mixin unifies the surface. ``_set_status`` keeps the persistent in-screen
status line (when the screen has one) AND fires an app-level notify popup, so
all action feedback is visually consistent with the dispatcher's popups.

Screens set ``STATUS_WIDGET_ID`` to the id of their status ``Static`` widget,
or leave it ``None`` (e.g. the Dashboard, which has no status line but still
gets the popup — that's what closes F10, "Dashboard R has no visible feedback").

It also consolidates the icon set: config_editor/backup used the unicode glyphs
(✓ ● ⚠ ✗) while themes/boot_entries had drifted to ASCII (ok >> !! xx). The
unicode set is now canonical everywhere.
"""

from __future__ import annotations

from textual.widgets import Static

# Catppuccin Mocha status colors, keyed by grubForge status level.
_COLOR = {
    "ok":    "#a6e3a1",
    "info":  "#89b4fa",
    "warn":  "#f9e2af",
    "error": "#f38ba8",
}

# Canonical status icons (unicode — consolidated from the divergent ASCII set
# that themes.py / boot_entries.py had copy-pasted).
_ICON = {
    "ok":    "✓",
    "info":  "●",
    "warn":  "⚠",
    "error": "✗",
}

# Map grubForge status levels to Textual notify severities.
_SEVERITY = {
    "ok":    "information",
    "info":  "information",
    "warn":  "warning",
    "error": "error",
}


class StatusMixin:
    """Provides a unified ``_set_status(msg, level)`` for screen widgets.

    Mix in *before* the Textual container base so this ``_set_status`` is the
    one resolved, e.g. ``class FooScreen(StatusMixin, Container)``.
    """

    # Override per screen with the id of its status Static, or leave None.
    STATUS_WIDGET_ID: str | None = None

    def _set_status(self, msg: str, level: str = "info", *, popup: bool = True) -> None:
        """Update the in-screen status line and (by default) fire a toast popup.

        Pass ``popup=False`` for *passive* status — a one-time hint written to
        the status line at mount, not action feedback. Without this, every
        screen's ``on_mount`` hint would toast at launch (all five screens mount
        up-front, hidden), spraying popups before the user has done anything.
        Action feedback uses the default ``popup=True`` so it stays consistent
        with the global-binding dispatcher's notifications (F9 / F10).
        """
        color = _COLOR.get(level, "#cdd6f4")
        icon = _ICON.get(level, "●")

        # Persistent in-screen status line, if this screen declares one.
        if self.STATUS_WIDGET_ID:
            try:
                self.query_one(f"#{self.STATUS_WIDGET_ID}", Static).update(
                    f"[{color}]{icon} {msg}[/{color}]"
                )
            except Exception:
                # Status widget not mounted yet (e.g. called during on_mount
                # before compose completes), or absent — the popup still fires.
                pass

        # Transient app-level popup — consistent with the global-binding
        # dispatcher's notifications (F9). Screens with no status line still
        # surface feedback here (F10).
        if popup:
            self.app.notify(msg, severity=_SEVERITY.get(level, "information"), timeout=4)
