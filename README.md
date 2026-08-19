# ⚡ grubForge

> A terminal application for managing and customizing the GRUB bootloader on Linux — safely, clearly, and beautifully.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Version: 1.0.3](https://img.shields.io/badge/Version-1.0.3-purple.svg)
[![AUR](https://img.shields.io/aur/version/grubforge)](https://aur.archlinux.org/packages/grubforge)

> 🛡 **Security** — every release is GPG-signed and every commit is GitHub-Verified. **[Where We Stand](https://github.com/jetomev/KognogOS/blob/main/docs/where-we-stand.md)** covers our response to the 2026 AUR supply-chain attacks and how to check us yourself.

---

## Why grubForge?

GRUB is the first program your computer runs when you turn it on. Its job is to load your operating system — and if it breaks, your machine doesn't boot.

Changing it has traditionally meant opening a terminal, editing a configuration file as root, hoping you didn't make a typo, and running a command to compile your changes. There's no safety net. One wrong character can leave you looking at a black screen.

**grubForge exists to change that.** It should be:

- **Safe** — a backup before every change, and a confirmation before every action
- **Clear** — every setting explained in plain language, and checked before it's written
- **Good-looking** — a proper application, not a config screen from 1985
- **Approachable** — keyboard-driven, fast, and usable if you're not a bootloader expert

It came out of a simple frustration: why is one of the most critical parts of a Linux system also one of the least friendly to work with? It doesn't have to be.

---

## Features

- 🏠 **Dashboard** — what your GRUB setup currently looks like, and a live indicator that warns you when your boot menu is out of date with your settings
- 🔧 **Config Editor** — every GRUB setting with an explanation, checked as you type. Required and optional settings are distinguished, so optional ones can be cleared.
- 🎨 **Theme Browser** — browse the themes you have installed, preview their colours, apply one with a keystroke, and get help installing more
- 🖥 **Boot Entries** — reorder, rename, and create entries, find your other operating systems, save a custom order, and restore the original whenever you want
- 🗂 **Backup & Restore** — a timestamped backup before every change, kept to the 10 most recent, restorable from inside the app
- 🔄 **Rebuild the boot menu** in one keystroke after any change
- ⌨️ **Consistent keys** — Edit, Save, Apply, Refresh and Regenerate work from every screen. Screen-specific keys never clash with them.
- 🚦 **Read-only unless you elevate** — launch without `sudo` and you can explore everything safely. Nothing can be written until you have the rights to write it.
- 🌙 **Catppuccin Mocha** throughout

---

## Screenshots

### Dashboard
![Dashboard](screenshots/screenshot_dashboard.png)

### Config Editor
![Config Editor](screenshots/screenshot_config_editor.png)

### Theme Browser
![Theme Browser](screenshots/screenshot_themes.png)

### Backup & Restore
![Backup & Restore](screenshots/screenshot_backup.png)

### Boot Entries
![Boot Entries](screenshots/screenshot_boot_entries.png)

---

## Requirements

- Linux, with GRUB installed (developed and tested on Arch)
- Python 3.10 or newer
- `python-textual` and `python-rich`

---

## Installation

### Arch Linux, from the AUR (recommended)

```bash
yay -S grubforge
```

[aur.archlinux.org/packages/grubforge](https://aur.archlinux.org/packages/grubforge)

### Arch Linux, from source

```bash
sudo pacman -S python-textual python-rich
git clone https://github.com/jetomev/grubforge.git
cd grubforge
```

### Other distributions

```bash
pip install textual rich
git clone https://github.com/jetomev/grubforge.git
cd grubforge
```

---

## Usage

```bash
grubforge              # installed from the AUR
python main.py         # running from source
```

Run it normally and everything is browsable, but nothing can be saved — writing to GRUB's configuration needs root.

To make changes today, you have to start the whole application with `sudo`:

```bash
sudo grubforge
```

> **We're changing this.** Starting the entire application as root means every part of it — and every Python library it depends on — runs with full system privileges just to write one file. That's more power than the job needs.
>
> In **v1.1.0**, grubForge will stay unprivileged and ask for your password only at the moment a specific change needs it, through your desktop's own authentication dialog. See the [roadmap](#roadmap).

---

## Keybindings

Action keys work from every screen and do the right thing for whichever screen you're on. Screen-specific keys stay local and never clash. Pressing an action key on a screen that doesn't use it tells you so, rather than doing nothing.

### Anywhere

| Key | Action |
|-----|--------|
| `1`–`5` | Dashboard / Config Editor / Theme Browser / Backup & Restore / Boot Entries |
| `E` | Edit |
| `S` | Save |
| `A` | Apply |
| `R` | Refresh the current screen |
| `Ctrl+R` | Rebuild the boot menu |
| `?` | Help (`Esc` to close) |
| `q` | Quit |

### Backup & Restore

| Key | Action |
|-----|--------|
| `N` | Create a backup |
| `X` | Restore the selected backup |
| `D` | Delete the selected backup |

### Boot Entries

| Key | Action |
|-----|--------|
| `K` / `J` | Move the selected entry up / down |
| `N` | Rename it |
| `X` | Restore the original order |

### Theme Browser

| Key | Action |
|-----|--------|
| `H` | Show or hide the theme installation guide |

`F5` also refreshes on any screen.

---

## Project Structure

```
grubforge/
|-- main.py                      # Entry point
|-- grubforge.1                  # Man page
|-- grubforge/
|   |-- app.py                   # The application shell and key dispatch
|   |-- config_manager.py        # Reads, validates and writes GRUB settings
|   |-- backup_manager.py        # Create, list, restore and delete backups
|   |-- theme_manager.py         # Finds themes and reads their colours
|   |-- boot_entries_manager.py  # Boot entry parsing and reordering
|   |-- grubforge.css            # Catppuccin Mocha styling
|   |-- screens/                 # One file per screen
|   |-- widgets/                 # Shared components
|-- docs/                        # Changelog, and how this project is built
|-- screenshots/
|-- testing/                     # Test matrix, results and release checklist per version
|-- LICENSE
```

---

## Safety Philosophy

grubForge is built around one rule: **never break the bootloader.**

Every change passes three checks:

1. **Validation** — your input is checked before it's staged
2. **Confirmation** — a dialog asks before anything is written
3. **Backup** — your current configuration is saved automatically first

Backups live in `/var/lib/grubforge/backups` and can be restored from inside the app at any time.

When you reorder boot entries, grubForge switches off GRUB's auto-generating scripts rather than editing generated files directly. This is the same approach grub-customizer uses, and one keypress reverses it.

> **⚠️ Important: kernel updates while a custom order is saved.**
>
> While a custom boot order is active, GRUB's automatic entry generators are switched off. Any rebuild of the boot menu after that — **including the ones your system runs automatically when a kernel updates** — produces a menu *without* auto-detected Linux entries.
>
> In practice: new kernels won't appear in your boot menu until you press **Restore Original** in the Boot Entries screen, or add them yourself as custom entries.
>
> If your system installs kernel updates regularly, it's safer to leave grubForge in default-order mode and only save a custom order when you actually need one.

---

## How this project is built

grubForge is a human and AI collaboration, and we've written down how that actually works in practice — including how we keep an AI collaborator reliable when its memory gets compacted mid-project.

📖 **[Building grubForge with AI](docs/AI-COLLABORATION.md)** — the honest answer, and the reason the `testing/` folder is published rather than hidden.

---

## Roadmap

### Next — v1.1.0: ask for permission properly ([#18](https://github.com/jetomev/grubforge/issues/18))

- [ ] **Stop requiring `sudo` for the whole application.** Today the only way to save anything is to launch the entire program as root, so grubForge and every library it depends on run with full system privileges in order to write one file.

  In v1.1.0 grubForge runs as your own user. The handful of actions that genuinely need root — writing the config, rebuilding the boot menu, managing backups, installing a theme, toggling OS detection — are each authorised individually through **polkit**, at the moment you trigger them. You get your desktop's own password dialog and enter *your* password, not root's.

  We chose polkit over showing our own password box on purpose: if grubForge collected your password itself, grubForge would be holding it in memory. This way the prompt belongs to the system, and the application never sees it.

  *Reported by [@marco-gallegos](https://github.com/marco-gallegos). Targeting 28 August 2026.*

### After that

- [ ] **Warn when boot entries are frozen** ([#19](https://github.com/jetomev/grubforge/issues/19)) — while a custom boot order is saved, some settings in the Config Editor silently have no effect. grubForge should say so, and offer to apply them to the frozen entries or unfreeze. Also: make saving and rebuilding behave consistently across screens.
- [ ] **Document what happens when the config changes outside the app** ([#17](https://github.com/jetomev/grubforge/issues/17))
- [ ] **Rebuild on [forgekit](https://github.com/jetomev/forgekit)** — the shared foundation the other Forge apps now use
- [ ] **A layout pass for small terminals** — Boot Entries, Config Editor and Theme Browser get cramped
- [ ] **Configurable preferences** — backup retention, theme paths, and similar

### Done

- [x] **v1.0.3** — UX batch closing 15 findings from the v1.0.1 retest
- [x] **v1.0.2** — Textual 8.x compatibility, unblocking anyone on a rolling distribution
- [x] **v1.0.1** — backup retention cap, boot-menu sync indicator, read-only indicator, consistent key bindings
- [x] **v1.0** — the full application: dashboard, config editor with validation, theme browser, boot entry management, OS detection, automatic backups, boot menu rebuilding, man page, and AUR packaging

---

## Changelog

### v1.0.3 — May 27, 2026

**A UX batch closing all 15 findings from the v1.0.1 retest.**

- 🔄 **Screens refresh themselves.** Every screen now re-reads from disk when you open it, so a save, a new backup or an applied theme shows up without a manual refresh. The Dashboard gained a distinct yellow "pending changes" state, separate from "your boot menu is older than your settings" and "everything is in sync".
- 🧭 **Rebuilding works from anywhere.** `Ctrl+R` regenerates the boot menu from any screen, not just the Config Editor — so the old "go to the Config Editor and press Ctrl+R" instructions are gone.
- 💬 **One consistent way of talking to you.** All feedback now goes through a single channel — a status line plus a toast — replacing five near-identical per-screen versions with their own inconsistent icons.
- 🐛 **Widget fixes.** The read-only badge renders again, `?` opens a real help window instead of stacking toasts, the backup preview scrolls, `E` selects the first setting if none is chosen, and screen keys work on entry without needing a click first.

No dependency or install changes.

### v1.0.2 — May 26, 2026

**A blocker fix: compatibility with Textual 8.x.**

Fixes [issue #1](https://github.com/jetomev/grubforge/issues/1), filed by `@jfp42`. grubForge crashed on startup with `AttributeError: type object 'Static' has no attribute 'Clicked'`. Textual had removed that event type between the version grubForge was written against and 8.2.7 — so every install on a rolling distribution broke the moment Textual updated.

```python
# Before (broken on Textual ≥ 8.2.7):
def on_static_click(self, event: Static.Clicked) -> None:

# After (works on both):
def on_click(self, event: events.Click) -> None:
```

`events.Click` is the underlying event the removed one was built on, so behaviour is identical.

Also added: a build-time import check in the AUR package, so we can never again ship a version that won't start.

**Credit:** this release exists because `@jfp42` filed a detailed report from a Debian Sid install. Thank you.

*The complete history lives in [docs/CHANGELOG.md](docs/CHANGELOG.md).*

---

## Related Projects

- **[KognogOS](https://github.com/jetomev/KognogOS)** — the distribution grubForge ships with
- **[nog](https://github.com/jetomev/nog)** — tier-aware package manager
- **[forgekit](https://github.com/jetomev/forgekit)** — the shared foundation for the Forge apps
- **[alacrittyForge](https://github.com/jetomev/alacrittyforge)** — terminal configurator
- **[bitlaForge](https://github.com/jetomev/bitlaforge)** — solo Bitcoin mining, honestly framed

---

## Authors

**jetomev** — idea, vision, direction, testing

**Claude (Anthropic)** — co-developer, architecture, implementation

Built as a collaboration between a human with a good idea and an AI that helped bring it to life — one command at a time. If you're curious how that works day to day, we wrote it down: [Building grubForge with AI](docs/AI-COLLABORATION.md).

---

## License

grubForge is free software, released under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for the full text.

---

## Contributing

Contributions are welcome — open an issue or a pull request.

Bug reports are genuinely valued here. Two of the releases above exist because somebody outside the project took the time to write one.

If you find grubForge useful, a star helps others find it.
