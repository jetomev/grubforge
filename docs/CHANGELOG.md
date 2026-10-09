# grubForge — full changelog

*The README carries the two most recent entries; the complete history lives here, newest-first.*

### v2.2.0 — October 8, 2026

**A key for every menu entry, "Boot Menu", a page of hypeForge Settings, and buttons that show their key.** Javier found these on October 8 while running grubForge inside hypeForge Settings, in two rounds.

- ⌨ **Help has a number now** ([#38](https://github.com/jetomev/grubforge/issues/38), F-6). The numbers **1 – 6** follow the menu bar, Help included (Quit has none), and **Ctrl** + an entry's underlined letter goes there too. The bottom bar says **1-6 menu** instead of the confusing "1-5 screens". These keys now come from [forgekit](https://github.com/jetomev/forge-suite/tree/main/forgekit) 0.10.0, which makes them from the menu itself, so no entry can be left without a key again.
- 🔡 **Javier's letter rule** (his second run, same day): each entry's Ctrl letter is the first letter of its name unless another entry already has it, then the next letter of the name. Help is always H, Quit Q, and grubForge's own Ctrl+R (rebuild) is left alone. So **Settings is now Ctrl+S** (was Ctrl+E) and **Backups Ctrl+A** (was Ctrl+K: B belongs to Boot Menu). Pressing a menu's number again closes it (6, 6 opens and closes Help), and the open menu's name stays lit while it's open.
- 📄 **About, License, Keys and the manual open as pages** in the main area instead of windows on top, with Help lit while they show; **Esc** goes back to where you were. **F1** still opens the manual at the right page, and Esc then returns to the screen you were on; in the manual, **Backspace** goes to the previous manual page.
- 🔤 **"Boot Menu"** ([#39](https://github.com/jetomev/grubforge/issues/39), F-7): the screen's name in the menu bar, on the screen itself, in the manual and in the README.
- 🧩 **A page of hypeForge Settings** ([#40](https://github.com/jetomev/grubforge/issues/40)): started as `grubforge --hypeforge` (any capitals), grubForge has no Quit of its own. Settings closes it, and grubForge first asks its usual question when something isn't saved or isn't in the boot menu yet. `--help` doesn't list it: it's for Settings, not for people.
- 🏷 **Buttons in Javier's format** ([#40](https://github.com/jetomev/grubforge/issues/40)): the name in Title Case, then the key in brackets: **Save Changes (s)**, **Rebuild Boot Menu (F9)**, **Restore (r)**, **Find Other Systems (f)**. A button without a key of its own shows just its name. Three buttons said "(asks for your password)"; that moved into the text beside them, so brackets always mean a key.
- Also: the install steps for other distributions now fetch forgekit from the [Forge Suite](https://github.com/jetomev/forge-suite) (its old repository is archived) together with `pyte`, and the Usage section describes 2.1's password box instead of the desktop's password window.

Tests: 78 → **108** (30 new; each one was seen to fail with its fix taken out). Warnings: 3 → 3 (no change), all deprecation notices from the PyGObject library and forgekit's use of it, none from grubForge's own code. New requirement: `python-forgekit` ≥ 0.10.0.

### v2.1.0 — October 4, 2026

**The password in grubForge's own box, and saving on a text console** ([#36](https://github.com/jetomev/grubforge/issues/36)). Javier: a desktop password window *"doesn't make sense"* for a terminal app, and *"how does it work on the tty version?"* Until now it didn't: with no desktop to draw the password window, `pkexec` gave up and grubForge said to start it with `sudo`.

- 🔐 grubForge becomes polkit's password asker **for its own process only** ([forgekit 0.6.0](https://github.com/jetomev/forgekit/releases/tag/v0.6.0)'s `InAppPolkitAgent`). polkit's own helper checks the password; grubForge still never runs as root, and its helper still does one fixed job at a time. A wrong password is asked again (three tries); Cancel cancels.
- 🖥 **A text console can save now.** The manual's console pages no longer say `sudo grubforge`.
- Over SSH nothing changes: grubForge's rule still refuses permission there.

Tested in the KognogOS VM on a real text console (a wrong password asked again, the right one made a backup as root), then by Javier on his desktop (a theme change and a backup, both asked in grubForge's box: *"perfect!"*) and on tty3 (*"works wonders"*). Tests: 53. New dependency: `python-gobject`; `python-forgekit` ≥ 0.6.0.

### v2.0.0 — October 2, 2026

**grubForge, rebuilt.** Every screen was redesigned from a screen-by-screen plan Javier approved before any code was written ([`docs/design/v2.0.0-screens.html`](design/v2.0.0-screens.html)). Then it was built on [forgekit](https://github.com/jetomev/forgekit) 0.5.0, the base the Forge apps share. Javier's brief: screens with care for formatting, colour and the flow of use, and "leave as little to the user to write where options are known to select from."

**Five screens**
- 🏠 **Overview**: "is my boot menu all right?" in four boxes. Anything that needs attention comes with the button that fixes it.
- 🔧 **Settings** is a form: 17 settings in five groups (Start-up, Look, Kernel options, Other systems, Advanced), each with a plain name and GRUB's own name in the help line. Lists read from your computer (entries, themes, screen sizes), worded On/Off switches, wait-time presets, a kernel-options checklist with an explanation per option, colours with a sample. A changed row says "● changed · was: …".
- 🖥 **Boot menu**: the menu as it shows at start-up. Move, rename, choose what starts first, remove, find other systems. **Add an entry** from lists read from this computer (kernels, start-up images, disks, EFI loaders), checked with GRUB's own `grub-script-check` before it is saved. Entries made by other tools (btrfs snapshots, memtest) are **fixed** and never copied into your order ([#20](https://github.com/jetomev/grubforge/issues/20)); an old copy left by 1.x can be dropped.
- 🎨 **Themes**: a preview of *your* entries in the theme's colours; installing a downloaded theme goes through a checked helper step (plain files only, nothing outside the theme's folder, size limits, never overwrites).
- 🗂 **Backups**: why each was made, in plain words, and what restoring it would change, before you do. Your boot order is copied beside each backup.

**Save and Rebuild**
- **F10** saves: a review of every change (old → new), a backup, then the write. **F9** rebuilds the boot menu, or both happen at once with "Save and rebuild". What you save stays saved.
- "Saved · not in the boot menu yet" stays visible until you rebuild, also across restarts and for changes made outside grubForge ([#17](https://github.com/jetomev/grubforge/issues/17)). Quitting asks first.
- When grubForge closes, the terminal gets a record: what was saved, whether the boot menu has it, the newest backup, and the run log (`~/.local/share/grubforge/logs/`).

**Also**
- 📖 A **manual inside the app** (M, 14 pages); F1 on anything opens its page.
- 🖥 **Readable on a plain text console** ([#21](https://github.com/jetomev/grubforge/issues/21)), and nothing cut off at 100 columns ([#33](https://github.com/jetomev/grubforge/issues/33)).
- 🐧 **Every major distribution** ([#24](https://github.com/jetomev/grubforge/issues/24)): Arch, Debian/Ubuntu, Fedora/RHEL (`/boot/grub2`, `grub2-mkconfig`, entry files), openSUSE, found automatically; the helper picks the right tool itself. Systems that don't use GRUB open read-only and say why. Tested in VMs built from each distribution's cloud image (`scripts/make-test-vms.sh`), with a real save each. They found four problems, all fixed:
  - [#29](https://github.com/jetomev/grubforge/issues/29): an unset list setting looked like a change;
  - [#30](https://github.com/jetomev/grubforge/issues/30): `/etc/default/grub.d` silently overrode a save; such settings are now shown locked with their file;
  - [#31](https://github.com/jetomev/grubforge/issues/31): Fedora's Boot menu offered things that don't apply there;
  - [#32](https://github.com/jetomev/grubforge/issues/32): empty and unset weren't treated as the same.
- Kernel options warn while your own order is in use, since entries in it keep their own options ([#19](https://github.com/jetomev/grubforge/issues/19)).
- `grubforge --version` and `--help` print instead of opening the app ([#22](https://github.com/jetomev/grubforge/issues/22)).
- The test matrix no longer simulates a root-only `grub.cfg` (impossible on a FAT32 `/boot`); the helper's read path was exercised for real on KognogOS, where the file is root-only ([#25](https://github.com/jetomev/grubforge/issues/25)).

**Testing**: §1–§10 of [`testing/20261002 - Test Matrix for grubForge v2-0-0.md`](../testing/), including Javier's own run on KognogOS as a real package upgrade from 1.1.3 (built with `scripts/make-rc-packages.sh`), which ended with a restart from the menu 2.0 built. Tests: 25 → **78** (53 new); warnings 0 (the new tests first raised 32 cleanup warnings; fixed).

New dependency: `python-forgekit` ≥ 0.5.0. Gone: the 1.x screens; the backup list's Size column.

### v1.1.3 — September 29, 2026

**grubForge now reads where each boot entry comes from, instead of guessing.**

The Boot Entries screen shows a *source* under every entry. It was guessed from the entry's title: anything without "windows", "uefi" or "snapshot" in its name was credited to this system. So a second Linux found on the disk — Ubuntu next to Debian, Fedora next to Arch — was listed as if it were your own. Found while fixing [#27](https://github.com/jetomev/grubforge/issues/27), filed as [#28](https://github.com/jetomev/grubforge/issues/28).

- 📖 **Read, not guessed.** `grub-mkconfig` already writes which script produced each section of `grub.cfg`. grubForge now reads that, so the Ubuntu found by os-prober reads "OS Prober", and your own kernels read your system's name.
- 🔁 **The source survives a custom order.** Saving an order moves every entry into one file, `40_custom`. Read literally, every entry would then say "Custom", which tells you nothing. grubForge now writes a one-line note above each entry recording where it came from, and shows it as *"OS Prober · custom order"*. GRUB treats the note as a comment and ignores it.
- 🤷 **When it has to guess, it says so.** An order saved by an earlier grubForge carries no notes, so those entries read *"(guessed)"* until you save the order again. The guess itself is better: os-prober always names what it finds "… (on /dev/…)", and grubForge now recognises that.
- 🛠 **Saving switches off the right scripts.** The source also decides which GRUB scripts a save turns off. A second Linux wrongly credited to this system left the os-prober script running, which could list it twice. It is now switched off with the rest.
- 🔐 **The root helper passes the new lines, and nothing else.** On systems where `grub.cfg` is readable only by root, the helper now hands back the section markers and notes too, each matched against one fixed shape. The rest of the file, including any password hash, still never leaves.

Also new: `tests/`, 25 automated checks that need no root and run during every AUR build.

No new dependencies.

### v1.1.2 — September 29, 2026

**grubForge told Debian users their own system was Arch Linux.**

[@jfp42](https://github.com/jfp42) filed [#27](https://github.com/jetomev/grubforge/issues/27): on Debian, the Boot Entries screen labelled Debian's own kernels `source: Arch Linux`. The label for `10_linux` — the GRUB script that finds the kernels installed on whatever machine it runs on — was written into the code as "Arch Linux". That is only true on Arch.

It was wrong closer to home too. On a KognogOS machine, which is built on Arch but is not Arch, the same entries read "Arch Linux" instead of "KognogOS".

- 🏷 **The system names itself.** grubForge now reads the name from `/etc/os-release`, the same file GRUB itself uses to title the entries. Debian reads "Debian GNU/Linux", Fedora "Fedora Linux", KognogOS "KognogOS", Arch still "Arch Linux".
- 🤷 **When it can't tell, it says so.** If `/etc/os-release` is missing or unreadable, the label is a neutral "This system" rather than a distribution grubForge has not confirmed.
- 🧩 **Xen entries get a name too.** `20_linux_xen` had no label at all and now follows the same rule, as "<your system> (Xen)".

Verified on a stock Debian 13 virtual machine before and after the change, and on a KognogOS desktop. Entries from other scripts (other systems found on the disk, firmware settings, snapshots, custom entries) are unchanged.

**Known and next:** the *source* underneath the label is still guessed from the entry's title, so another Linux found on the disk is credited to this system ([#28](https://github.com/jetomev/grubforge/issues/28)). That is the next release.

No new dependencies. One new file: `grubforge/system.py`.

### v1.1.1 — August 31, 2026

**grubForge could not read a boot menu it was not allowed to open — and reported that there wasn't one.**

[@jfp42](https://github.com/jfp42) filed [#23](https://github.com/jetomev/grubforge/issues/23): on a laptop where `/boot/grub/grub.cfg` is readable only by root, grubForge showed **"Boot entries 0 detected"**. The file was full of boot entries. grubForge never got to look, and presented that as an answer.

Checking the report on a stock Debian 13 virtual machine turned out worse than the report. Debian ships `/boot/grub/grub.cfg` as `rw-------` by default — no GRUB password configured, nothing hardened, just the default. **Every Debian user has been shown an empty boot menu and told that was the truth.** One person wrote in; the rest presumably concluded grubForge was broken and moved on.

- 🔍 **"I couldn't read it" and "there's nothing there" are now different answers.** Both places that load the boot menu caught the permission error and returned an empty list, which is how a locked file came to look like an empty one. The Dashboard now says the file is readable only by root, and Boot Entries says so too instead of showing an empty menu.
- 🔐 **The boot menu is read through the privileged helper when the ordinary read is refused.** A tenth verb, `read-entries` — the same polkit prompt you already get when saving. Where `grub.cfg` is world-readable, Arch included, nothing changes and nobody is asked for anything.
- 🙈 **The helper hands back only the menu blocks, never the whole file.** The part above them can carry a `password_pbkdf2` hash, which is one of the reasons some distributions lock the file down to begin with. Drawing a list of boot entries is no reason to hand that to an unprivileged process.
- 🚫 **No password prompt merely for opening the app.** The Dashboard reports the situation and leaves it there. The prompt comes when you open Boot Entries to actually do something — on opening the screen, with nothing to press.
- 📦 **Distributions without a package can install the helper.** `install-helper.sh` puts the helper and the polkit rule where polkit requires them. Without it, everyone outside Arch was stuck read-only — which, on Debian, meant no boot menu at all. This is the part that makes the fix reach the person who reported it.

The `chmod a+r /boot/grub/grub.cfg` workaround is no longer needed — and was never a good trade, since it exposes the file to every account on the machine.

No new dependencies. One new file: `install-helper.sh`, for distributions that have no grubForge package.

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
