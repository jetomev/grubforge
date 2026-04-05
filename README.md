# ⚡ GrubForge

> A terminal UI application for managing and customizing the GRUB bootloader on Linux — safely, intuitively, and beautifully.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Version: 0.9.0](https://img.shields.io/badge/Version-0.9.0-purple.svg)

---

## Why GrubForge?

GRUB is the first program your computer runs after powering on. It is responsible for loading your operating system — and if it breaks, your machine won't boot. Editing it has traditionally meant opening a terminal, manually editing a configuration file as root, hoping you didn't make a typo, and running a command to compile the changes.

There is no safety net. One wrong character can leave you staring at a black screen.

**GrubForge exists to change that.**

We believe managing your bootloader should be:
- **Safe** — automatic backups before every change, confirm dialogs before every action
- **Clear** — every setting explained in plain language, live validation before anything is written
- **Beautiful** — a Catppuccin Mocha themed TUI that feels like a proper application, not a 1980s config screen
- **Accessible** — keyboard-driven, fast, and usable by people who are not bootloader experts

GrubForge was born from a simple frustration: why is one of the most critical pieces of your Linux system also one of the most unfriendly to interact with? It doesn't have to be.

---

## Features

- 🏠 **Dashboard** — system overview showing GRUB config status, active settings, and backup count
- 🔧 **Config Editor** — view and edit all GRUB settings with descriptions and live validation
- 🎨 **Theme Browser** — browse locally installed GRUB themes, preview color palettes, apply with one key, and get guided help on installing new themes
- 🖥 **Boot Entries** — reorder, rename, and create custom boot entries, detect other OSes via os-prober, save a custom order, and restore the original at any time
- 🗂 **Backup & Restore** — timestamped backups created automatically before every change
- 🔄 **grub-mkconfig** — regenerate your boot menu in one keystroke after any change
- 🌙 **Catppuccin Mocha** — a beautiful, consistent dark theme throughout

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

- Linux (developed and tested on Arch Linux)
- Python 3.10 or newer
- GRUB bootloader installed
- `python-textual` and `python-rich`

---

## Installation

### Arch Linux (recommended)
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
cd grubforge
sudo python main.py
```

> `sudo` is required to write to `/etc/default/grub`, manage `/etc/grub.d/` scripts, and run `grub-mkconfig`.
> You can run without `sudo` to explore the app safely in read-only demo mode.

---

## Keybindings

### Global

| Key | Action |
|-----|--------|
| `1` | Dashboard |
| `2` | Config Editor |
| `3` | Theme Browser |
| `4` | Backup & Restore |
| `5` | Boot Entries |
| `?` | Help |
| `q` | Quit |

### Config Editor

| Key | Action |
|-----|--------|
| `E` | Edit selected value |
| `S` | Save all pending changes |
| `R` | Refresh from disk |
| `Ctrl+R` | Regenerate grub.cfg |

### Theme Browser

| Key | Action |
|-----|--------|
| `A` | Apply selected theme |
| `F5` | Refresh theme list |

### Boot Entries

| Key | Action |
|-----|--------|
| `K` | Move entry up |
| `J` | Move entry down |
| `S` | Save custom order |
| `R` | Restore original order |
| `F5` | Refresh |

### Backup & Restore

| Key | Action |
|-----|--------|
| `B` | Create new backup |
| `R` | Restore selected backup |
| `D` | Delete selected backup |
| `F5` | Refresh |

---

## Project Structure

```
grubforge/
|-- main.py                      # Entry point
|-- grubforge/
    |-- app.py                   # Main Textual application shell
    |-- config_manager.py        # GRUB config parser, writer, validator
    |-- backup_manager.py        # Backup create, list, restore, delete
    |-- theme_manager.py         # Theme scanner, parser, color extractor
    |-- boot_entries_manager.py  # Boot entry parser, reorder, grub.d manager
    |-- grubforge.css            # Catppuccin Mocha stylesheet
    |-- screens/
    |   |-- dashboard.py         # System overview screen
    |   |-- config_editor.py     # Config editor screen
    |   |-- themes.py            # Theme browser screen
    |   |-- boot_entries.py      # Boot entries screen
    |   |-- backup.py            # Backup & restore screen
    |-- widgets/
        |-- confirm_dialog.py    # Reusable confirmation dialog
```

---

## Safety Philosophy

GrubForge is built around one principle: **never break the bootloader**.

Every change goes through three layers of protection:

1. **Validation** — your input is checked before it is staged
2. **Confirmation** — a dialog asks you to confirm before anything is written
3. **Backup** — a timestamped backup of your current config is created automatically before every write

Backups are stored in `/var/lib/grubforge/backups` and can be restored from within the app at any time.

When reordering boot entries, GrubForge disables the auto-generate scripts in `/etc/grub.d/` rather than editing generated files directly. This is the same approach used by grub-customizer and is fully reversible with one button press.

---

## Roadmap

- [x] Dashboard with system overview
- [x] Config editor with live validation
- [x] Automatic backup and restore
- [x] grub-mkconfig integration
- [x] Theme browser with help guide
- [x] Boot entry reordering
- [x] Boot entry renaming
- [x] Custom boot entry creation
- [x] OS detection and os-prober integration
- [x] Screenshots in README
- [x] Man page
- [ ] Packaged installer (AUR)

---

## Changelog

### v0.9.0 — April 4, 2026
**Man Page**
- 📖 **Man page added** — `grubforge.1` included in the repository
- Documents all 5 screens, all keybindings, and all managed file paths
- Built-in SEE ALSO references to `grub-mkconfig`, `grub-install`, `os-prober`
- Test locally with: `man ./grubforge.1`

### v0.8.0 — April 4, 2026
**Screenshots**
- 📸 **Screenshots added to README** — all five screens captured and published
  - Dashboard
  - Config Editor
  - Theme Browser
  - Backup & Restore
  - Boot Entries

### v0.7.0 — April 4, 2026
**Theme Browser Help Guide**
- Press H in the Theme Browser to open the installation guide
- Explains exactly where to save themes (/boot/grub/themes/)
- Shows correct folder structure with examples
- Step by step installation instructions
- Curated list of recommended theme sources with URLs
- Tips on required GRUB settings for themes to display correctly
- Press H again or select a theme to close the help

### v0.6.0 — April 4, 2026
**OS Detection**
- Detect other operating systems installed on your drives directly from Boot Entries
- Checks if os-prober is installed and enabled automatically on screen load
- Install os-prober via pacman with one click if missing
- Enable os-prober in /etc/default/grub with automatic backup
- Scan button runs os-prober and displays all detected OSes with device and type info
- Works seamlessly with existing grub-mkconfig regeneration flow

### v0.5.0 — April 4, 2026
**Custom Boot Entry Creation**
- ➕ Add custom boot entries directly from the Boot Entries screen
- 📋 Four built-in templates: Linux, Chainload, Memtest, Blank
- ✏ Raw block editor — full control over the menuentry commands
- 👁 Preview Template button fills the editor with a named template
- ✅ Custom entries are added to the list and saved with the same flow as reordering

### v0.4.0 — April 3, 2026
**Boot Entry Renaming**
- ✏ Rename any boot entry directly from the Boot Entries screen
- 🔄 Rename input pre-fills with the current entry name when selected
- ✅ Renamed entries preserved correctly when saving custom order
- 🔒 Only the display name changes — all boot commands stay identical

### v0.3.0 — April 2, 2026
**Boot Entries Manager**
- 🖥 View all GRUB boot entries parsed from `/boot/grub/grub.cfg`
- ↕ Reorder entries with K/J keys or Move Up/Down buttons
- 💾 Save custom order to `/etc/grub.d/40_custom`
- ↺ Restore original auto-generated order with one button
- 🔧 Script status panel showing which `/etc/grub.d/` scripts are enabled
- 🎨 Color coded entries by source (Arch Linux, OS Prober, UEFI, BTRFS Snapshots)

### v0.2.0 — April 2, 2026
**Theme Browser**
- 🎨 Automatically scan `/boot/grub/themes/` for installed themes
- 🎨 Color palette preview with visual swatches from each theme
- 📄 Syntax highlighted `theme.txt` preview
- ✓ One-click apply with automatic backup before writing
- 🟢 Active theme indicator
- 🔧 Fixed graphical terminal settings for themes to display correctly

### v0.1.0 — April 1, 2026
**Initial Release**
- 🏠 Dashboard with system overview
- 🔧 Config Editor with live validation for all 17 GRUB settings
- 🗂 Automatic backup and restore with timestamped backups
- 🔄 grub-mkconfig integration — regenerate boot menu in one keystroke
- 🌙 Catppuccin Mocha theme throughout

---

## Authors

**jetomev** — idea, vision, direction, testing

**Claude (Anthropic)** — co-developer, architecture, implementation

This project was built as a collaboration between a human with a great idea and an AI that helped bring it to life — one command at a time.

---

## License

GrubForge is free software: you can redistribute it and/or modify it under the terms of the **GNU General Public License v3.0** as published by the Free Software Foundation.

See [LICENSE](LICENSE) for the full license text.

---

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

If you find GrubForge useful, consider starring the repository — it helps others find it.