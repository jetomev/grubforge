"""
GrubForge — Config Manager
Handles reading, parsing, validating, and writing /etc/default/grub safely.
"""

import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field


# ── Constants ────────────────────────────────────────────────────────────────

GRUB_CONFIG_PATH = Path("/etc/default/grub")

MANAGED_KEYS = [
    "GRUB_DEFAULT",
    "GRUB_TIMEOUT",
    "GRUB_TIMEOUT_STYLE",
    "GRUB_DISTRIBUTOR",
    "GRUB_CMDLINE_LINUX_DEFAULT",
    "GRUB_CMDLINE_LINUX",
    "GRUB_TERMINAL_INPUT",
    "GRUB_TERMINAL_OUTPUT",
    "GRUB_GFXMODE",
    "GRUB_GFXPAYLOAD_LINUX",
    "GRUB_THEME",
    "GRUB_BACKGROUND",
    "GRUB_COLOR_NORMAL",
    "GRUB_COLOR_HIGHLIGHT",
    "GRUB_DISABLE_SUBMENU",
    "GRUB_DISABLE_OS_PROBER",
    "GRUB_SAVEDEFAULT",
]

KEY_DESCRIPTIONS = {
    "GRUB_DEFAULT":               "Default boot entry (index or 'saved')",
    "GRUB_TIMEOUT":               "Boot menu timeout in seconds (-1 = infinite)",
    "GRUB_TIMEOUT_STYLE":         "Timeout style: menu | countdown | hidden",
    "GRUB_DISTRIBUTOR":           "Distribution name shown in menu",
    "GRUB_CMDLINE_LINUX_DEFAULT": "Kernel parameters for normal boot",
    "GRUB_CMDLINE_LINUX":         "Kernel parameters for all entries",
    "GRUB_TERMINAL_INPUT":        "Terminal input: console | serial | at_keyboard",
    "GRUB_TERMINAL_OUTPUT":       "Terminal output: console | serial | gfxterm",
    "GRUB_GFXMODE":               "Graphical resolution (e.g. 1920x1080)",
    "GRUB_GFXPAYLOAD_LINUX":      "Kernel video mode: keep | text | <resolution>",
    "GRUB_THEME":                 "Path to GRUB theme file",
    "GRUB_BACKGROUND":            "Path to background image",
    "GRUB_COLOR_NORMAL":          "Normal text color (fg/bg)",
    "GRUB_COLOR_HIGHLIGHT":       "Highlighted text color (fg/bg)",
    "GRUB_DISABLE_SUBMENU":       "Disable submenus: true | false",
    "GRUB_DISABLE_OS_PROBER":     "Disable OS detection: true | false",
    "GRUB_SAVEDEFAULT":           "Save last selection as default: true | false",
}


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class GrubEntry:
    """A single key=value pair from /etc/default/grub."""
    key: str
    value: str
    raw_line: str
    line_number: int
    commented: bool = False


@dataclass
class GrubConfig:
    """Parsed representation of /etc/default/grub."""
    path: Path
    entries: dict = field(default_factory=dict)
    raw_lines: list = field(default_factory=list)
    is_mock: bool = False


# ── Parser ───────────────────────────────────────────────────────────────────

_LINE_RE = re.compile(
    r'^(?P<comment>#\s*)?'
    r'(?P<key>[A-Z_]+)'
    r'='
    r'(?P<value>"[^"]*"|[^#\n]*)'
    r'(?:\s*#.*)?$'
)


def parse_grub_config(path: Path) -> GrubConfig:
    """
    Parse /etc/default/grub into a GrubConfig object.
    Falls back to a mock config when the file does not exist.
    """
    config = GrubConfig(path=path)

    if not path.exists():
        config.is_mock = True
        config.raw_lines = _mock_grub_lines()
    else:
        config.raw_lines = path.read_text(encoding="utf-8").splitlines(keepends=True)

    for i, line in enumerate(config.raw_lines):
        m = _LINE_RE.match(line.rstrip())
        if not m:
            continue

        key = m.group("key")
        raw_value = m.group("value").strip()
        value = raw_value.strip('"') if raw_value.startswith('"') else raw_value
        commented = bool(m.group("comment"))

        entry = GrubEntry(
            key=key,
            value=value,
            raw_line=line,
            line_number=i,
            commented=commented,
        )
        if key not in config.entries or not commented:
            config.entries[key] = entry

    return config


# ── Writer ───────────────────────────────────────────────────────────────────

