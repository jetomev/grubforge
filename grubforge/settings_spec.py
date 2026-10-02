"""Every setting grubForge shows, in plain words (v2.0.0).

One ``Setting`` per GRUB key: the name a person reads, the group it belongs
to, which control sets it, a one-paragraph explanation, and how GRUB's stored
text maps to what the control shows. Two of GRUB's switches are stored
backwards (``GRUB_DISABLE_OS_PROBER=false`` means "do look for other systems");
``inverted`` turns them the right way round.

``None`` as a value means "not set": the line is absent (or commented out) and
GRUB uses its own default, which ``default`` describes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

GROUPS = [
    ("startup", "Start-up", "How the boot menu behaves when the computer starts"),
    ("look", "Look", "What the boot menu looks like"),
    ("kernel", "Kernel options", "Extra instructions passed to Linux when it starts"),
    ("others", "Other systems", "Windows and other systems on this computer"),
    ("advanced", "Advanced", "Less common settings"),
]

# GRUB's 16 named colours, in its own order
GRUB_COLOURS = ["black", "blue", "green", "cyan", "red", "magenta", "brown", "light-gray",
                "dark-gray", "light-blue", "light-green", "light-cyan", "light-red",
                "light-magenta", "yellow", "white"]

# kernel options a person may want, with a plain explanation each
KNOWN_KERNEL_OPTIONS = [
    ("quiet", "fewer start-up messages"),
    ("splash", "picture, not text"),
    ("loglevel=3", "only serious errors"),
    ("nomodeset", "basic display driver"),
    ("nowatchdog", "no hang detector"),
    ("nvidia_drm.modeset=1", "NVIDIA on Wayland"),
]

COMMON_RESOLUTIONS = ["1920x1080", "2560x1440", "3840x2160", "1680x1050", "1600x900",
                      "1366x768", "1280x1024", "1280x720", "1024x768", "800x600"]


@dataclass
class Setting:
    key: str
    group: str
    label: str
    control: str            # list | switch | number | choices | text | kernel | colours | file
    help: str
    default: str = ""       # what GRUB does when the line is absent, in words
    inverted: bool = False  # switch: On is stored as "false"
    choices: list = field(default_factory=list)   # (value, label) for list/choices
    note: str = ""          # the muted second line when unchanged


SETTINGS: list[Setting] = [
    # ── Start-up ──
    Setting("GRUB_DEFAULT", "startup", "Start this entry", "list",
            "The entry GRUB starts when nobody presses a key. \"Last chosen\" starts whatever "
            "was picked the time before; it needs \"Remember last choice\" on as well.",
            default="the first entry", note="the entry GRUB starts when nobody presses a key"),
    Setting("GRUB_SAVEDEFAULT", "startup", "Remember last choice", "switch",
            "Remembers the entry you pick, so \"Last chosen\" can start it next time. Only "
            "has an effect when \"Start this entry\" is \"Last chosen\".",
            default="off", note='only works with "Last chosen"'),
    Setting("GRUB_TIMEOUT", "startup", "Wait before starting", "number",
            "How long the menu waits for you before starting the entry above. 0 starts at "
            "once; \"wait forever\" waits until you pick.", default="5 seconds"),
    Setting("GRUB_TIMEOUT_STYLE", "startup", "Show the menu", "choices",
            "\"Always\" shows the menu while it waits. \"With a countdown\" shows only the "
            "seconds left; press Esc to see the menu. \"Hidden\" shows nothing; hold Shift "
            "(or press Esc) while starting to see it.",
            default="always", choices=[("menu", "Always"), ("countdown", "With a countdown"),
                                       ("hidden", "Hidden")]),
    # ── Look ──
    Setting("GRUB_THEME", "look", "Theme", "list",
            "A theme changes the menu's background, fonts and colours. Themes need the "
            "menu drawn as graphics. The Themes screen shows a preview.", default="none"),
    Setting("GRUB_GFXMODE", "look", "Screen resolution", "list",
            "The menu's resolution. Automatic lets GRUB choose; pick your screen's size for "
            "sharp text and themes.", default="automatic"),
    Setting("GRUB_TERMINAL_OUTPUT", "look", "Menu drawn as", "list",
            "Graphics allows themes, pictures and any resolution. Plain text is the most "
            "reliable on unusual hardware.", default="automatic",
            choices=[("gfxterm", "Graphics"), ("console", "Plain text console"),
                     ("vga_text", "VGA text (older computers)"), ("serial", "Serial port")]),
    Setting("GRUB_COLOR_NORMAL", "look", "Text colours", "colours",
            "Colour of the menu's text, and of the background behind it, when no theme or "
            "picture is used.", default="GRUB's own"),
    Setting("GRUB_COLOR_HIGHLIGHT", "look", "Highlight colours", "colours",
            "Colour of the selected entry's text and its background.", default="GRUB's own"),
    Setting("GRUB_BACKGROUND", "look", "Background picture", "file",
            "A picture behind the menu (PNG, JPG or TGA) when no theme is used.",
            default="none"),
    Setting("GRUB_GFXPAYLOAD_LINUX", "look", "Resolution after the menu", "list",
            "What screen mode Linux starts in. \"Keep the menu's\" avoids a flicker.",
            default="GRUB decides",
            choices=[("keep", "Keep the menu's"), ("text", "Text mode")]),
    # ── Kernel options ──
    Setting("GRUB_CMDLINE_LINUX_DEFAULT", "kernel", "For normal starts", "kernel",
            "Options for a normal start. Recovery entries don't get these.",
            default="none"),
    Setting("GRUB_CMDLINE_LINUX", "kernel", "For every start", "kernel",
            "Options for every start, recovery included. Usually set by the installer "
            "(disks, encryption); change with care.", default="none"),
    # ── Other systems ──
    Setting("GRUB_DISABLE_OS_PROBER", "others", "Find other systems", "switch",
            "When on, rebuilding the boot menu also searches the disks for Windows and other "
            "operating systems and adds them to the menu. Needs the os-prober program.",
            default="off", inverted=True),
    # ── Advanced ──
    Setting("GRUB_DISABLE_SUBMENU", "advanced", "Older kernels in a submenu", "switch",
            "When on, extra kernels go into an \"Advanced options\" submenu, keeping the "
            "main menu short.", default="on", inverted=True),
    Setting("GRUB_DISTRIBUTOR", "advanced", "Name shown for this system", "text",
            "The name at the start of this system's entries. Often a command that reads it "
            "from the system; leave it unless you want a different name.", default="the system's name"),
    Setting("GRUB_TERMINAL_INPUT", "advanced", "Keyboard", "list",
            "Where GRUB reads keys from. Change only if the keyboard doesn't work in the menu.",
            default="automatic",
            choices=[("console", "Built-in keyboard"), ("usb_keyboard", "USB keyboard"),
                     ("at_keyboard", "AT keyboard"), ("serial", "Serial port")]),
]

BY_KEY = {s.key: s for s in SETTINGS}

TRUE_WORDS = {"true", "y", "yes", "1"}


def switch_is_on(setting: Setting, raw: str | None) -> bool:
    """What a switch shows for a stored value (None = not set)."""
    if raw is None or raw == "":
        return setting.default == "on"
    stored_true = raw.strip().lower() in TRUE_WORDS
    return (not stored_true) if setting.inverted else stored_true


def switch_value(setting: Setting, on: bool) -> str:
    """What to store for a switch position."""
    return ("false" if on else "true") if setting.inverted else ("true" if on else "false")


def split_kernel(raw: str | None) -> tuple[list[str], str]:
    """The known options that are on, and the rest as typed."""
    tokens = (raw or "").split()
    known = {k for k, _d in KNOWN_KERNEL_OPTIONS}
    on = [t for t in tokens if t in known]
    other = " ".join(t for t in tokens if t not in known)
    return on, other


def join_kernel(on: list[str], other: str) -> str:
    ordered = [k for k, _d in KNOWN_KERNEL_OPTIONS if k in on]
    return " ".join(ordered + other.split())


def kernel_other_problem(text: str) -> str:
    """Why a typed option list can't be stored, or "" when it can."""
    for bad, why in (('"', "quotes"), ("'", "quotes"), (";", "a semicolon"), ("`", "a backtick"),
                     ("$", "a dollar sign"), ("\\", "a backslash"), ("\n", "a line break")):
        if bad in text:
            return f"can't contain {why}"
    return ""


def display(setting: Setting, raw: str | None, choices: list | None = None) -> str:
    """A stored value in plain words, for the "was:" line and the review."""
    if raw is None:
        return f"not set ({setting.default})"
    if setting.control == "switch":
        return "On" if switch_is_on(setting, raw) else "Off"
    if setting.key == "GRUB_TIMEOUT":
        return "wait forever" if raw.strip() == "-1" else f"{raw} second{'' if raw.strip() == '1' else 's'}"
    if setting.key == "GRUB_GFXMODE" and raw == "auto":
        return "automatic"
    if setting.key == "GRUB_DEFAULT":
        if raw == "saved":
            return "Last chosen"
        if raw == "0":
            return "the first entry"
    for v, label in (choices or setting.choices):
        if v == raw:
            return label
    return raw if raw != "" else "empty"
