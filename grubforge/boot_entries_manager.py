"""
grubForge — Boot Entries Manager
Reads boot entries from grub.cfg, allows reordering and grouping,
writes custom order to /etc/grub.d/40_custom, and manages script permissions.
"""

import re
import os
import stat
import subprocess
from pathlib import Path
from dataclasses import dataclass, field


# ── Constants ─────────────────────────────────────────────────────────────────

GRUB_CFG_PATH    = Path("/boot/grub/grub.cfg")
GRUB_D_PATH      = Path("/etc/grub.d")
CUSTOM_40        = GRUB_D_PATH / "40_custom"
MANAGED_SCRIPTS  = ["10_linux", "20_linux_xen", "30_os-prober", "30_uefi-firmware"]

CUSTOM_40_HEADER = """\
#!/bin/sh
exec tail -n +3 $0
# This file is managed by grubForge.
# Manual edits may be overwritten.
# To restore original boot order, use grubForge > Boot Entries > Restore Original.

"""


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class BootEntry:
    """A single boot entry or submenu from grub.cfg."""
    title:      str
    entry_type: str        # "menuentry" | "submenu"
    source:     str        # which grub.d script generates this
    raw_block:  str        # full menuentry { ... } block
    children:   list = field(default_factory=list)  # for submenus
    enabled:    bool = True

    @property
    def display_title(self) -> str:
        icon = "📁" if self.entry_type == "submenu" else "🖥"
        children_note = f" ({len(self.children)} entries)" if self.children else ""
        return f"{icon}  {self.title}{children_note}"

    @property
    def source_label(self) -> str:
        labels = {
            "10_linux":           "Arch Linux",
            "30_os-prober":       "OS Prober",
            "30_uefi-firmware":   "UEFI",
            "41_snapshots-btrfs": "BTRFS Snapshots",
            "40_custom":          "Custom",
        }
        return labels.get(self.source, self.source)


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_boot_entries(cfg_path: Path = GRUB_CFG_PATH) -> list:
    """
    Parse grub.cfg and return a list of BootEntry objects.
    Only returns top-level menuentry and submenu blocks.
    """
    if not cfg_path.exists():
        return _mock_entries()

    try:
        text = cfg_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    entries = []
    lines   = text.splitlines()
    i       = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip the menuentry_id_option lines and exports
        if line.startswith("if") or line.startswith("export") or \
           line.startswith("#") or not line:
            i += 1
            continue

        # Match top-level menuentry or submenu
        me = re.match(r'^(menuentry|submenu)\s+[\'"](.+?)[\'"]', line)
        if me:
            entry_type = me.group(1)
            title      = me.group(2)

            # Grab the full block
            block, end_i = _extract_block(lines, i)
            source       = _guess_source(title, entry_type)

            entry = BootEntry(
                title      = title,
                entry_type = entry_type,
                source     = source,
                raw_block  = block,
            )

            # If submenu, parse children
            if entry_type == "submenu":
                entry.children = _parse_submenu_children(block)

            entries.append(entry)
            i = end_i + 1
            continue

        i += 1

    return entries


def _extract_block(lines: list, start: int) -> tuple:
    """
    Extract a { ... } block starting at lines[start].
    Returns (block_text, end_line_index).
    """
    depth     = 0
    block     = []
    i         = start

    while i < len(lines):
        line = lines[i]
        block.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0 and i > start:
            break
        i += 1

    return "\n".join(block), i


def _parse_submenu_children(block: str) -> list:
    """Extract child menuentry titles from a submenu block."""
    children = []
    for match in re.finditer(r'menuentry\s+[\'"](.+?)[\'"]', block):
        children.append(match.group(1))
    return children


def _guess_source(title: str, entry_type: str) -> str:
    """Guess which grub.d script generated this entry."""
    title_lower = title.lower()
    if "windows" in title_lower:
        return "30_os-prober"
    if "uefi" in title_lower or "firmware" in title_lower:
        return "30_uefi-firmware"
    if "snapshot" in title_lower:
        return "41_snapshots-btrfs"
    if "arch" in title_lower or entry_type == "submenu" and "advanced" in title_lower:
        return "10_linux"
    return "10_linux"


# ── Writer ────────────────────────────────────────────────────────────────────

def write_custom_order(entries: list) -> None:
    """
    Write the given entries to /etc/grub.d/40_custom in order.
    Requires root privileges.
    """
    lines = [CUSTOM_40_HEADER]

    for entry in entries:
        if entry.enabled:
            lines.append(entry.raw_block)
            lines.append("")

    content = "\n".join(lines)
    CUSTOM_40.write_text(content, encoding="utf-8")

    # Make sure 40_custom is executable
    current = CUSTOM_40.stat().st_mode
    CUSTOM_40.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# ── Script permission management ──────────────────────────────────────────────

