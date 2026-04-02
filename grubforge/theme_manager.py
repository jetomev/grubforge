"""
GrubForge — Theme Manager
Scans /boot/grub/themes/, parses theme.txt files, and extracts color information.
"""

import re
from pathlib import Path
from dataclasses import dataclass, field


# ── Constants ─────────────────────────────────────────────────────────────────

THEMES_DIR = Path("/boot/grub/themes")


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class GrubTheme:
    """Represents a single installed GRUB theme."""
    name:             str
    path:             Path
    theme_txt:        Path
    colors:           dict = field(default_factory=dict)
    fonts:            list = field(default_factory=list)
    has_background:   bool = False
    background_file:  str  = ""
    raw_txt:          str  = ""

    @property
    def is_active(self) -> bool:
        """Check if this theme is currently set in /etc/default/grub."""
        from grubforge.config_manager import GRUB_CONFIG_PATH, parse_grub_config
        try:
            config = parse_grub_config(GRUB_CONFIG_PATH)
            entry  = config.entries.get("GRUB_THEME")
            if not entry or not entry.value:
                return False
            return str(self.theme_txt) in entry.value or self.name in entry.value
        except Exception:
            return False


# ── Core functions ────────────────────────────────────────────────────────────

def list_themes() -> list:
    """
    Scan THEMES_DIR and return all valid GRUB themes found.
    A valid theme is a subdirectory containing a theme.txt file.
    Returns an empty list if the directory does not exist.
    """
    if not THEMES_DIR.exists():
        return []

    themes = []
    for entry in sorted(THEMES_DIR.iterdir()):
        if not entry.is_dir():
            continue
        theme_txt = entry / "theme.txt"
        if not theme_txt.exists():
            continue
        theme = _parse_theme(entry, theme_txt)
        themes.append(theme)

    return themes


def _parse_theme(theme_dir: Path, theme_txt: Path) -> GrubTheme:
    """Parse a theme.txt file and extract colors, fonts, background."""
    theme = GrubTheme(
        name      = theme_dir.name,
        path      = theme_dir,
        theme_txt = theme_txt,
    )

    try:
        raw = theme_txt.read_text(encoding="utf-8", errors="replace")
        theme.raw_txt = raw

        for line in raw.splitlines():
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Extract color values — lines like: message-color: "#fff"
            color_match = re.match(
                r'^([\w-]*color[\w-]*)\s*[=:]\s*"?([#\w]+)"?', line, re.IGNORECASE
            )
            if color_match:
                key   = color_match.group(1).strip()
                value = color_match.group(2).strip()
                theme.colors[key] = _normalize_color(value)

            # Extract fonts
            font_match = re.match(r'^[\w-]*font[\w-]*\s*[=:]\s*"([^"]+)"', line, re.IGNORECASE)
            if font_match:
                font = font_match.group(1).strip()
                if font not in theme.fonts:
                    theme.fonts.append(font)

            # Extract background image
            bg_match = re.match(r'^desktop-image\s*[=:]\s*"([^"]+)"', line, re.IGNORECASE)
            if bg_match:
                theme.background_file = bg_match.group(1).strip()
                bg_path = theme_dir / theme.background_file
                theme.has_background  = bg_path.exists()

    except Exception:
        pass  # Return partially parsed theme on error

    return theme


def _normalize_color(color: str) -> str:
    """
    Normalize a color value to 6-digit hex.
    Handles: #fff → #ffffff, #abc123 → #abc123, named colors → fallback.
    """
    color = color.strip().lstrip("#")

    # 3-digit hex → 6-digit
    if len(color) == 3:
        color = "".join(c * 2 for c in color)

    # Validate it's a hex color
    try:
        int(color, 16)
        return f"#{color.lower()}"
    except ValueError:
        return "#888888"  # fallback for named colors


def apply_theme(theme: GrubTheme) -> None:
    """
    Write GRUB_THEME to /etc/default/grub pointing to this theme.
    Caller must have write permission (run as root).
    Creates a backup before writing.
    """
    from grubforge.config_manager import GRUB_CONFIG_PATH, parse_grub_config, write_grub_config
    from grubforge.backup_manager import create_backup

    create_backup(label=f"pre-theme-{theme.name}")

    config    = parse_grub_config(GRUB_CONFIG_PATH)
    new_lines = write_grub_config(config, {"GRUB_THEME": str(theme.theme_txt)})

    if GRUB_CONFIG_PATH.exists():
        GRUB_CONFIG_PATH.write_text("".join(new_lines), encoding="utf-8")


def get_color_palette(theme: GrubTheme) -> list:
    """
    Return a list of (label, hex_color) tuples for display.
    Picks the most interesting colors from the theme.
    """
    priority_keys = [
        "message-color",
        "message-bg-color",
        "item_color",
        "selected_item_color",
        "text_color",
        "fg_color",
        "bg_color",
        "border_color",
    ]

    palette = []
    seen    = set()

    # Add priority keys first
    for key in priority_keys:
        if key in theme.colors:
            color = theme.colors[key]
            if color not in seen:
                palette.append((key, color))
                seen.add(color)

    # Add any remaining colors
    for key, color in theme.colors.items():
        if color not in seen:
            palette.append((key, color))
            seen.add(color)

    return palette