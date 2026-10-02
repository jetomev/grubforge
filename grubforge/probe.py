"""What "Add an entry" reads from this computer, and the entries it builds (v2.0.0).

Nothing here needs root and nothing here writes: kernels and start-up images
are listed from /boot, disks from ``lsblk``, where /boot lives from
``findmnt``, other systems' loaders from the EFI partition. The built entry is
checked with GRUB's own ``grub-script-check`` before it can be added.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def kernels() -> list[str]:
    return sorted(Path(p).name for p in glob.glob("/boot/vmlinuz-*"))


def images() -> list[str]:
    found = glob.glob("/boot/initramfs-*.img") + glob.glob("/boot/initrd.img-*") + glob.glob("/boot/initrd-*")
    return sorted(Path(p).name for p in found)


def image_for(kernel: str, imgs: list[str]) -> str:
    """The start-up image that belongs to a kernel (not the fallback one)."""
    name = kernel.removeprefix("vmlinuz-")
    for cand in (f"initramfs-{name}.img", f"initrd.img-{name}", f"initrd-{name}"):
        if cand in imgs:
            return cand
    return imgs[0] if imgs else ""


@dataclass
class Disk:
    path: str
    uuid: str
    fstype: str
    label: str
    size: str
    mounts: list[str]
    esp: bool

    @property
    def describe(self) -> str:
        where = f" · {self.mounts[0]}" if self.mounts else ""
        name = f" · {self.label}" if self.label else ""
        return f"{Path(self.path).name}{name} · {self.fstype} · {self.size}{where}"


ESP_GUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"


def disks() -> list[Disk]:
    out = _run(["lsblk", "-J", "-o", "PATH,UUID,FSTYPE,LABEL,SIZE,MOUNTPOINTS,PARTTYPE"])
    try:
        data = json.loads(out)
    except ValueError:
        return []
    found: list[Disk] = []

    def walk(nodes):
        for n in nodes:
            if n.get("uuid") and n.get("fstype") and n.get("fstype") not in ("swap", "crypto_LUKS", "LVM2_member"):
                found.append(Disk(n["path"], n["uuid"], n["fstype"], n.get("label") or "", n.get("size") or "",
                                  [m for m in (n.get("mountpoints") or []) if m],
                                  (n.get("parttype") or "").lower() == ESP_GUID))
            walk(n.get("children") or [])
    walk(data.get("blockdevices") or [])
    return found


def mount_uuid(target: str) -> tuple[str, str]:
    """(uuid, fstype) of the filesystem holding ``target``."""
    out = _run(["findmnt", "-no", "UUID,FSTYPE,TARGET", "-T", target]).split()
    return (out[0], out[1]) if len(out) >= 2 else ("", "")


def boot_layout() -> tuple[str, str, str]:
    """(uuid of the filesystem holding /boot, its type, path prefix GRUB needs).

    When /boot is its own partition GRUB sees the kernels at /vmlinuz-…;
    when it is a folder on the system disk, at /boot/vmlinuz-…."""
    uuid, fstype = mount_uuid("/boot")
    out = _run(["findmnt", "-no", "TARGET", "-T", "/boot"]).strip()
    prefix = "" if out == "/boot" else "/boot"
    return uuid, fstype, prefix


def current_root_options() -> str:
    """root=/rootflags= as this system was started with, so a new entry for
    this system starts it the same way (btrfs subvolumes, encryption)."""
    try:
        cmdline = Path("/proc/cmdline").read_text().split()
    except OSError:
        return ""
    keep = [t for t in cmdline if t.startswith(("root=", "rootflags=", "cryptdevice=", "rd.luks", "resume="))]
    return " ".join(keep)


def esp_loaders() -> list[tuple[str, str]]:
    """(uuid, /EFI/…/loader.efi) for the EFI loaders on mounted EFI partitions."""
    out = []
    for d in disks():
        if not (d.esp or d.fstype == "vfat"):
            continue
        for m in d.mounts:
            for p in glob.glob(os.path.join(m, "EFI", "*", "*.[eE][fF][iI]")):
                rel = "/" + os.path.relpath(p, m)
                if "grub" in rel.lower() or rel.lower().endswith(("/mmx64.efi", "/fbx64.efi")):
                    continue
                out.append((d.uuid, rel))
    return sorted(set(out), key=lambda x: x[1])


def memtest_path() -> str:
    for p in ("/boot/memtest86+/memtest.efi", "/boot/memtest86+/memtest.bin", "/boot/memtest86+.efi",
              "/boot/memtest86+.bin", "/boot/memtest.efi"):
        if os.path.exists(p):
            return p
    return ""


def is_efi() -> bool:
    return os.path.isdir("/sys/firmware/efi")


def _q(title: str) -> str:
    """A title in single quotes, as grub-mkconfig writes them."""
    return "'" + title.replace("'", "'\\''") + "'"


def linux_entry(title: str, kernel: str, image: str, options: str) -> str:
    uuid, fstype, prefix = boot_layout()
    mod = {"ext4": "ext2", "ext3": "ext2", "ext2": "ext2", "vfat": "fat"}.get(fstype, fstype or "ext2")
    root = current_root_options() or f"root=UUID={mount_uuid('/')[0]}"
    lines = [f"menuentry {_q(title)} --class linux --class os {{",
             "    load_video", "    set gfxpayload=keep", "    insmod gzio", "    insmod part_gpt",
             f"    insmod {mod}",
             f"    search --no-floppy --fs-uuid --set=root {uuid}",
             f"    linux {prefix}/{kernel} {root} rw {options}".rstrip()]
    if image:
        lines.append(f"    initrd {prefix}/{image}")
    lines.append("}")
    return "\n".join(lines)


def chainload_entry(title: str, uuid: str, loader: str) -> str:
    return "\n".join([f"menuentry {_q(title)} --class os {{", "    insmod part_gpt", "    insmod fat",
                      f"    search --no-floppy --fs-uuid --set=root {uuid}", f"    chainloader {loader}", "}"])


def memtest_entry(title: str, path: str) -> str:
    uuid, fstype, prefix = boot_layout()
    rel = prefix + "/" + os.path.relpath(path, "/boot")
    cmd = "linux" if path.endswith(".efi") else "linux16"
    mod = {"ext4": "ext2"}.get(fstype, fstype or "ext2")
    return "\n".join([f"menuentry {_q(title)} --class memtest {{", f"    insmod {mod}",
                      f"    search --no-floppy --fs-uuid --set=root {uuid}", f"    {cmd} {rel}", "}"])


def firmware_entry(title: str) -> str:
    return "\n".join([f"menuentry {_q(title)} --class efi {{", "    fwsetup", "}"])


def empty_entry(title: str) -> str:
    # GRUB refuses an entry with no command in it, so the starting point has one
    return "\n".join([f"menuentry {_q(title)} {{", "    # replace this line with the commands for this entry",
                      "    echo 'Nothing here yet'", "}"])


def check_entry(block: str) -> str:
    """"" when GRUB's own checker accepts the entry, else its complaint.
    Without grub-script-check installed, only the braces are checked."""
    if not re.match(r"^\s*menuentry\s", block):
        return "an entry must start with menuentry"
    if block.count("{") != block.count("}"):
        return "the { and } don't match"
    tool = shutil.which("grub-script-check") or shutil.which("grub2-script-check")
    if not tool:
        return ""
    with tempfile.NamedTemporaryFile("w", suffix=".cfg", delete=False) as f:
        f.write(block + "\n")
        name = f.name
    try:
        r = subprocess.run([tool, name], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            return ""
        # the last line is the readable one ("Syntax error at line 2")
        text = (r.stderr.strip() or r.stdout.strip() or "GRUB rejects this entry").splitlines()
        return text[-1]
    finally:
        os.unlink(name)


def os_prober_install_hint(family: str) -> str:
    cmd = {"Arch": "nog install os-prober   (or: sudo pacman -S os-prober)",
           "Debian": "sudo apt install os-prober", "Fedora": "sudo dnf install os-prober",
           "openSUSE": "sudo zypper install os-prober", "Gentoo": "sudo emerge sys-boot/os-prober",
           "Void": "sudo xbps-install os-prober"}.get(family, "install os-prober with your package manager")
    return cmd


def bls_entries(folder: Path = Path("/boot/loader/entries")) -> list[tuple[str, str, str]]:
    """(id, title, version) for Fedora-style entry files, newest version first."""
    out = []
    for p in sorted(folder.glob("*.conf")):
        title = version = ""
        try:
            for line in p.read_text(errors="replace").splitlines():
                if line.startswith("title "):
                    title = line[6:].strip()
                elif line.startswith("version "):
                    version = line[8:].strip()
        except OSError:
            continue
        out.append((p.stem, title or p.stem, version))
    return sorted(out, key=lambda x: x[2], reverse=True)
