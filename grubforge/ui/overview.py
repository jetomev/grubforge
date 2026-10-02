"""Overview — "is my boot menu all right?" in four boxes (v2.0.0).

Your boot menu · Needs attention · Safety · Common tasks. Anything that needs
attention comes with the button that fixes it.
"""

from __future__ import annotations

import datetime as dt

from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Grid, Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Static

from forgekit import glyph

from ..backup_manager import list_backups
from ..boot_entries_manager import GrubCfgUnreadable, parse_boot_entries
from ..settings_spec import BY_KEY, display


def _when(t: float | None) -> str:
    if not t:
        return "never"
    d = dt.datetime.fromtimestamp(t)
    today = dt.date.today()
    day = "today" if d.date() == today else ("yesterday" if d.date() == today - dt.timedelta(days=1)
                                             else f"{d:%b %d}")
    return f"{day} {d:%H:%M}"


class OverviewScreen(VerticalScroll, can_focus=False):
    FORGE_HINTS = [("Tab", "next button"), ("Enter", "do it"), ("1-5", "screens"), ("F1", "help"), ("?", "all keys")]

    def __init__(self, session, **kw) -> None:
        super().__init__(**kw)
        self.session = session

    def compose(self) -> ComposeResult:
        with Grid(id="gf-overview"):
            with Vertical(classes="gf-box", id="box-menu"):
                yield Static("", id="ov-menu")
            with Vertical(classes="gf-box gf-attention", id="box-attention"):
                yield Static("", id="ov-attention")
                with Horizontal(classes="forge-buttons gf-box-buttons", id="ov-attention-buttons"):
                    yield Button("Rebuild it now", id="ov-rebuild", variant="primary")
                    yield Button("What this means", id="ov-why")
            with Vertical(classes="gf-box", id="box-safety"):
                yield Static("", id="ov-safety")
            with Vertical(classes="gf-box", id="box-tasks"):
                yield Static("", id="ov-tasks")
                with Horizontal(classes="forge-buttons gf-task-row"):
                    yield Button("Choose what starts first", id="task-default")
                    yield Button("Change wait time", id="task-timeout")
                with Horizontal(classes="forge-buttons gf-task-row"):
                    yield Button("Pick a theme", id="task-theme")
                    yield Button("Back up now", id="task-backup")

    def on_mount(self) -> None:
        for box, title in (("box-menu", "Your boot menu"), ("box-attention", "Needs attention"),
                           ("box-safety", "Safety"), ("box-tasks", "Common tasks")):
            self.query_one(f"#{box}").border_title = title
        self.refresh_view()

    def refresh_view(self) -> None:
        s = self.session
        env = s.env
        try:
            entries = parse_boot_entries(env.grub_cfg)
            count = f"{len(entries)}" + (" · your own order" if self.session.custom_order_in_use else "")
        except GrubCfgUnreadable:
            count = "readable only by an administrator"
        except OSError:
            count = "unknown"
        rows = [
            ("Starts", display(BY_KEY["GRUB_DEFAULT"], s.original.get("GRUB_DEFAULT"))),
            ("Waits", display(BY_KEY["GRUB_TIMEOUT"], s.original.get("GRUB_TIMEOUT"))
             + ", " + display(BY_KEY["GRUB_TIMEOUT_STYLE"], s.original.get("GRUB_TIMEOUT_STYLE")).lower()),
            ("Entries", count),
            ("Theme", (s.original.get("GRUB_THEME") or "none").split("/")[-2]
             if (s.original.get("GRUB_THEME") or "").endswith("theme.txt") else (s.original.get("GRUB_THEME") or "none")),
            ("Rebuilt", _when(env.grub_cfg.stat().st_mtime if env.grub_cfg.exists() else None)),
        ]
        self.query_one("#ov-menu", Static).update(
            "\n".join(f"[$forge-muted]{k:<9}[/] {escape(v)}" for k, v in rows))

        # needs attention
        items = []
        stale = s.not_rebuilt
        if s.read_only:
            items.append(f"[b $forge-warn]{glyph('warn')}[/] [b]Read-only.[/] {escape(s.read_only_reason)}")
        if stale:
            items.append(f"[b $forge-warn]{glyph('warn')}[/] [b]The boot menu is older than your settings.[/]\n"
                         f"   Changes saved {_when(s.last_saved().timestamp() if s.last_saved() else None)} "
                         f"aren't in it yet.")
        if self.session.custom_order_in_use:
            items.append(f"[b $forge-warn]{glyph('warn')}[/] [b]Your own entry order is in use.[/]\n"
                         "   A new kernel won't show up until you restore the original order.")
        if s.overrides:
            names = ", ".join(sorted({f for f, _v in s.overrides.values()}))
            items.append(f"[$forge-info]{glyph('info')}[/] {len(s.overrides)} setting"
                         f"{'s are' if len(s.overrides) != 1 else ' is'} decided in /etc/default/grub.d "
                         f"({escape(names)}).\n   Settings shows them, locked, with the file that sets them.")
        if env.bls:
            items.append(f"[$forge-info]{glyph('info')}[/] This system keeps its entries as separate files "
                         "(Fedora style).")
        if not items:
            items.append(f"[$forge-ok]{glyph('ok')} Nothing needs attention.[/]")
        self.query_one("#ov-attention", Static).update("\n\n".join(items))
        self.query_one("#ov-rebuild").display = stale and not s.read_only
        self.query_one("#ov-why").display = self.session.custom_order_in_use
        self.query_one("#ov-attention-buttons").display = (stale and not s.read_only) or self.session.custom_order_in_use

        backups = list_backups()
        newest = _when(backups[0].timestamp.timestamp()) if backups else "none yet"
        pw = {"root": "not needed (running as root)", "polkit": "asked only when you save or rebuild",
              "none": "can't be asked: read-only"}[s.capability.level.value]
        self.query_one("#ov-safety", Static).update("\n".join([
            f"[$forge-muted]{'Backups':<10}[/] {len(backups)} · newest {newest}",
            f"[$forge-muted]{'Password':<10}[/] {pw}",
            f"[$forge-muted]{'GRUB':<10}[/] {escape(env.summary)}",
        ]))
        self.query_one("#ov-tasks", Static).update("[$forge-muted]One step to the things people change most.[/]")