def disable_script(script_name: str) -> None:
    """
    Remove execute permission from a grub.d script so grub-mkconfig skips it.
    Backs up original permissions first.
    """
    script = GRUB_D_PATH / script_name
    if not script.exists():
        return

    # Save original permissions as a sidecar
    perm_backup = script.with_suffix(".grubforge_perms")
    if not perm_backup.exists():
        original_mode = oct(script.stat().st_mode)
        perm_backup.write_text(original_mode, encoding="utf-8")

    # Remove execute bits
    current = script.stat().st_mode
    script.chmod(
        current & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH
    )


def enable_script(script_name: str) -> None:
    """
    Restore execute permission to a grub.d script.
    Restores original permissions if backup exists.
    """
    script = GRUB_D_PATH / script_name
    if not script.exists():
        return

    perm_backup = script.with_suffix(".grubforge_perms")
    if perm_backup.exists():
        try:
            original_mode = int(perm_backup.read_text().strip(), 8)
            script.chmod(original_mode)
            perm_backup.unlink()
            return
        except Exception:
            pass

    # Fallback: just add execute bits back
    current = script.stat().st_mode
    script.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def get_script_status() -> dict:
    """
    Return a dict of {script_name: is_executable} for all managed scripts.
    """
    status = {}
    for name in MANAGED_SCRIPTS:
        script = GRUB_D_PATH / name
        if script.exists():
            mode = script.stat().st_mode
            status[name] = bool(mode & stat.S_IXUSR)
        else:
            status[name] = None  # not installed
    return status


def restore_original_order() -> None:
    """
    Re-enable all managed scripts and clear 40_custom back to default.
    This restores the fully auto-generated grub.cfg behaviour.
    """
    for name in MANAGED_SCRIPTS:
        enable_script(name)

    # Reset 40_custom to the stock empty template
    CUSTOM_40.write_text(
        "#!/bin/sh\nexec tail -n +3 $0\n"
        "# This file provides an easy way to add custom menu entries.\n"
        "# Simply type the menu entries you want to add after this comment.\n"
        "# Be careful not to change the 'exec tail' line above.\n",
        encoding="utf-8",
    )
    current = CUSTOM_40.stat().st_mode
    CUSTOM_40.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


# ── Mock data (dev mode) ──────────────────────────────────────────────────────

def _mock_entries() -> list:
    """Return mock boot entries when grub.cfg is not available."""
    return [
        BootEntry(
            title      = "Arch Linux",
            entry_type = "menuentry",
            source     = "10_linux",
            raw_block  = 'menuentry "Arch Linux" {\n  echo "Loading Arch Linux"\n}',
        ),
        BootEntry(
            title      = "Advanced options for Arch Linux",
            entry_type = "submenu",
            source     = "10_linux",
            raw_block  = 'submenu "Advanced options for Arch Linux" {\n}',
            children   = ["Arch Linux, with Linux linux-zen", "Arch Linux, with Linux linux-lts"],
        ),
        BootEntry(
            title      = "Windows Boot Manager",
            entry_type = "menuentry",
            source     = "30_os-prober",
            raw_block  = 'menuentry "Windows Boot Manager" {\n  echo "Loading Windows"\n}',
        ),
        BootEntry(
            title      = "UEFI Firmware Settings",
            entry_type = "menuentry",
            source     = "30_uefi-firmware",
            raw_block  = 'menuentry "UEFI Firmware Settings" {\n  echo "Loading UEFI"\n}',
        ),
    ]
    
def rename_entry(entry: BootEntry, new_title: str) -> BootEntry:
    """
    Return a new BootEntry with the title replaced in the raw block.
    Does not write anything to disk — caller handles that.
    """
    if not new_title or not new_title.strip():
        raise ValueError("New title cannot be empty.")

    new_title = new_title.strip()

    # Replace the title in the first line of the raw block
    # Handles both single and double quoted titles
    new_raw = re.sub(
        r'^(menuentry|submenu)\s+([\'"]).*?\2',
        lambda m: f'{m.group(1)} {m.group(2)}{new_title}{m.group(2)}',
        entry.raw_block,
        count=1,
        flags=re.MULTILINE,
    )

    return BootEntry(
        title      = new_title,
        entry_type = entry.entry_type,
        source     = entry.source,
        raw_block  = new_raw,
        children   = entry.children,
        enabled    = entry.enabled,
    )
    
# ── Custom entry templates ────────────────────────────────────────────────────

