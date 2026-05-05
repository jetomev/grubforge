"""
grubForge — Backup Manager
Creates timestamped backups of /etc/default/grub and restores them safely.
"""

import shutil
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


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

def ensure_backup_dir() -> None:
    """Create the backup directory if it does not exist."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(
    source: Path = GRUB_CONFIG_PATH,
    label:  str  = "",
) -> Backup:
    """
    Copy source to BACKUP_DIR with a timestamped filename.
    Returns a Backup object describing the new backup.
    Falls back to mock content when source does not exist.
    """
    ensure_backup_dir()

    ts     = datetime.now()
    ts_str = ts.strftime(_TS_FORMAT)
    dest   = BACKUP_DIR / f"{BACKUP_PREFIX}{ts_str}{BACKUP_SUFFIX}"

    if source.exists():
        shutil.copy2(source, dest)
    else:
        dest.write_text(_mock_backup_content(ts_str), encoding="utf-8")

    if label:
        _label_path(dest).write_text(label, encoding="utf-8")

    _rotate_old_backups()

    stat = dest.stat()
    return Backup(path=dest, timestamp=ts, size_bytes=stat.st_size, label=label)


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


def restore_backup(
    backup: Backup,
    dest:   Path = GRUB_CONFIG_PATH,
) -> None:
    """
    Restore a backup over dest.
    Auto-creates a safety backup of the current file first.
    """
    if dest.exists():
        create_backup(source=dest, label="auto (pre-restore)")

    if dest.parent.exists():
        shutil.copy2(backup.path, dest)


def delete_backup(backup: Backup) -> None:
    """Delete a backup file and its label sidecar."""
    backup.path.unlink(missing_ok=True)
    _label_path(backup.path).unlink(missing_ok=True)


def read_backup_content(backup: Backup) -> str:
    """Return the raw text content of a backup file."""
    return backup.path.read_text(encoding="utf-8")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _rotate_old_backups() -> None:
    """Remove oldest backups when count exceeds MAX_BACKUPS."""
    all_backups = list_backups()
    for old in all_backups[MAX_BACKUPS:]:
        delete_backup(old)


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


def _mock_backup_content(ts: str) -> str:
    return f"""\
# grubForge mock backup — {ts}
# (Demo mode: no real /etc/default/grub found on this system)
GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DISTRIBUTOR="Arch Linux"
GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3"
GRUB_CMDLINE_LINUX=""
GRUB_GFXMODE=auto
GRUB_GFXPAYLOAD_LINUX=keep
GRUB_DISABLE_OS_PROBER=false
"""