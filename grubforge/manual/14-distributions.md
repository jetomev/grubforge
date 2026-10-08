# On other distributions

GRUB keeps its files in different places on different distributions. grubForge finds them by itself and says what it found on the Overview (**Safety ▸ GRUB / Menu file**).

| Family | Examples | GRUB lives in | Rebuilt by |
|---|---|---|---|
| Arch | Arch, KognogOS, EndeavourOS, Manjaro | /boot/grub | grub-mkconfig |
| Debian | Debian, Ubuntu, Mint, Zorin | /boot/grub | grub-mkconfig (what update-grub runs) |
| Fedora | Fedora, RHEL, Rocky, Alma | /boot/grub2 | grub2-mkconfig |
| openSUSE | Tumbleweed, Leap | /boot/grub2 | grub2-mkconfig |
| Others | Gentoo, Void… | /boot/grub | grub-mkconfig |

**Fedora-style systems** keep each Linux entry as its own file in `/boot/loader/entries`. grubForge shows them, and you choose what starts first in **Settings ▸ Start this entry**; their order follows the kernel versions.

**Systems that don't use GRUB** (Pop!_OS uses systemd-boot) open read-only, and grubForge says why.

On distributions other than Arch, the password helper is installed with `sudo sh install-helper.sh` from the source folder; without it, run grubForge with `sudo`.
