# grubForge — full changelog

*The README carries the two most recent entries; the complete history lives here, newest-first.*

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

### v1.0.1 — May 5, 2026
**Hotfix Batch — Stability + UX Polish (15 findings closed + backup retention cap)**

This release closes the v1.0.1-alpha test cycle. Findings are F-numbered in the [Test Results](testing/) document for traceability — every fix in this release is tied back to a documented defect.

Major:
- 🛠 **Fixed `WorkerError` on Backup screen Create / Restore / Delete buttons** (F14) — the v1.0.0 worker regression that v1.0.0's hotfix was originally meant to kill. The fix had landed in `themes.py` but `backup.py` was missed; this release applies the same idiom (sync action shim → private async worker, no `@work` decorator double-wrap) to all three sites
- ⌨️ **Universal action bindings architecture** (F13 + F15 + F16) — `E` Edit, `S` Save, `A` Apply, `R` Refresh, `Ctrl+R` Regen now fire from every screen via an app-level dispatcher; section-local keys rebound off footer collisions (Backup `B → N`, `R → X`; Boot Entries `R → X`); section bindings carry `priority=True` so they fire from any focus context; button labels carry inline key hints like `Restore (x)`
- 🚦 **Demo-mode detection** (F4 + F17) — red **DEMO** badge in sidebar logo when launched without `sudo`; destructive actions across all screens now show "Read-only mode — relaunch with sudo to ..." instead of the raw `[Errno 13] Permission denied`
- 📊 **Dashboard sync indicator** — flags when `/etc/default/grub` and `/boot/grub/grub.cfg` are out of sync, prompting `Ctrl+R` to regenerate; catches the same class of bug from any path that writes config without regen, including external tools

Minor:
- ⚙️ **Config Editor validator** (F12) — distinguishes required keys (`GRUB_DEFAULT`, `GRUB_TIMEOUT`) from optional; clearing `GRUB_THEME` and other optional values now works correctly
- ✏️ **Rebrand sweep** (F10) — `GrubForge` → `grubForge` across docs, source strings, and user-facing messages; the canonical project name is consistent everywhere
- 🗂 **Backup retention cap** (M4) — `MAX_BACKUPS` lowered from 20 to 10 (FIFO eviction was already in place; only the constant changed)
- 🎨 Help overlay shows close hint (F5); Dashboard title-box centred (F7); Config file row mirrors `grub.cfg` row format with the path included (F8)
- 📖 Man page synced (F1 / F2 / F3) — version, SYNOPSIS, USAGE all reflect the packaged launcher form

Documentation:
- ⚠️ **New caveat — kernel updates while custom order is active.** While a custom boot order is saved, the auto-generate scripts (`10_linux`, `30_os-prober`, `30_uefi-firmware`) are non-executable. Any subsequent `grub-mkconfig` run — including kernel-update post-install hooks — will produce a `grub.cfg` without auto-detected linux entries until **Restore Original** is run
- 📋 **Test artifacts in repo** — Test Matrix, Test Results, and a Release Checklist now ship in `testing/` for transparency. The release-checklist captures the worker-pattern audit (greps for `@work` + `run_worker`), version sync across six locations, pre-test snapshot procedure, and co-author credit gates that this run identified as process gaps

Investigation only (no code change):
- **F18** — observed drift in `GRUB_GFXMODE` from `"1920x1080"` to `1920x1080,auto` during the v1.0.1-alpha run. Audit of `write_grub_config` and `apply_theme` confirmed grubForge scopes mutations to the keys passed in — the drift was caused by an external writer (likely the `tela` theme's post-install hook running `grub-mkconfig`)

Deferred to v2+:
- F6 / F9 / F11 — small-terminal cramping in Boot Entries, Config Editor, Theme Browser. To be fixed as a coherent layout pass

This release was developed and tested as a Human+AI collaboration. Every finding (`F1`–`F18`) is documented in `testing/20260421 - Test Results for grubForge v1-0-1-alpha.md`.

### v1.0.0 — April 4, 2026
**First Stable Release — AUR Package**
- 📦 grubForge is now available on the AUR: `yay -S grubforge`
- 🚀 Proper system executable — run with `sudo grubforge` from anywhere
- 🔧 PKGBUILD installs to `/usr/lib/grubforge/` with launcher at `/usr/bin/grubforge`
- 📖 Man page installed to `/usr/share/man/man1/grubforge.1`

### v0.9.0 — April 4, 2026
**Man Page**
- 📖 Man page added — `grubforge.1` included in the repository
- Documents all 5 screens, all keybindings, and all managed file paths
- Built-in SEE ALSO references to `grub-mkconfig`, `grub-install`, `os-prober`
- Test locally with: `man ./grubforge.1`

### v0.8.0 — April 4, 2026
**Screenshots**
- 📸 Screenshots added to README — all five screens captured and published
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
