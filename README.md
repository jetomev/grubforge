# ⚡ grubForge

> A terminal application for managing and customizing the GRUB bootloader on Linux — safely, clearly, and beautifully.

![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)
![Platform: Linux](https://img.shields.io/badge/Platform-Linux-lightgrey.svg)
![Python: 3.10+](https://img.shields.io/badge/Python-3.10+-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Version: 1.1.0](https://img.shields.io/badge/Version-1.1.0-purple.svg)
[![AUR](https://img.shields.io/aur/version/grubforge?v=1.1.0)](https://aur.archlinux.org/packages/grubforge)

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
- 🔐 **Runs as you, not as root** — grubForge never needs `sudo`. When a change genuinely needs permission, your desktop asks for your password and grubForge never sees it.
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
- **`polkit`** — how grubForge asks for permission without running as root. Almost every desktop Linux install already has it.

---

## Installation

### Arch Linux, from the AUR (recommended)

```bash
yay -S grubforge
```

[aur.archlinux.org/packages/grubforge](https://aur.archlinux.org/packages/grubforge)

### Arch Linux, from source

```bash
sudo pacman -S python-textual python-rich polkit
git clone https://github.com/jetomev/grubforge.git
cd grubforge
```

Running from a clone, grubForge is read-only: the privileged helper has to be
installed system-wide before polkit will run it. Install the package, or use
`sudo python main.py` while developing.

### Other distributions

```bash
pip install textual rich
git clone https://github.com/jetomev/grubforge.git
cd grubforge
```

You'll also want `polkit` from your distribution's packages. Without it grubForge
still runs, but read-only — and it says so rather than failing silently.

---

## Usage

```bash
grubforge              # installed from the AUR
python main.py         # running from source
```

**No `sudo`.** Run it as yourself.

grubForge browses and edits everything as your normal user. The moment you do something that actually changes the bootloader — saving a setting, applying a theme, rebuilding the boot menu — your desktop shows its own password dialog, you type **your** password, and the change goes through.

Confirmation dialogs tell you in advance when a password is coming, so it never arrives as a surprise.

> **Why grubForge doesn't ask for your password itself.**
>
> If the application collected your password, the application would be holding your password — in the memory of a Python program with a stack of third-party libraries behind it. Instead we use **polkit**, the permission system your desktop already uses. The prompt belongs to the system. grubForge never sees, stores, or forwards what you type.
>
> Only a small, fixed helper runs as root, and it accepts a short list of specific jobs. It cannot be handed a command to run.
>
> *Changed in v1.1.0, after [#18](https://github.com/jetomev/grubforge/issues/18).*

`sudo grubforge` still works if you prefer it, and skips the prompts entirely.

On a machine with no desktop session — over SSH, or a plain text console — `sudo` is the way to make changes, because there's no window a password dialog could appear in. If you try without it, grubForge says exactly that and points you at `sudo`, rather than leaving you with polkit's rather alarming *"Not authorized. This incident has been reported."*

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
|   |-- privilege.py             # The one place grubForge asks for permission
|   |-- config_manager.py        # Reads, validates and writes GRUB settings
|   |-- backup_manager.py        # Create, list, restore and delete backups
|   |-- theme_manager.py         # Finds themes and reads their colours
|   |-- boot_entries_manager.py  # Boot entry parsing and reordering
|   |-- grubforge.css            # Catppuccin Mocha styling
|   |-- screens/                 # One file per screen
|   |-- widgets/                 # Shared components
|-- helper/
|   |-- grubforge-helper         # The only part that runs as root
|-- polkit/
|   |-- org.kognogos.grubforge.policy   # What permission is asked for, and how
|-- docs/                        # Changelog, and how this project is built
|-- screenshots/
|-- testing/                     # Test matrix, results and release checklist per version
|-- LICENSE
```

---

## Safety Philosophy

grubForge is built around one rule: **never break the bootloader.**

Every change passes four checks:

1. **Validation** — your input is checked before it's staged
2. **Confirmation** — a dialog asks before anything is written
3. **Backup** — your current configuration is saved automatically first
4. **Permission** — the change is authorised by polkit, one action at a time

Backups live in `/var/lib/grubforge/backups` and can be restored from inside the app at any time.

### How permission works

grubForge runs as your user. It cannot write to `/etc` or `/boot` at all — it doesn't have the rights, and doesn't ask for them up front.

When you make a change, it hands the job to a small helper that runs as root, and **polkit** decides whether that's allowed. Your desktop draws the password dialog. grubForge never touches your password.

The helper accepts a **fixed list of jobs** and nothing else:

| Job | What it does |
|-----|--------------|
| `write-config` | Save `/etc/default/grub` |
| `write-custom-40` | Save your custom boot order |
| `regenerate` | Rebuild the boot menu |
| `backup-create` / `-restore` / `-delete` | Manage backups |
| `script-enable` / `script-disable` | Turn GRUB's generator scripts on and off |
| `os-prober-run` | Scan for other operating systems |

That list is the point. **You cannot hand the helper a command to run** — if you could, it would be a way to run anything as root, which is exactly what it exists to prevent. It also re-checks everything it's given: settings files must contain only `KEY=value` lines, backup names must match the exact pattern grubForge generates, and only the four GRUB scripts it manages can be touched, by name.

Once you authenticate, polkit remembers for a few minutes, so saving a change and rebuilding the boot menu asks once rather than twice. Being asked repeatedly for one task is how people learn to type their password without reading the dialog.

> **grubForge no longer installs packages for you.** It used to offer to install `os-prober` by running `pacman` as root. Installing software is a much wider power than editing a bootloader config, and it belongs to your package manager. grubForge now shows you the command and you run it.

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

### Next — v2.0.0: rebuild on forgekit

- [ ] **Move onto [forgekit](https://github.com/jetomev/forgekit)**, the shared foundation the other Forge apps already use. grubForge is the last one still carrying its own hand-built menus, dialogs and styling — several hundred lines that exist in one form here and a better form in the shared library.

  It also brings grubForge the in-place editing style that alacrittyForge invented: one table per section, values edited where they live, staged changes marked and a fixed footer where the only button that writes anything sits.

### After that

- [ ] **Stop duplicating entries from generators grubForge doesn't manage** ([#20](https://github.com/jetomev/grubforge/issues/20)) — saving a custom order copies entries from scripts like `41_snapshots-btrfs` into `40_custom` without switching those scripts off, so they appear twice in the boot menu
- [ ] **Be readable on a plain text console** ([#21](https://github.com/jetomev/grubforge/issues/21), tracking [forgekit#1](https://github.com/jetomev/forgekit/issues/1)) — a console offers 8 colours and no icon glyphs, and a console is exactly where you end up when the desktop won't start
- [ ] **Warn when boot entries are frozen** ([#19](https://github.com/jetomev/grubforge/issues/19)) — while a custom boot order is saved, some settings in the Config Editor silently have no effect. grubForge should say so, and offer to apply them to the frozen entries or unfreeze. Also: make saving and rebuilding behave consistently across screens.
- [ ] **Document what happens when the config changes outside the app** ([#17](https://github.com/jetomev/grubforge/issues/17))
- [ ] **A layout pass for small terminals** — Boot Entries, Config Editor and Theme Browser get cramped
- [ ] **Configurable preferences** — backup retention, theme paths, and similar

### Done

- [x] **v1.1.0** — runs as your user and asks permission through polkit, instead of needing `sudo` for the whole application ([#18](https://github.com/jetomev/grubforge/issues/18))
- [x] **v1.0.3** — UX batch closing 15 findings from the v1.0.1 retest
- [x] **v1.0.2** — Textual 8.x compatibility, unblocking anyone on a rolling distribution
- [x] **v1.0.1** — backup retention cap, boot-menu sync indicator, read-only indicator, consistent key bindings
- [x] **v1.0** — the full application: dashboard, config editor with validation, theme browser, boot entry management, OS detection, automatic backups, boot menu rebuilding, man page, and AUR packaging

---

## Changelog

### v1.1.0 — August 2026

**grubForge stopped needing `sudo`.**

Until now, saving anything meant launching the whole application as root. Every screen, every widget, and every third-party library underneath it ran with full system privileges — in order to write one text file. [@marco-gallegos](https://github.com/marco-gallegos) filed [#18](https://github.com/jetomev/grubforge/issues/18) saying so, and was right.

grubForge now runs as your normal user and asks for permission one action at a time, through **polkit**. Your desktop draws the password dialog; you type your own password, not root's; and grubForge never sees it.

- 🔐 **A privileged helper with a fixed vocabulary.** The only part that runs as root is a small standalone script accepting nine specific jobs — save the config, rebuild the boot menu, create/restore/delete a backup, enable/disable a generator script, scan for other systems. It cannot be handed a command to run, because a helper that could would just be a way to run anything as root.
- 🛡 **It re-checks everything it's given.** Settings files must contain only `KEY=value` lines — `grub-mkconfig` *sources* that file as shell, so anything else would mean running arbitrary code as root. Backup names must match the exact pattern grubForge generates and must still resolve inside the backup directory after symlinks. Only the four GRUB scripts grubForge manages can be touched, by name.
- ✍️ **Config writes are atomic.** Written to a temporary file, then renamed into place, so an interrupted save can never leave you with half a `/etc/default/grub` — which is a machine that doesn't boot.
- 💬 **You're told before you're asked.** Confirmation dialogs say when a password is coming, so it never arrives as a surprise. Cancelling the dialog reports *"Cancelled — nothing was changed"* rather than an error, because nothing did go wrong.
- ⏳ **One prompt per job.** polkit remembers for a few minutes, so saving a setting and rebuilding the boot menu asks once, not twice. Repeated prompting for one task teaches people to type their password without reading it.
- 🖥 **The interface stays alive while you type.** Privileged work now runs off the event loop. Previously the whole TUI froze during `grub-mkconfig`; with a password dialog on screen for twenty seconds, a frozen interface would read as a crash.
- 📦 **grubForge no longer installs packages for you.** The "Install os-prober" button used to run `pacman -S --noconfirm os-prober` as root. Installing software is far broader than editing a bootloader config, and it's your package manager's job. The button now shows you the command.
- 🚦 **The read-only badge means something new.** It used to mean "you aren't root". It now means "permission cannot be requested here" — no polkit, no helper installed, or no desktop session — and it tells you which, and what to do about it.

`sudo grubforge` still works and skips the prompts. On a console or over SSH, where there's no window to show a dialog in, that's the way to make changes — and grubForge says so instead of failing mysteriously.

New dependency: `polkit`.

### v1.0.3 — May 27, 2026

**A UX batch closing all 15 findings from the v1.0.1 retest.**

- 🔄 **Screens refresh themselves.** Every screen now re-reads from disk when you open it, so a save, a new backup or an applied theme shows up without a manual refresh. The Dashboard gained a distinct yellow "pending changes" state, separate from "your boot menu is older than your settings" and "everything is in sync".
- 🧭 **Rebuilding works from anywhere.** `Ctrl+R` regenerates the boot menu from any screen, not just the Config Editor — so the old "go to the Config Editor and press Ctrl+R" instructions are gone.
- 💬 **One consistent way of talking to you.** All feedback now goes through a single channel — a status line plus a toast — replacing five near-identical per-screen versions with their own inconsistent icons.
- 🐛 **Widget fixes.** The read-only badge renders again, `?` opens a real help window instead of stacking toasts, the backup preview scrolls, `E` selects the first setting if none is chosen, and screen keys work on entry without needing a click first.

No dependency or install changes.

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