def write_grub_config(config: GrubConfig, new_values: dict) -> list:
    """
    Apply new_values to config.raw_lines and return the updated lines.
    Does NOT write to disk — caller handles that.
    """
    updated_lines = list(config.raw_lines)
    handled = set()

    for i, line in enumerate(updated_lines):
        m = _LINE_RE.match(line.rstrip())
        if not m:
            continue
        key = m.group("key")
        if key not in new_values:
            continue
        new_val = new_values[key]
        if new_val in ("true", "false") or new_val.lstrip("-").isdigit():
            updated_lines[i] = f'{key}={new_val}\n'
        else:
            updated_lines[i] = f'{key}="{new_val}"\n'
        handled.add(key)

    for key, value in new_values.items():
        if key not in handled:
            if value in ("true", "false") or value.lstrip("-").isdigit():
                updated_lines.append(f'{key}={value}\n')
            else:
                updated_lines.append(f'{key}="{value}"\n')

    return updated_lines


# ── Validation ───────────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def validate_changes(changes: dict) -> ValidationResult:
    """Validate a dict of proposed GRUB config changes."""
    result = ValidationResult(valid=True)

    for key, value in changes.items():
        if key == "GRUB_TIMEOUT":
            if not _is_int(value) or int(value) < -1:
                result.errors.append(
                    f"GRUB_TIMEOUT must be an integer >= -1 (got '{value}')"
                )
        elif key == "GRUB_DEFAULT":
            if not (value == "saved" or _is_non_negative_int(value)):
                result.errors.append(
                    f"GRUB_DEFAULT must be 'saved' or a non-negative integer (got '{value}')"
                )
        elif key == "GRUB_TIMEOUT_STYLE":
            if value not in ("menu", "countdown", "hidden"):
                result.errors.append(
                    f"GRUB_TIMEOUT_STYLE must be menu|countdown|hidden (got '{value}')"
                )
        elif key == "GRUB_GFXMODE":
            if value != "auto" and not re.match(r'^\d+x\d+(?:x\d+)?$', value):
                result.warnings.append(
                    f"GRUB_GFXMODE '{value}' is non-standard; verify your hardware supports it"
                )
        elif key in ("GRUB_DISABLE_OS_PROBER", "GRUB_DISABLE_SUBMENU", "GRUB_SAVEDEFAULT"):
            if value not in ("true", "false"):
                result.errors.append(
                    f"{key} must be 'true' or 'false' (got '{value}')"
                )
        elif key == "GRUB_THEME":
            if value and not Path(value).exists():
                result.warnings.append(
                    f"Theme path does not exist: {value}"
                )

    result.valid = len(result.errors) == 0
    return result


# ── grub-mkconfig ─────────────────────────────────────────────────────────────

def regenerate_grub(output_path: str = "/boot/grub/grub.cfg") -> tuple:
    """
    Run grub-mkconfig to regenerate grub.cfg.
    Returns (success: bool, output: str).
    Requires root privileges.
    """
    try:
        result = subprocess.run(
            ["grub-mkconfig", "-o", output_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except FileNotFoundError:
        return False, "grub-mkconfig not found. Is GRUB installed?"
    except subprocess.TimeoutExpired:
        return False, "grub-mkconfig timed out after 60 seconds."
    except Exception as e:
        return False, str(e)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_int(s: str) -> bool:
    try:
        int(s)
        return True
    except ValueError:
        return False


def _is_non_negative_int(s: str) -> bool:
    return _is_int(s) and int(s) >= 0


def _mock_grub_lines() -> list:
    """Return mock /etc/default/grub content for development and testing."""
    return [line + "\n" for line in """\
# GRUB boot loader configuration
# (Mock config — /etc/default/grub not found on this system)

GRUB_DEFAULT=0
GRUB_TIMEOUT=5
GRUB_TIMEOUT_STYLE=menu
GRUB_DISTRIBUTOR="Arch Linux"
GRUB_CMDLINE_LINUX_DEFAULT="quiet loglevel=3"
GRUB_CMDLINE_LINUX=""

#GRUB_TERMINAL_OUTPUT=gfxterm
GRUB_GFXMODE=auto
GRUB_GFXPAYLOAD_LINUX=keep

#GRUB_THEME=/boot/grub/themes/catppuccin-mocha/theme.txt

#GRUB_COLOR_NORMAL="light-blue/black"
#GRUB_COLOR_HIGHLIGHT="light-cyan/blue"

#GRUB_DISABLE_SUBMENU=y

GRUB_DISABLE_OS_PROBER=false""".splitlines()]