CUSTOM_ENTRY_TEMPLATES = {
    "Linux": """\
menuentry "{title}" {{
    search --no-floppy --fs-uuid --set=root {uuid}
    linux   /boot/vmlinuz-linux root=UUID={uuid} rw quiet loglevel=3
    initrd  /boot/initramfs-linux.img
}}""",

    "Chainload": """\
menuentry "{title}" {{
    insmod part_gpt
    insmod fat
    search --no-floppy --fs-uuid --set=root {uuid}
    chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}}""",

    "Memtest": """\
menuentry "{title}" {{
    insmod part_gpt
    insmod ext2
    search --no-floppy --fs-uuid --set=root {uuid}
    linux16 /boot/memtest86+/memtest.efi
}}""",

    "Blank": """\
menuentry "{title}" {{
    # Add your boot commands here
    echo "Loading {title}..."
}}""",
}


def create_custom_entry(title: str, template_name: str, raw_block: str = "") -> BootEntry:
    """
    Create a new BootEntry from a title and raw block.
    If raw_block is provided, use it directly.
    Otherwise use the template as a starting point.
    """
    if not title or not title.strip():
        raise ValueError("Entry title cannot be empty.")

    title = title.strip()

    if not raw_block:
        template = CUSTOM_ENTRY_TEMPLATES.get(template_name, CUSTOM_ENTRY_TEMPLATES["Blank"])
        raw_block = template.format(title=title, uuid="YOUR-UUID-HERE")

    return BootEntry(
        title      = title,
        entry_type = "menuentry",
        source     = "40_custom",
        raw_block  = raw_block,
    )


def get_template_names() -> list:
    """Return list of available template names."""
    return list(CUSTOM_ENTRY_TEMPLATES.keys())


def get_template_preview(template_name: str, title: str = "My Entry") -> str:
    """Return a filled-in preview of a template."""
    template = CUSTOM_ENTRY_TEMPLATES.get(template_name, CUSTOM_ENTRY_TEMPLATES["Blank"])
    return template.format(title=title, uuid="YOUR-UUID-HERE")
    
# ── OS Detection ──────────────────────────────────────────────────────────────

def is_os_prober_installed() -> bool:
    """Check if os-prober is installed on the system."""
    return Path("/usr/bin/os-prober").exists()


def is_os_prober_enabled() -> bool:
    """
    Check if os-prober is enabled in /etc/default/grub.
    Returns True if GRUB_DISABLE_OS_PROBER is not set or set to false.
    """
    from grubforge.config_manager import GRUB_CONFIG_PATH, parse_grub_config
    try:
        config = parse_grub_config(GRUB_CONFIG_PATH)
        entry  = config.entries.get("GRUB_DISABLE_OS_PROBER")
        if not entry or entry.commented:
            return True   # not set means os-prober runs by default
        return entry.value.lower() == "false"
    except Exception:
        return False


def install_os_prober() -> tuple:
    """
    Install os-prober via pacman.
    Returns (success: bool, output: str).
    Requires root privileges.
    """
    try:
        result = subprocess.run(
            ["pacman", "-S", "--noconfirm", "os-prober"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, "pacman not found. Is this an Arch-based system?"
    except subprocess.TimeoutExpired:
        return False, "pacman timed out after 120 seconds."
    except Exception as e:
        return False, str(e)


def enable_os_prober() -> None:
    """
    Set GRUB_DISABLE_OS_PROBER=false in /etc/default/grub.
    Creates a backup first.
    Requires root privileges.
    """
    from grubforge.config_manager import GRUB_CONFIG_PATH, parse_grub_config, write_grub_config
    from grubforge.backup_manager import create_backup

    create_backup(label="pre-os-prober-enable")
    config    = parse_grub_config(GRUB_CONFIG_PATH)
    new_lines = write_grub_config(config, {"GRUB_DISABLE_OS_PROBER": "false"})

    if GRUB_CONFIG_PATH.exists():
        GRUB_CONFIG_PATH.write_text("".join(new_lines), encoding="utf-8")


def run_os_prober() -> tuple:
    """
    Run os-prober to detect other operating systems.
    Returns (success: bool, detected: list of str).
    Each detected item is a line like:
      /dev/sdb2:Windows 11:Windows:chain
    Requires root privileges.
    """
    try:
        result = subprocess.run(
            ["os-prober"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return True, []

        detected = []
        for line in output.splitlines():
            line = line.strip()
            if line:
                detected.append(line)

        return True, detected
    except FileNotFoundError:
        return False, ["os-prober not found."]
    except subprocess.TimeoutExpired:
        return False, ["os-prober timed out after 30 seconds."]
    except Exception as e:
        return False, [str(e)]


def parse_os_prober_output(lines: list) -> list:
    """
    Parse os-prober output lines into human readable dicts.
    Each line format: /dev/sdXN:Label:ShortName:type
    Returns list of {device, label, short, type} dicts.
    """
    results = []
    for line in lines:
        parts = line.split(":")
        if len(parts) >= 3:
            results.append({
                "device": parts[0].strip(),
                "label":  parts[1].strip(),
                "short":  parts[2].strip() if len(parts) > 2 else "",
                "type":   parts[3].strip() if len(parts) > 3 else "unknown",
            })
    return results