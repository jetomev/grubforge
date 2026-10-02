"""
grubForge — Boot Entries Manager
Reads boot entries from grub.cfg, allows reordering and grouping,
writes custom order to /etc/grub.d/40_custom, and manages script permissions.

Reading grub.cfg and working out the new order happen here, as your user.
Writing the result, changing script permissions and scanning for other
operating systems all go through the privileged helper — see
grubforge/privilege.py.
"""

import re
import stat
from pathlib import Path
from dataclasses import dataclass, field

from grubforge import privilege
from grubforge.privilege import HelperResult
from grubforge.system import system_name


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

# grub-mkconfig wraps each /etc/grub.d script's output in these markers, so
# grub.cfg itself says which script produced every entry (issue #28).
# v2.0.0: "+" allowed — Debian ships 20_memtest86+, whose entries were
# unrecognised, guessed as 10_linux, and so copied into a saved order (#20).
SECTION_BEGIN_RE = re.compile(r'^### BEGIN /etc/grub\.d/([A-Za-z0-9_.+-]+) ###$')
SECTION_END_RE   = re.compile(r'^### END /etc/grub\.d/([A-Za-z0-9_.+-]+) ###$')

# Saving a custom order moves every entry into 40_custom, where the markers can
# only say "40_custom". So grubForge writes where each entry originally came
# from on the line above it, and reads it back. 40_custom starts with
# `exec tail -n +3 $0`, so these lines reach grub.cfg as comments, which GRUB
# ignores. " (guessed)" marks an origin grubForge could not read.
ORIGIN_PREFIX    = "# grubforge-source: "
ORIGIN_RE        = re.compile(r'^# grubforge-source: ([A-Za-z0-9_.+-]+)( \(guessed\))?$')

# The third line of CUSTOM_40_HEADER, and the first one tail prints. Seeing it
# in grub.cfg means grubForge wrote that 40_custom, even one saved before
# origin lines existed.
MANAGED_MARK     = "# This file is managed by grubForge."


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
    # Held in grubForge's saved custom order (40_custom). `source` still names
    # where the entry originally came from: that is what "Source" means (#28).
    in_custom_order: bool = False
    # The source was inferred from the title, not read from grub.cfg.
    source_guessed:  bool = False

    @property
    def display_title(self) -> str:
        icon = "📁" if self.entry_type == "submenu" else "🖥"
        children_note = f" ({len(self.children)} entries)" if self.children else ""
        return f"{icon}  {self.title}{children_note}"

    @property
    def source_label(self) -> str:
        # 10_linux and 20_linux_xen find kernels on THIS machine, whatever it
        # happens to be, so the label has to come from the machine rather than
        # from an assumption. Hardcoding "Arch Linux" here labelled Debian's
        # own boot entries as Arch for every non-Arch user (issue #27).
        this_system = system_name()
        labels = {
            "10_linux":           this_system,
            "20_linux_xen":       f"{this_system} (Xen)",
            "30_os-prober":       "OS Prober",
            "30_uefi-firmware":   "UEFI",
            "41_snapshots-btrfs": "BTRFS Snapshots",
            "40_custom":          "Custom",
        }
        label = labels.get(self.source, self.source)
        if self.source_guessed:
            label += " (guessed)"
        if self.in_custom_order and self.source != "40_custom":
            label += " · custom order"
        return label


# ── Parser ────────────────────────────────────────────────────────────────────

class GrubCfgUnreadable(Exception):
    """
    grub.cfg exists, but this user is not allowed to read it.

    Worth its own exception. Some distributions ship /boot/grub/grub.cfg
    readable only by root, and reporting "0 boot entries" for a file we were
    never able to open tells the user something that is not true. Callers catch
    this and read the file through the privileged helper instead.
    """

    def __init__(self, path):
        self.path = path
        super().__init__(f"{path} is readable only by root")


def parse_boot_entries(cfg_path: Path = GRUB_CFG_PATH) -> list:
    """
    Parse grub.cfg and return a list of BootEntry objects.
    Only returns top-level menuentry and submenu blocks.

    Raises GrubCfgUnreadable when the file is present but unreadable as this
    user, so the caller can ask for permission rather than show an empty menu.
    """
    if not cfg_path.exists():
        return _mock_entries()

    try:
        text = cfg_path.read_text(encoding="utf-8", errors="replace")
    except PermissionError as exc:
        raise GrubCfgUnreadable(cfg_path) from exc
    except OSError:
        return []

    return parse_entries_text(text)


