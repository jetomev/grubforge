"""
grubForge — facts about the system we are actually running on.

Kept in one place because guessing them is how issue #27 happened. The boot
entry list labelled every kernel found by GRUB's 10_linux script as
"Arch Linux", which is only true on Arch. On Debian it told people their own
Debian entries came from Arch.

os-release is the same file GRUB itself reads to derive GRUB_DISTRIBUTOR, so
reading it here keeps grubForge and GRUB telling the user the same story.
"""

from pathlib import Path

# /etc wins over /usr/lib, per os-release(5): the distribution ships the
# second, and an administrator may override it with the first.
OS_RELEASE_PATHS = (Path("/etc/os-release"), Path("/usr/lib/os-release"))

# Used when os-release is missing or unreadable. Deliberately NOT a
# distribution name — inventing one is the bug this module exists to prevent.
UNKNOWN_SYSTEM = "This system"

_cached_name = None


def parse_os_release(text: str) -> dict:
    """Parse os-release format: KEY=value, one per line, values often quoted."""
    values = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value
    return values


def system_name(refresh: bool = False) -> str:
    """
    The name of this operating system — "Debian GNU/Linux", "Arch Linux".

    Falls back to UNKNOWN_SYSTEM rather than naming a distribution we have not
    actually confirmed. Cached, because it is read once per boot entry drawn.
    """
    global _cached_name
    if _cached_name is not None and not refresh:
        return _cached_name

    name = UNKNOWN_SYSTEM
    for path in OS_RELEASE_PATHS:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        candidate = (parse_os_release(text).get("NAME") or "").strip()
        if candidate:
            name = candidate
            break

    _cached_name = name
    return name
