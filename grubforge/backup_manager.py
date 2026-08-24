"""
grubForge — Backup Manager
Creates timestamped backups of /etc/default/grub and restores them safely.

Listing and reading backups needs no special rights. Creating, restoring and
deleting them do, so those go through the privileged helper — see
grubforge/privilege.py.
"""

from datetime import datetime
from pathlib import Path
from dataclasses import dataclass

from grubforge import privilege
from grubforge.privilege import HelperResult


# ── Constants ─────────────────────────────────────────────────────────────────

BACKUP_DIR       = Path("/var/lib/grubforge/backups")
GRUB_CONFIG_PATH = Path("/etc/default/grub")
MAX_BACKUPS      = 10
BACKUP_PREFIX    = "grub_"
BACKUP_SUFFIX    = ".bak"

_TS_FORMAT = "%Y%m%d_%H%M%S_%f"


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Backup:
    """Describes a single backup file."""
    path:       Path
    timestamp:  datetime
    size_bytes: int
    label:      str = ""

    @property
    def display_name(self) -> str:
        ts    = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        label = f"  [{self.label}]" if self.label else ""
        return f"{ts}{label}"

    @property
    def size_display(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        return f"{self.size_bytes / 1024:.1f} KB"


# ── Core functions ────────────────────────────────────────────────────────────

async def create_backup(label: str = "", capability=None) -> HelperResult:
    """
    Snapshot /etc/default/grub into the backup directory.

    On success, HelperResult.output holds the new backup's filename. Old
    backups beyond MAX_BACKUPS are removed by the helper in the same step.
    """
    return await privilege.run_async(
        "backup-create", argument=label, capability=capability
    )


def list_backups() -> list:
    """
    Return all backups in BACKUP_DIR, newest first.
    Returns an empty list if the directory does not exist yet.
    """
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for p in sorted(
        BACKUP_DIR.glob(f"{BACKUP_PREFIX}*{BACKUP_SUFFIX}"),
        reverse=True,
    ):
        try:
            ts    = _parse_timestamp(p)
            label = _read_label(p)
            stat  = p.stat()
            backups.append(Backup(
                path       = p,
                timestamp  = ts,
                size_bytes = stat.st_size,
                label      = label,
            ))
        except Exception:
            continue

    return backups


async def restore_backup(backup: Backup, capability=None) -> HelperResult:
    """
    Put a backup back over /etc/default/grub.

    The helper snapshots the current config first, so restoring is itself
    undoable, and re-checks the backup's contents before writing.
    """
    return await privilege.run_async(
        "backup-restore", argument=backup.path.name, capability=capability
    )


async def delete_backup(backup: Backup, capability=None) -> HelperResult:
    """Delete a backup file and its label sidecar."""
    return await privilege.run_async(
        "backup-delete", argument=backup.path.name, capability=capability
    )


def read_backup_content(backup: Backup) -> str:
    """Return the raw text content of a backup file."""
    return backup.path.read_text(encoding="utf-8")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _label_path(backup_path: Path) -> Path:
    return backup_path.with_suffix(backup_path.suffix + ".label")


def _parse_timestamp(path: Path) -> datetime:
    """Extract datetime from filename: grub_YYYYMMDD_HHMMSS_ffffff.bak"""
    stem    = path.stem
    ts_part = stem.removeprefix(BACKUP_PREFIX)
    return datetime.strptime(ts_part, _TS_FORMAT)


def _read_label(backup_path: Path) -> str:
    p = _label_path(backup_path)
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return ""
