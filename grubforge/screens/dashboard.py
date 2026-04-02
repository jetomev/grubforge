"""
GrubForge — Dashboard Screen
System overview: GRUB version, config status, backup count, quick stats.
"""

import subprocess
from pathlib import Path

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import ScrollableContainer

from grubforge.config_manager import GRUB_CONFIG_PATH, parse_grub_config
from grubforge.backup_manager import BACKUP_DIR, list_backups


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_grubcfg_path() -> Path:
    for p in [Path("/boot/grub/grub.cfg"), Path("/boot/grub2/grub.cfg")]:
        if p.exists():
            return p
    return Path("/boot/grub/grub.cfg")


def _count_boot_entries(cfg_path: Path) -> int:
    try:
        text = cfg_path.read_text(errors="replace")
        return text.count("menuentry ")
    except Exception:
        return 0


# ── Screen ────────────────────────────────────────────────────────────────────

class DashboardScreen(ScrollableContainer):
    """Main dashboard showing system and GRUB status at a glance."""

    def on_mount(self) -> None:
        self._refresh_data()

    def compose(self) -> ComposeResult:
        yield Static("", id="dashboard-content")

    def _refresh_data(self) -> None:
        config   = parse_grub_config(GRUB_CONFIG_PATH)
        backups  = list_backups()
        grubcfg  = _get_grubcfg_path()

        timeout  = config.entries.get("GRUB_TIMEOUT")
        default  = config.entries.get("GRUB_DEFAULT")
        theme    = config.entries.get("GRUB_THEME")
        gfxmode  = config.entries.get("GRUB_GFXMODE")
        cmdline  = config.entries.get("GRUB_CMDLINE_LINUX_DEFAULT")
        osprober = config.entries.get("GRUB_DISABLE_OS_PROBER")

        timeout_val  = timeout.value  if timeout  else "5 (default)"
        default_val  = default.value  if default  else "0"
        theme_val    = theme.value    if theme and theme.value else "none"
        gfxmode_val  = gfxmode.value  if gfxmode  else "auto"
        cmdline_val  = (cmdline.value if cmdline   else "quiet splash")[:46]
        osprober_val = osprober.value if osprober  else "false"

        config_exists  = GRUB_CONFIG_PATH.exists()
        grubcfg_exists = grubcfg.exists()
        backup_count   = len(backups)
        entry_count    = _count_boot_entries(grubcfg) if grubcfg_exists else 0

        cfg_status = (
            "[green]✓ Found[/green]" if config_exists
            else "[yellow]⚠ Not found (mock mode)[/yellow]"
        )
        grubcfg_status = (
            f"[green]✓ {grubcfg}[/green]" if grubcfg_exists
            else "[yellow]⚠ Not found (run grub-mkconfig)[/yellow]"
        )
        backup_color = "green" if backup_count > 0 else "yellow"
        mock_note = (
            "\n[dim italic]  ↳ Running in demo mode — /etc/default/grub not found[/dim italic]"
            if config.is_mock else ""
        )

        content = f"""\
[bold #89b4fa]╔═══════════════════════════════════════════════╗
║           GrubForge — System Overview          ║
╚═══════════════════════════════════════════════╝[/bold #89b4fa]
{mock_note}

[bold #a6adc8]── GRUB Configuration ────────────────────────────[/bold #a6adc8]

  [dim]Config file  [/dim]  {cfg_status}
  [dim]grub.cfg     [/dim]  {grubcfg_status}
  [dim]Boot entries [/dim]  [#cdd6f4]{entry_count}[/#cdd6f4] [dim]detected[/dim]

[bold #a6adc8]── Active Settings ────────────────────────────────[/bold #a6adc8]

  [dim]GRUB_DEFAULT              [/dim]  [#89b4fa]{default_val}[/#89b4fa]
  [dim]GRUB_TIMEOUT              [/dim]  [#cdd6f4]{timeout_val}s[/#cdd6f4]
  [dim]GRUB_GFXMODE              [/dim]  [#cdd6f4]{gfxmode_val}[/#cdd6f4]
  [dim]GRUB_CMDLINE_LINUX_DEFAULT[/dim]  [#a6adc8]{cmdline_val}[/#a6adc8]
  [dim]GRUB_THEME                [/dim]  [#cdd6f4]{theme_val}[/#cdd6f4]
  [dim]GRUB_DISABLE_OS_PROBER    [/dim]  [#cdd6f4]{osprober_val}[/#cdd6f4]

[bold #a6adc8]── Backups ────────────────────────────────────────[/bold #a6adc8]

  [dim]Backup count [/dim]  [{backup_color}]{backup_count}[/{backup_color}] [dim]saved in /var/lib/grubforge/backups[/dim]

[bold #a6adc8]── Quick Actions ──────────────────────────────────[/bold #a6adc8]

  [dim]Press [/dim][bold #89b4fa]2[/bold #89b4fa][dim] to open Config Editor[/dim]
  [dim]Press [/dim][bold #89b4fa]3[/bold #89b4fa][dim] to browse Themes[/dim]
  [dim]Press [/dim][bold #89b4fa]4[/bold #89b4fa][dim] to manage Backups[/dim]
  [dim]Press [/dim][bold #89b4fa]?[/bold #89b4fa][dim] for help[/dim]
"""
        self.query_one("#dashboard-content", Static).update(content)