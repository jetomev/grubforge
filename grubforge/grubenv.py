"""Where GRUB lives on this computer, and what rebuilds it (v2.0.0, #24).

GRUB is the same program everywhere, but distributions keep its files in
different places and name its tools differently:

    Arch, Debian/Ubuntu, Gentoo, Void   /boot/grub    grub-mkconfig
    Fedora/RHEL, openSUSE               /boot/grub2   grub2-mkconfig

Fedora-style systems also keep their Linux entries as separate files under
``/boot/loader/entries`` (the Boot Loader Specification), switched on by
``GRUB_ENABLE_BLSCFG=true``; grub.cfg then holds a ``blscfg`` command instead
of the entries. Some systems do not start with GRUB at all (systemd-boot on
Pop!_OS); grubForge then says so and stays read-only.

``detect()`` reads all of this once; everything else asks the result.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .system import parse_os_release, OS_RELEASE_PATHS

GRUB_DEFAULT_FILE = Path("/etc/default/grub")
GRUB_D = Path("/etc/grub.d")
BLS_DIR = Path("/boot/loader/entries")
SYSTEMD_BOOT_MARKERS = (Path("/boot/loader/loader.conf"), Path("/efi/loader/loader.conf"),
                        Path("/boot/efi/loader/loader.conf"))

# family name → (os-release ids that belong to it)
FAMILIES = {
    "Arch": {"arch", "kognogos", "endeavouros", "manjaro", "cachyos", "garuda", "artix"},
    "Debian": {"debian", "ubuntu", "linuxmint", "pop", "zorin", "elementary", "kali", "raspbian", "mx"},
    "Fedora": {"fedora", "rhel", "centos", "rocky", "almalinux", "ol", "nobara"},
    "openSUSE": {"opensuse", "opensuse-tumbleweed", "opensuse-leap", "suse", "sles"},
    "Gentoo": {"gentoo", "funtoo"},
    "Void": {"void"},
}


@dataclass
class GrubEnv:
    family: str                 # "Arch", "Debian", "Fedora", "openSUSE", "Gentoo", "Void", "Other"
    distro: str                 # the system's own name, e.g. "KognogOS"
    uses_grub: bool
    grub_dir: Path              # /boot/grub or /boot/grub2
    grub_cfg: Path
    mkconfig: str               # "grub-mkconfig" or "grub2-mkconfig" (name, not path)
    bls: bool                   # entries kept as separate files (Fedora style)
    themes_dir: Path = field(default_factory=lambda: Path("/boot/grub/themes"))
    note: str = ""              # why grubForge is read-only, when uses_grub is False

    @property
    def summary(self) -> str:
        if not self.uses_grub:
            return self.note
        bls = " · entries as separate files" if self.bls else ""
        return f"{self.family} family · {self.grub_cfg} · {self.mkconfig}{bls}"


def family_of(os_release: dict) -> str:
    ids = {os_release.get("ID", "").lower()} | set(os_release.get("ID_LIKE", "").lower().split())
    for name, members in FAMILIES.items():
        if ids & members:
            return name
    return "Other"


def _read_default(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def bls_enabled(default_text: str, grub_cfg_text: str = "") -> bool:
    """BLS is on when /etc/default/grub says so, or grub.cfg calls blscfg."""
    for line in default_text.splitlines():
        s = line.strip()
        if s.startswith("GRUB_ENABLE_BLSCFG="):
            return s.split("=", 1)[1].strip().strip('"').lower() == "true"
    return "blscfg" in grub_cfg_text


def detect(root: Path = Path("/"), which=shutil.which) -> GrubEnv:
    """Read this computer. ``root`` and ``which`` are for tests."""
    def p(rel: str) -> Path:
        return root / rel.lstrip("/")

    os_release = {}
    for cand in OS_RELEASE_PATHS:
        f = p(str(cand))
        if f.is_file():
            os_release = parse_os_release(f.read_text(encoding="utf-8", errors="replace"))
            break
    family = family_of(os_release)
    distro = os_release.get("NAME", "This system")

    # grub2 first where the family uses it, so a stray /boot/grub left over
    # from an old install doesn't win
    order = ["boot/grub2", "boot/grub"] if family in ("Fedora", "openSUSE") else ["boot/grub", "boot/grub2"]
    grub_dir = next((p(d) for d in order if (p(d) / "grub.cfg").exists()), None)
    mk_name = "grub2-mkconfig" if which("grub2-mkconfig") and not which("grub-mkconfig") else "grub-mkconfig"
    if grub_dir is None:
        # no grub.cfg yet: trust the tool's name
        grub_dir = p("boot/grub2") if mk_name == "grub2-mkconfig" else p("boot/grub")
    cfg = grub_dir / "grub.cfg"

    has_tool = bool(which("grub-mkconfig") or which("grub2-mkconfig"))
    uses_grub = cfg.exists() or has_tool
    note = ""
    if not uses_grub:
        if any(p(str(m)).exists() for m in SYSTEMD_BOOT_MARKERS):
            note = ("This computer starts with systemd-boot, not GRUB. grubForge can only "
                    "show what it finds; nothing here would change how this computer starts.")
        else:
            note = ("GRUB isn't installed here (no grub.cfg and no grub-mkconfig), so there "
                    "is nothing for grubForge to change.")

    try:
        cfg_text = cfg.read_text(encoding="utf-8", errors="replace") if cfg.exists() else ""
    except OSError:          # root-only grub.cfg: the default file decides
        cfg_text = ""
    bls = bls_enabled(_read_default(p(str(GRUB_DEFAULT_FILE))), cfg_text) and p(str(BLS_DIR)).is_dir()

    return GrubEnv(family=family, distro=distro, uses_grub=uses_grub, grub_dir=grub_dir,
                   grub_cfg=cfg, mkconfig=mk_name, bls=bls, themes_dir=grub_dir / "themes", note=note)


def saved_but_not_rebuilt(env: GrubEnv, sources: tuple[Path, ...] = (GRUB_DEFAULT_FILE, GRUB_D / "40_custom")) -> bool:
    """True when a file GRUB reads changed after grub.cfg was last built.

    Read from the files' times, so it is right across restarts and for changes
    made outside grubForge (#17)."""
    try:
        built = env.grub_cfg.stat().st_mtime
    except OSError:
        return False
    for s in sources:
        try:
            if s.stat().st_mtime > built + 1:
                return True
        except OSError:
            continue
    return False