async def parse_boot_entries_privileged(capability=None) -> tuple:
    """
    Read the boot menu through the privileged helper, prompting via polkit.

    Returns (entries, HelperResult). The helper hands back only the menuentry
    and submenu blocks, so the rest of grub.cfg never reaches this process.
    """
    result = await privilege.run_async("read-entries", capability=capability)
    if not result.ok:
        return [], result
    return parse_entries_text(result.output), result


def parse_entries_text(text: str) -> list:
    """
    Parse grub.cfg content into BootEntry objects — top-level blocks only.

    Each entry's source is read from the section markers grub-mkconfig writes
    around every script's output. Inside grubForge's own 40_custom it comes
    from the origin line written above the entry. Only when neither exists (a
    hand-written grub.cfg, or an order saved before v1.1.3) is it guessed.
    """
    entries    = []
    lines      = text.splitlines()
    i          = 0
    section    = None    # the /etc/grub.d script whose output we are inside
    managed_40 = False   # this 40_custom was written by grubForge
    origin     = None    # (script, guessed) from the line above the next entry

    while i < len(lines):
        line = lines[i].strip()

        begin = SECTION_BEGIN_RE.match(line)
        if begin:
            section, managed_40, origin = begin.group(1), False, None
            i += 1
            continue
        if SECTION_END_RE.match(line):
            section, managed_40, origin = None, False, None
            i += 1
            continue
        mark = ORIGIN_RE.match(line)
        if mark:
            origin = (mark.group(1), bool(mark.group(2)))
            i += 1
            continue
        if line == MANAGED_MARK:
            managed_40 = True
            i += 1
            continue

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
            source, guessed, custom = _resolve_source(
                title, entry_type, section, managed_40, origin)
            origin = None

            entry = BootEntry(
                title           = title,
                entry_type      = entry_type,
                source          = source,
                raw_block       = block,
                in_custom_order = custom,
                source_guessed  = guessed,
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


def _resolve_source(title, entry_type, section, managed_40, origin) -> tuple:
    """
    Work out where an entry came from. Returns (source, guessed, in_custom_order).
    """
    if section is None:
        # No markers at all: a grub.cfg not written by grub-mkconfig.
        return _guess_source(title, entry_type), True, False

    if section != "40_custom":
        return section, False, False

    if origin:
        script, guessed = origin
        return script, guessed, script != "40_custom"

    if managed_40:
        # Saved by grubForge before origin lines existed. The entry did come
        # from somewhere else, and the title is all that is left to go on.
        return _guess_source(title, entry_type), True, True

    # Someone's own hand-written 40_custom entry.
    return "40_custom", False, False


def _guess_source(title: str, entry_type: str) -> str:
    """Guess which grub.d script generated this entry, from its title alone."""
    title_lower = title.lower()
    if "windows" in title_lower:
        return "30_os-prober"
    # os-prober titles every system it finds "<name> (on /dev/<device>)".
    if re.search(r'\(on /dev/[^)]+\)\s*$', title):
        return "30_os-prober"
    if "uefi" in title_lower or "firmware" in title_lower:
        return "30_uefi-firmware"
    if "snapshot" in title_lower:
        return "41_snapshots-btrfs"
    if "arch" in title_lower or entry_type == "submenu" and "advanced" in title_lower:
        return "10_linux"
    return "10_linux"


# ── Writer ────────────────────────────────────────────────────────────────────

def render_custom_order(entries: list) -> str:
    """
    Build the text of /etc/grub.d/40_custom for the given entries.

    Pure — produces the content without writing anything, so it can be shown,
    tested or diffed before it is ever handed to the helper.
    """
    lines = [CUSTOM_40_HEADER]

    for entry in entries:
        if entry.enabled:
            lines.append(_origin_line(entry))
            lines.append(entry.raw_block)
            lines.append("")

    return "\n".join(lines)


def _origin_line(entry: BootEntry) -> str:
    """The line above an entry in 40_custom that records where it came from."""
    source = entry.source
    if not re.fullmatch(r'[A-Za-z0-9_.+-]+', source or ""):
        # Never write something the reader would not accept back — and never a
        # newline into a file that GRUB and the shell both read.
        source, guessed = "40_custom", False
    else:
        guessed = entry.source_guessed
    return ORIGIN_PREFIX + source + (" (guessed)" if guessed else "")


async def write_custom_order(entries: list, capability=None) -> HelperResult:
    """Write the given entries to /etc/grub.d/40_custom, in order."""
    return await privilege.run_async(
        "write-custom-40",
        content=render_custom_order(entries),
        capability=capability,
    )


# ── Script permission management ──────────────────────────────────────────────

async def disable_script(script_name: str, capability=None) -> HelperResult:
    """
    Take away a grub.d script's execute bit, so grub-mkconfig skips it.

    The helper records the original permissions first, so enable_script() can
    put them back exactly rather than guessing.
    """
    return await privilege.run_async(
        "script-disable", argument=script_name, capability=capability
    )


async def enable_script(script_name: str, capability=None) -> HelperResult:
    """Give a grub.d script its execute bit back, restoring the saved mode."""
    return await privilege.run_async(
        "script-enable", argument=script_name, capability=capability
    )


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


STOCK_CUSTOM_40 = (
    "#!/bin/sh\nexec tail -n +3 $0\n"
    "# This file provides an easy way to add custom menu entries.\n"
    "# Simply type the menu entries you want to add after this comment.\n"
    "# Be careful not to change the 'exec tail' line above.\n"
)


async def restore_original_order(capability=None) -> HelperResult:
    """
    Hand the boot menu back to GRUB.

    Re-enables every managed script and resets 40_custom to Arch's stock
    template, so grub.cfg is fully auto-generated again. Stops at the first
    failure rather than half-restoring.
    """
    for name in MANAGED_SCRIPTS:
        if not (GRUB_D_PATH / name).is_file():
            continue  # not installed on this system
        result = await enable_script(name, capability=capability)
        if not result.ok:
            return result

    return await privilege.run_async(
        "write-custom-40", content=STOCK_CUSTOM_40, capability=capability
    )


# ── Mock data (dev mode) ──────────────────────────────────────────────────────

def _mock_entries() -> list:
    """Return mock boot entries when grub.cfg is not available."""
    this_system = system_name()
    return [
        BootEntry(
            title      = this_system,
            entry_type = "menuentry",
            source     = "10_linux",
            raw_block  = f'menuentry "{this_system}" {{\n  echo "Loading {this_system}"\n}}',
        ),
        BootEntry(
            title      = f"Advanced options for {this_system}",
            entry_type = "submenu",
            source     = "10_linux",
            raw_block  = f'submenu "Advanced options for {this_system}" {{\n}}',
            children   = [f"{this_system}, with Linux linux-zen",
                          f"{this_system}, with Linux linux-lts"],
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
        in_custom_order = entry.in_custom_order,
        source_guessed  = entry.source_guessed,
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


# grubForge no longer installs os-prober for you.
#
# It used to run `pacman -S --noconfirm os-prober` as root. Installing packages
# is a far wider power than editing a bootloader config, and it is your package
# manager's job, not grubForge's. We show the command instead; you run it.
OS_PROBER_INSTALL_HINT = (
    "os-prober is not installed.\n\n"
    "Install it with your package manager, then come back:\n\n"
    "    sudo pacman -S os-prober\n\n"
    "On KognogOS:\n\n"
    "    nog install os-prober"
)


async def enable_os_prober(capability=None) -> HelperResult:
    """
    Set GRUB_DISABLE_OS_PROBER=false in /etc/default/grub.

    Backs up first. Both steps are privileged, but polkit remembers the
    authorisation, so you are asked once.
    """
    from grubforge.config_manager import (
        GRUB_CONFIG_PATH, parse_grub_config, write_grub_config, save_grub_config,
    )
    from grubforge.backup_manager import create_backup

    backup = await create_backup(label="pre-os-prober-enable", capability=capability)
    if not backup.ok:
        return backup

    config    = parse_grub_config(GRUB_CONFIG_PATH)
    new_lines = write_grub_config(config, {"GRUB_DISABLE_OS_PROBER": "false"})

    return await save_grub_config(new_lines, capability=capability)


async def run_os_prober(capability=None) -> tuple:
    """
    Scan for other operating systems installed on this machine.

    Returns (result, detected) where detected holds lines like
      /dev/sdb2:Windows 11:Windows:chain
    Scanning every disk needs root, so this goes through the helper — but it
    only reads; nothing is changed by looking.
    """
    result = await privilege.run_async("os-prober-run", capability=capability)
    if not result.ok:
        return result, []

    detected = [line.strip() for line in result.output.splitlines() if line.strip()]
    return result, detected


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