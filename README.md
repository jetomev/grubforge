# ⚡ GrubForge

> A terminal UI application for managing and customizing the GRUB bootloader on Linux — safely, intuitively, and beautifully.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)

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

- 🔧 **Config Editor** — view and edit all GRUB settings with descriptions and live validation
- 🗂 **Backup & Restore** — timestamped backups created automatically before every change
- 🎨 **Theme Browser** — browse, preview, and apply GRUB themes *(coming soon)*
- 📦 **Theme Downloader** — download themes from a curated list *(coming soon)*
- 🔄 **grub-mkconfig** — regenerate your boot menu in one keystroke
- 🌙 **Catppuccin Mocha** — a beautiful, consistent dark theme throughout

---

## Screenshots

*Coming soon*

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

> `sudo` is required to write to `/etc/default/grub` and run `grub-mkconfig`.
> You can run without `sudo` to explore the app safely in read-only demo mode.

---

## Keybindings

| Key | Action |
|-----|--------|
| `1` | Dashboard |
| `2` | Config Editor |
| `3` | Theme Browser |
| `4` | Backup & Restore |
| `E` | Edit selected value |
| `S` | Save all pending changes |
| `R` | Refresh from disk |
| `Ctrl+R` | Regenerate grub.cfg |
| `B` | Create new backup |
| `D` | Delete selected backup |
| `?` | Help |
| `q` | Quit |

---

## Project Structure
```
grubforge/
├── main.py                          # Entry point
└── grubforge/
    ├── app.py                       # Main Textual application shell
    ├── config_manager.py            # GRUB config parser, writer, validator
    ├── backup_manager.py            # Backup create, list, restore, delete
    ├── grubforge.css                # Catppuccin Mocha stylesheet
    ├── screens/
    │   ├── dashboard.py             # System overview screen
    │   ├── config_editor.py         # Config editor screen
    │   ├── backup.py                # Backup & restore screen
    │   └── themes.py                # Theme browser (coming soon)
    └── widgets/
        └── confirm_dialog.py        # Reusable confirmation dialog
```

---

## Safety Philosophy

GrubForge is built around one principle: **never break the bootloader**.

Every change goes through three layers of protection:

1. **Validation** — your input is checked before it is staged
2. **Confirmation** — a dialog asks you to confirm before anything is written
3. **Backup** — a timestamped backup of your current config is created automatically before every write

Backups are stored in `/var/lib/grubforge/backups` and can be restored from within the app at any time.

---

## Roadmap

- [x] Config editor with live validation
- [x] Automatic backup and restore
- [x] grub-mkconfig integration
- [ ] Theme browser (local themes)
- [ ] Theme downloader (curated list)
- [ ] Boot entry viewer
- [ ] Packaged installer (AUR / pip)
- [ ] Man page

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