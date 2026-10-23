> ## 📦 grubForge has moved into the [Forge Suite](https://github.com/jetomev/forge-suite/tree/main/grubforge)
> Since **22 October 2026** grubForge lives in **[jetomev/forge-suite](https://github.com/jetomev/forge-suite)**, with its full history. New releases are tagged `grubforge-vX.Y.Z` there, and issues go there too (the open ones moved: #34 → [forge-suite#119](https://github.com/jetomev/forge-suite/issues/119), #35 → [#120](https://github.com/jetomev/forge-suite/issues/120)). This repository is archived: its releases (up to 2.2.2) and issues stay readable, and the AUR package `grubforge` keeps working. Thank you to everyone who starred it here.

# ⚡ grubForge

> The GRUB boot menu, without editing files by hand: every setting in plain words, picked from lists, reviewed before it's written, with a backup first.

> 🖥 **Where it runs:** **any major Linux distribution with GRUB** (Arch, Debian/Ubuntu, Fedora/RHEL, openSUSE…) · **no desktop needed**: any desktop, or none · **works on a plain text console** (a tty), saving included.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Version: 2.2.2](https://img.shields.io/badge/Version-2.2.2-purple.svg)
[![AUR](https://img.shields.io/aur/version/grubforge?v=2.2.2-1)](https://aur.archlinux.org/packages/grubforge)

> 🛡 **Security** — every release is GPG-signed and every commit is GitHub-Verified. **[Where We Stand](https://github.com/jetomev/KognogOS/blob/main/docs/where-we-stand.md)** covers our response to the 2026 AUR supply-chain attacks and how to check us yourself.

---

## Why grubForge?

GRUB is the first program your computer runs when you turn it on. Its job is to load your operating system, and if it breaks, your machine doesn't start.

Changing it has traditionally meant editing a configuration file as root, hoping you didn't make a typo, and running a command to rebuild the menu. One wrong character can leave you looking at a black screen.

**grubForge exists to change that.** It should be:

- **Safe**: a review of every change before it's written, a backup first, nothing installed or removed without asking
- **Clear**: every setting with a plain name and an explanation, and the GRUB name shown for those who want it
- **Easy**: known values are picked from lists; you type only names and unusual kernel options
- **Honest**: when something you saved isn't in the boot menu yet, or a setting is decided somewhere else, it says so

---

## Features

- 🏠 **Overview**: "is my boot menu all right?" in four boxes. Anything that needs attention comes with the button that fixes it.
- 🔧 **Settings**: every GRUB setting as a form, in five groups (Start-up, Look, Kernel options, Other systems, Advanced). Lists, worded On/Off switches, presets, a kernel-options checklist with an explanation per option, colours with a sample. "● changed" and "was: …" on each row you change.
- 🖥 **Boot Menu**: the menu as it shows at start-up. Move, rename, choose what starts first, remove, add an entry built from this computer (kernels, start-up images, disks, EFI loaders) and checked by GRUB's own checker, find other systems.
- 🎨 **Themes**: a preview of *your* entries in the theme's colours; install a downloaded theme safely.
- 🗂 **Backups**: why each was made, in plain words, and what restoring it would change, before you do.
- 💾 **Save and Rebuild, separately**: **F10** saves (review, backup, write); **F9** rebuilds the boot menu. "Saved · not in the boot menu yet" stays visible until you rebuild, and quitting asks first.
- 📖 **A manual inside the app** (**M**), and **F1** on anything opens its page. Since 2.2 the manual and the list of keys open in the main area, and **Esc** goes back.
- ⌨ **Every menu entry has a key** *(2.2)*: **1 – 6** in the order of the menu bar (Help is 6), or **Ctrl** + the underlined letter. Every button shows its own key in brackets, like **Save Changes (s)**.
- 🧩 **A page of hypeForge Settings** *(2.2)*: hypeForge's Settings window can show grubForge as one of its pages (see [Inside hypeForge Settings](#inside-hypeforge-settings)).
- 🖥 **Works on a plain text console**, where you end up when the desktop won't start: readable, and since 2.1 it can save there too.
- 🐧 **Every major distribution**: Arch, Debian/Ubuntu, Fedora/RHEL, openSUSE and more, each found automatically.
- 🔐 **Runs as you, not as root** *(2.1)*: when a change needs permission, grubForge asks for your password **in its own box** (on the desktop and on a text console alike), and polkit checks it. grubForge never runs as root; only its small helper does, for one fixed job at a time.
- 🌙 **Catppuccin Mocha**, on [forgekit](https://github.com/jetomev/forge-suite/tree/main/forgekit), the Forge Suite's shared base.

---

## Screenshots

### Overview
![Overview](screenshots/v2_overview.png)

### Settings
![Settings](screenshots/v2_settings.png)

### Boot Menu
![Boot Menu](screenshots/v2_boot_menu.png)

### Themes
![Themes](screenshots/v2_themes.png)

### Review before saving
![Review](screenshots/v2_review.png)

---

## Requirements

**Everything it needs** to build, run and test, with why, is in [docs/PACKAGING.md](docs/PACKAGING.md), measured from the code (the Forge Suite's [dependency audit](https://github.com/jetomev/forge-suite/issues/91), 2026-10-11).

- Linux with GRUB (any major distribution; see the table below): **GRUB itself** (`grub-mkconfig`, `grub-script-check`) — the AUR package depends on `grub`
- `os-prober` — optional, for other systems on the boot menu
- Python 3.10 or newer
- `python-textual`, `python-rich` and [`python-forgekit`](https://github.com/jetomev/forge-suite/tree/main/forgekit) 0.10.0 or newer (which also needs `python-pyte`)
- **`polkit`** and **`python-gobject`**: how grubForge asks for permission without running as root, with the password asked in its own box. Almost every desktop install already has both.

---

## Installation

### Arch Linux and KognogOS, from the AUR (recommended)

```bash
nog install grubforge      # KognogOS
yay -S grubforge           # any AUR helper
```

[aur.archlinux.org/packages/grubforge](https://aur.archlinux.org/packages/grubforge)

### Any other distribution

```bash
git clone https://github.com/jetomev/grubforge.git
cd grubforge
python3 -m venv .venv && .venv/bin/pip install textual rich pyte
git clone https://github.com/jetomev/forge-suite.git ../forge-suite
sudo sh install-helper.sh
PYTHONPATH=../forge-suite/forgekit .venv/bin/python main.py
```

`install-helper.sh` copies two files and nothing else: the helper to `/usr/lib/grubforge/` and the polkit rule to `/usr/share/polkit-1/actions/`, both owned by root. polkit only runs a helper installed at the exact path named in its policy. Without it grubForge still runs, read-only, and says so.

forgekit, the base grubForge is built on, lives in the [Forge Suite](https://github.com/jetomev/forge-suite) repository. A virtual environment is used because most current distributions refuse `pip install` into the system Python. If yours packages `textual`, `rich` and `pyte`, prefer those. The password box also needs your distribution's PyGObject package (`python3-gi` on Debian and Ubuntu); without it the password is asked the usual way.

### Where GRUB lives

grubForge finds these by itself and shows what it found on the Overview.

| Family | Examples | GRUB lives in | Rebuilt by | Tested in a VM |
|---|---|---|---|---|
| Arch | Arch, KognogOS, EndeavourOS, Manjaro | /boot/grub | grub-mkconfig | KognogOS |
| Debian | Debian, Ubuntu, Mint, Zorin | /boot/grub | grub-mkconfig | Debian 13, Ubuntu 24.04 |
| Fedora | Fedora, RHEL, Rocky, Alma | /boot/grub2 | grub2-mkconfig | Fedora 44 |
| openSUSE | Tumbleweed, Leap | /boot/grub2 | grub2-mkconfig | Tumbleweed |
| Others | Gentoo, Void… | /boot/grub | grub-mkconfig | — |

- **Debian and Ubuntu** also read `/etc/default/grub.d/*.cfg` after `/etc/default/grub`. A setting decided there is shown with its real value and file, locked, because changing it in the main file would have no effect.
- **Fedora-style systems** keep each Linux entry as its own file (`/boot/loader/entries`). grubForge shows them; you choose what starts first in Settings.
- **Systems that don't use GRUB** (Pop!_OS uses systemd-boot) open read-only, and grubForge says why.

---

## Usage

```bash
grubforge               # open grubForge
grubforge --version     # print the version
grubforge --help        # print the usage
```

**No `sudo`.** Run it as yourself. When a change needs permission, grubForge asks for your password in its own box, on the desktop and on a text console alike (since 2.1).

> **Why grubForge never runs as root.** Permission goes through **polkit**, the permission system your desktop already uses: polkit's own helper checks the password, and only grubForge's small, fixed helper runs as root. That helper accepts a short list of specific jobs. It can't be handed a command to run.

Over SSH, grubForge's polkit rule refuses permission, so run `sudo grubforge` there.

When grubForge closes, the terminal gets a short record: what you saved, whether the boot menu has it, the backup, where the run was logged (`~/.local/share/grubforge/logs/`), and a thank-you.

### Inside hypeForge Settings

hypeForge's Settings window can show grubForge as one of its pages. It starts grubForge as `grubforge --hypeforge` (any capitals work, `--hypeForge` too). Started that way, grubForge has **no Quit of its own**: Quit isn't in the menu bar, and Q and Ctrl+Q do nothing. Settings closes grubForge instead, and grubForge first asks the same question its own Quit asks when something isn't saved, or is saved but not in the boot menu yet. Your answer decides whether it closes. The option is for Settings, so `grubforge --help` doesn't list it.

---

## Keys

| Key | Does |
|---|---|
| Tab / Shift+Tab | next / previous field or button |
| Enter | open a list, press a button, confirm |
| Space | flip a switch, tick a box |
| Esc | close a window; leave a Help page (manual, Keys, About, License) |
| 1 – 6, or Ctrl + the underlined letter | Overview (O), Settings (S), Boot Menu (B), Themes (T), Backups (A), Help (6, H); 6 again closes Help |
| F10, or S | save, with a review first |
| F9, or Ctrl+R | rebuild the boot menu |
| R | read the files again |
| F1 | help on what is selected |
| M | the manual |
| ? | all keys |
| Q, or Ctrl+Q | quit (asks first if something isn't finished); not there inside hypeForge Settings |

In lists: **Shift+↑↓** moves an entry, **F2** renames, **+** adds, **F** finds other systems (Boot Menu); **I** installs a theme (Themes); **N / R / D** back up, restore, delete (Backups). Letter keys never act while you're typing in a field. A button shows its key in brackets after its name: **Save Changes (s)**, **Rebuild Boot Menu (F9)**, **Rename (F2)**.

The full manual is in [`grubforge/manual/`](grubforge/manual/), and inside the app with **M**.

---

## Safety

grubForge is built around one rule: **never break the bootloader.**

1. **Review**: before anything is written you see every change as old → new.
2. **Backup**: your settings, and your boot-order file, are saved first. The last 10 are kept in `/var/lib/grubforge/backups`.
3. **Permission**: polkit authorises the change. grubForge asks for the password in its own box (2.1) and polkit's own helper checks it; grubForge never sees whether it was right, and never runs as root.
4. **Rebuild when you choose**: what you save stays saved; the boot menu changes when you rebuild.

### The helper's fixed list of jobs

| Job | What it does |
|---|---|
| `write-config` | Save `/etc/default/grub` (only `KEY=value` lines) |
| `write-custom-40` | Save your boot order |
| `regenerate` | Rebuild the boot menu (grub-mkconfig or grub2-mkconfig, chosen by the helper itself) |
| `backup-create` / `-restore` / `-delete` | Manage backups (only grubForge's own backup names) |
| `script-enable` / `script-disable` | Turn the four GRUB scripts grubForge manages on and off |
| `os-prober-run` | Look for other operating systems |
| `read-entries` | Read the boot menu when grub.cfg is root-only (menu entries only, never a password hash) |
| `theme-install` | Install a theme: plain files and folders only, nothing reaching outside the theme's folder, size limits, `theme.txt` required, never overwrites |

**You can't hand the helper a command to run.** If you could, it would be a way to run anything as root, which is exactly what it exists to prevent.

### Your own boot order, and new kernels

Saving your own order writes the entries to `/etc/grub.d/40_custom` and turns off the scripts that made them, so your order stays. **Those scripts then no longer add new kernels by themselves.** After a kernel update, go **Back to the Original Order**, rebuild, and arrange again if you want. grubForge says this on the Overview, the Boot Menu screen and in Kernel options while your order is in use.

Entries made by other tools (btrfs snapshots, Debian's memtest) are **fixed**: their tool keeps placing them, and grubForge never copies them into your order, so they can't appear twice.

---

## How this project is built

grubForge is a human and AI collaboration, and we've written down how that works in practice.

📖 **[Building grubForge with AI](docs/AI-COLLABORATION.md)**, and the screen design that 2.0 was built from: [`docs/design/v2.0.0-screens.html`](docs/design/v2.0.0-screens.html). The `testing/` folder holds every test matrix, published on purpose.

---

## Roadmap

### Next

- [ ] **Write settings into `/etc/default/grub.d`** on Debian and Ubuntu, so settings decided there can be changed from grubForge too (today they're shown, locked, with the file to edit) ([#34](https://github.com/jetomev/grubforge/issues/34))
- [ ] **Fedora-style entries**: rename and reorder entries kept as separate files ([#35](https://github.com/jetomev/grubforge/issues/35))
- [ ] **Configurable preferences**: backup retention, theme folder

### Done

- [x] **v2.2.2**: the launcher entry ships with the package ([#37](https://github.com/jetomev/grubforge/issues/37))
- [x] **v2.2.1**: the AUR package builds on any machine; a reload reads the file it opened ([#41](https://github.com/jetomev/grubforge/issues/41))
- [x] Earlier releases: [docs/ROADMAP.md](docs/ROADMAP.md)

---

## Changelog

### v2.2.2 — October 22, 2026

**A launcher entry: grubForge shows in every app menu** ([#37](https://github.com/jetomev/grubforge/issues/37)).

- 🚀 **The launcher entry ships with the package**: `grubforge.desktop`, so the app shows in any desktop's app menu and launcher, opening in a terminal. Checked by `desktop-file-validate` in the tests and in the package's own check. hypeForge keeps its own copy for its floating window.
- 🔁 **Reproducible release files**: rebuilt from the tag, the tarball comes out byte for byte the same (every file dated the tag's commit time).
- 📖 The man page says the right version again (it still said 2.2.0 in 2.2.1).

Tests: 86 → **87**; warnings from grubForge's own code 0 → 0 (one from python-gobject's own code under Python 3.14 shows at 2.2.1 too on today's system). `desktop-file-utils` for the package's check.

### v2.2.1 — October 11, 2026

**The AUR package builds on any machine, and a reload always reads the file it opened** ([#41](https://github.com/jetomev/grubforge/issues/41), F-8). The Forge Suite's dependency audit built the 2.2.0 recipe in a clean Arch system and five tests failed there. Four came from a real slip: a reload of the settings read the system's own `/etc/default/grub` instead of the file the session was opened on. In everyday use they're the same file, so nothing looked wrong; the tests passed here only because this desktop's timeout matched theirs. The fifth needs GRUB's own checker, so the package now **depends on grub** (and suggests **os-prober** for other systems on the menu). What the package needs, with why: [docs/PACKAGING.md](docs/PACKAGING.md).

Tests: 108 → **111** (3 new: the package's needs list, a session reading its own file, GRUB's own check on its own; the session test fails on the old code). Warnings: 3 → 3 (no change).

*The complete history lives in [docs/CHANGELOG.md](docs/CHANGELOG.md).*

---

## Related Projects

- **[KognogOS](https://github.com/jetomev/KognogOS)**: the distribution grubForge ships with
- **[nog](https://github.com/jetomev/nog)**: tier-aware package manager
- **[forgekit](https://github.com/jetomev/forge-suite/tree/main/forgekit)**: the shared base for the Forge apps, in the [Forge Suite](https://github.com/jetomev/forge-suite)
- **[alacrittyForge](https://github.com/jetomev/alacrittyforge)**: terminal configurator
- **[bitlaForge](https://github.com/jetomev/bitlaforge)**: solo Bitcoin mining, honestly framed

---

## Authors

**jetomev**: idea, vision, direction, testing

**Claude (Anthropic)**: co-developer, architecture, implementation

Built as a collaboration between a human with a good idea and an AI that helped bring it to life. If you're curious how that works day to day: [Building grubForge with AI](docs/AI-COLLABORATION.md).

---

## License

grubForge is free software, released under the **GNU General Public License v3.0**. See [LICENSE](LICENSE).

---

## Contributing

Contributions are welcome: open an issue or a pull request.

Bug reports are genuinely valued here. Several releases exist because somebody outside the project took the time to write one.

If you find grubForge useful, a star helps others find it.
