# Test Matrix — grubForge v2-0-0

**Started:** 2026-10-02, filled in phase by phase as each lands (Javier: *"Remember the Test Matrix"*).
**Scope:** the move onto forgekit and the full redesign — design approved 2026-10-02 (`docs/design/v2.0.0-screens.html`), Javier's six rulings: form with visible controls; Save and Rebuild separate; plain names; entries from other tools fixed (#20); every major distribution (#24); closing note + quit warning.
**Where:** this desktop (KognogOS, real files, **read-only**: nothing is saved here) and the KognogOS VM `kognog-hypeforge` from snapshot `clean-install-3` (real saves; reverted after). Other distributions: VMs still to build (§9).
**Who:** §1–§8 Claude (headless through Textual's Pilot, screens recorded and looked at); §10 Javier, at the keyboard.

---

## 1 · Automated

| ID | Suite | Checks | Result | Notes |
|---|---|---|---|---|
| 1.1 | `tests/test_boot_entry_sources.py` (v1.1.3, #28) | 25 | **PASS** | unchanged, still green after the `+` marker fix |
| 1.2 | `tests/test_v2_settings.py` — distributions, settings in plain words, writer, session, screens | 21 | **PASS** | the long-field test proven in the failing direction (fails without the forgekit fix) |
| 1.3 | `tests/test_v2_bootmenu.py` — fixed entries (#20), the draft, Add an entry, the UEFI guard | 12 | **PASS** | found the `20_memtest86+` marker bug (below) |
| 1.3b | `tests/test_v2_themes_backups.py` — theme install safety (escapes, links, devices, names), packing, preview, backup differences | 11 | **PASS** | |
| 1.4 | forgekit `tests/` (v0.5.0 pieces) | 48 | **PASS** | incl. the gallery as a real text console |
| 1.5 | Helper refusals (not root / unknown verb / no verb) | 3 | **PASS** | |
| 1.6 | `grep -rn "run_worker(self\.action_" grubforge/` | empty | **PASS** | |

## 2 · Settings (Phase 2) — desktop, read-only

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 2.1 | Overview reads the real system | starts, waits, entries, theme, rebuilt, backups, GRUB family | **PASS** | "first entry · 10 seconds, always · 7 · your own order · kognogos · Sep 16 · 10 backups · Arch" |
| 2.2 | Nothing is "changed" at start | changes bar hidden | **PASS** | was 3 false changes (kernel order, unset colours) — fixed, test 1.2 guards it |
| 2.3 | Every group drawn: lists, worded switches, presets, choices, kernel checklist, colours + sample | readable, not clipped at 120×40 | **PASS** | screens in the design page v4 |
| 2.4 | A value as long as its field | visible | **PASS** | was blank (forgekit scrollbar) — fixed in forgekit |
| 2.5 | Tab order and hints | each setting in turn, then the bar; hints follow focus | **PASS** | |

## 3 · Save and Rebuild (Phase 2) — VM, real saves

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 3.1 | Change "Wait before starting" 5 → 3, F10, "Save and rebuild" | backup first; `GRUB_TIMEOUT=3`; grub.cfg rebuilt with `set timeout=3`; bar gone | **PASS** | backup `grub_20261002_134916_694646.bak` |
| 3.2 | Change "Show the menu" → countdown, F10, "Save" only | "⚠ Saved at … · not in the boot menu yet" | **PASS** | |
| 3.3 | Quit after 3.2 | "Before you go": Rebuild and quit / Quit anyway / Stay | **PASS** | |
| 3.4 | F9 after 3.2 | rebuilt; bar gone | **PASS** | |
| 3.5 | Closing note | "Closed · everything saved is in the boot menu", times, newest backup | **PASS** | |
| 3.6 | "Start this entry" list | the VM's real entries, submenu children as "Submenu ▸ entry" | **PASS** | |

## 4 · Boot menu (Phase 3)

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 4.1 | Desktop, read-only: the real menu | 7 rows; Windows entries from Other systems; snapshots fixed | **PASS** | sources "(guessed)": the desktop's order predates v1.1.3 origin lines |
| 4.2 | Desktop: the v1.x #20 duplicate | the copy inside the saved order marked "old copy · dropped when you save"; a notice says so; the review lists it | **PASS** | |
| 4.3 | Move up/down (Shift+↑↓) | slides; both moved entries marked; fixed entries never move | **PASS** | a 2-step move swapped instead of sliding — fixed |
| 4.4 | Add an entry: Linux kernel | kernel, image, disk and options read from the computer; GRUB's checker accepts it | **PASS** | desktop: `/boot` is the ESP (prefix ""), root btrfs `subvol=@` copied from /proc/cmdline |
| 4.5 | Add an entry: empty | GRUB accepts the starting point | **PASS** | an entry with only a comment was rejected by GRUB — fixed |
| 4.6 | VM: add "safe graphics", move it, rename "KognogOS Linux" → "KognogOS", Save and rebuild | real menu: KognogOS, KognogOS (safe graphics), Advanced options…; `10_linux` turned off | **PASS** | |
| 4.7 | VM: Back to the original order, then F9 | "saved, not rebuilt" in between; then the original two entries; `10_linux` executable again; stock 40_custom | **PASS** | |
| 4.8 | Find other systems | os-prober installed? search on? search through the helper | **PASS** (status) | the search itself not run here (no other OS in the VM) |

**Findings so far** (fixed, each with a test):
- `20_memtest86+` (Debian) wasn't recognised as a script (`+` not allowed in the marker pattern), so its entry was guessed as `10_linux` and would have been copied into a saved order: #20 again from a different tool. Pattern widened in the parser, origin lines and the helper's pass-through, together.

**Resolved:**
- O-1: the UEFI firmware entry now keeps its `if [ "$grub_platform" = "efi" ]` guard in a saved order (test in 1.3; no double wrap on a second save).
- An old #20 copy on this desktop first counted as "1 change not saved" at start. Ruled out: a problem found is not a change you made. The Boot menu now offers "Drop the old copy"; it becomes a change only then (or when any other order change is saved).

## 5 · Themes (Phase 4)

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 5.1 | Desktop: the installed themes | 8 listed, short names, kognogos "● in use"; preview in the theme's colours with the real entries | **PASS** | |
| 5.2 | VM: an attack archive (`../../../etc/grubforge-pwned`) straight to the helper | refused; nothing written outside; no theme folder left | **PASS** | "'..' is not allowed" |
| 5.3 | VM: Install a theme… from a downloaded folder | in `themes/My-Test-grub-theme`, root-owned, only its own files | **PASS** | a symlink in a download is left out when packing (test 1.3b) |
| 5.4 | VM: Use this theme → Save and rebuild | review shows the theme + "Menu drawn as Graphics"; grub.cfg uses the theme and gfxterm | **PASS** | |

## 6 · Backups (Phase 4)

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 6.1 | Desktop: the 10 backups | dates, plain reasons ("Before using a theme (kognogos)"), sizes; "Restoring this would change" | **PASS** | |
| 6.2 | VM: a save makes a backup with the boot-order copy beside it | `.bak` + `.bak.40_custom` | **PASS** | |
| 6.3 | VM: Restore… | the confirm starts on Cancel; settings back; "saved, not rebuilt"; F9 takes the theme out of grub.cfg | **PASS** | |
| 6.4 | VM: Delete… | the backup and its boot-order copy gone | **PASS** | |
## 7 · Manual, help, keys (Phase 5)

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 7.1 | `M` / Help ▸ Manual | 14 pages, contents left, steps first | **PASS** | `grubforge/manual/*.md`, also readable on GitHub |
| 7.2 | F1 on a setting | the manual at that group's page (e.g. Start-up) | **PASS** | |
| 7.3 | F1 on Boot menu / Themes / Backups / Overview | their pages | **PASS** | |
| 7.4 | Opening a page other than the first | stays there | **PASS** | the list's own first highlight sent it back to page 1 — fixed in forgekit, test added |
| 7.5 | The manual's claim "files are read again on every screen switch" | true | **PASS** | made true in code (it wasn't for Settings) |

## 8 · Text console (`TERM=linux`, forgekit's console preview)

| ID | Check | EXPECT | Result | Notes |
|---|---|---|---|---|
| 8.1 | Every screen at 100×30: Overview, Settings, Kernel options, Boot menu, Themes, Backups, Manual | only console-font characters; nothing drawn in its own background | **PASS** | |
| 8.2 | Same at 128×48 (a 1024×768 console) | same | **PASS** | |
| 8.3 | Unticked checklist boxes | empty | **PASS** | were an X coloured like the box (flagged as invisible) — forgekit `CheckList` draws nothing |
| 8.4 | List boxes | bordered, value beside its label | **PASS** | had no border on the console and the value floated a line up — fixed in forgekit |
| 8.5 | Button labels ending in "…" | "..." on the console | **PASS** | |
| 8.6 | A real tty in the VM (tty8, `sudo grubforge`) | readable and usable | — | to run with Javier's §10 |
| 8.7 | Nothing cut off at 100 columns: every button label whole and inside its row, no sideways scroll bar, every settings row's control inside its row (automatic: `test_every_button_label_fits_at_100_columns`, `test_no_settings_group_scrolls_sideways_at_100_columns`, `test_the_changed_mark_shows_at_100_columns`) | all whole | **PASS** | added 10-02 after 8.1 passed with things cut off: 8.1 checked that characters are *readable*, not that they *fit*. Found + fixed: Overview task buttons and Safety line; Backups buttons, list (sideways scroll, a hidden Size column) and heading; Boot menu "Remove…"; Look colour sample; wait-time presets ("forever", the known 100-column clip); the "● changed" mark (cut at 120, gone at 100 — moved to the line under the setting); notices wrapping to the edge. Each test was run against the old code and failed there. Note: the Backups list check relies on a backup with a long reason existing; on a machine with none it passes without exercising that path |

Formerly known at 100×30: the last wait-time preset ("forever") sat past the right edge. Fixed 10-02, see 8.7.

## 9 · Other distributions (VMs from each distribution's cloud image, UEFI — `scripts/make-test-vms.sh`)

Each VM: detection, the boot menu read, nothing pending at start, a real Save and rebuild that must show up in grub.cfg, then put back. Run as root inside the VM (`/opt/gf` venv with Textual), from snapshot `fresh`.

| ID | Distribution | Detected | Boot menu | Real change lands in grub.cfg | Result | Notes |
|---|---|---|---|---|---|---|
| 9.1 | Debian 13 | Debian · /boot/grub · grub-mkconfig | 3 entries | **yes** (countdown style) | **PASS** | first run found F-1 and F-2 (below) |
| 9.2 | Ubuntu 24.04 | Debian family · Ubuntu | 3 entries | **yes** | **PASS** | 4 settings decided in `50-cloudimg-settings.cfg`, locked |
| 9.3 | Fedora 44 | Fedora · /boot/grub2 · grub2-mkconfig · entries as separate files | 1 entry file + UEFI Firmware Settings (fixed) | **yes** (wait 0 → 7, put back) | **PASS** | first run found F-3 (below); SELinux permissive in the test VM only |
| 9.4 | openSUSE Tumbleweed | openSUSE · /boot/grub2 · grub2-mkconfig | 3 entries | **yes** (`set timeout=7`, put back) | **PASS** | first run found F-4 (below); the guest agent ships with guest-exec off, allowed in the test VM |

**Findings from the distribution VMs** (fixed, each with a test):
- **F-1 (Debian):** `GRUB_GFXMODE` not set in the file → the list fell back to "Automatic" and staged it as a change nobody made. Every list now offers "Not set (…)" when the file doesn't set it.
- **F-2 (Debian, Ubuntu):** `/etc/default/grub.d/*.cfg` (read by Debian's grub-mkconfig *after* /etc/default/grub) decided `GRUB_TIMEOUT`; grubForge's saved change had **no effect** and nothing said so. grubForge now checks whether the system's grub-mkconfig reads that folder; settings decided there are shown with their real value and file, locked ("change it there"), and the Overview says how many. Writing into that folder is a possible follow-up.
- **F-3 (Fedora):** on the Boot menu, a "Drop the old copy" button showed with no old copy, the hint line offered move/rename/add (which don't work on entry files), and GRUB's own entries (UEFI Firmware Settings) were missing. Now: the button only with an old copy, a hint line of keys that work, and GRUB's own entries listed after the entry files as fixed. Test `FedoraStyle` fails on the old code, passes on the new.
- **F-4 (openSUSE):** openSUSE ships `GRUB_BACKGROUND=` (present, empty). grubForge treated empty and unset as different, so it showed a change at start, and a save then switched that line off: an edit nobody asked for, though harmless to GRUB. Empty and unset now count as the same everywhere a change is decided. The test checks at start, on the Overview; a first version checked after opening Settings, where the false change had already gone, and it passed on the broken code too. Rewritten until it failed on the old code.

**§9 result: all four families PASS** (Debian 13, Ubuntu 24.04, Fedora 44, openSUSE Tumbleweed), each with a real save that reached the boot menu. Four findings, all fixed with tests.
## 10 · Javier's run (KognogOS VM, at the keyboard)

Setup by Claude (10-02, done): the VM `kognog-hypeforge` reset to `clean-install-3` (which ships grubForge 1.1.3 and forgekit 0.3.0, as KognogOS does), then **upgraded** to grubforge **2.0.0rc1** and python-forgekit **0.5.0rc1**: packages built by `scripts/make-rc-packages.sh` from the AUR recipes and commits `716c557` / `0c767f2`; every build check passed (53 + 25 tests, helper refusals, headless mount). Installed with `pacman -U`. **Correction (10-02, at release):** this note first said nog cannot install a package file. That was wrong, read into `nog install --help` without trying it: `nog install ./file.pkg.tar.zst` works (nog #17), and should have been used. Saved as snapshot **`grubforge-2.0.0rc1`**. A headless check as the VM's user: can save (through polkit), nothing pending at start. Javier logs in and opens a terminal.

| ID | Task | EXPECT | Result | Notes |
|---|---|---|---|---|
| 10.1 | `grubforge --version`, then `grubforge` | the version; the app opens on the Overview | — | |
| 10.2 | Overview | "Nothing needs attention"; Entries reads "readable only by an administrator" (KognogOS protects grub.cfg); Safety: password asked when you save or rebuild | — | |
| 10.3 | Settings ▸ Start-up: wait 5 → 3 with a preset, **F10**, **Save** | the review (old → new); the password window; "Saved · not in the boot menu yet" | — | |
| 10.4 | **F9** | rebuild progress; the bar clears | — | |
| 10.5 | Kernel options: tick `nomodeset`, F10, **Save and rebuild** | one review, one password, done | — | |
| 10.6 | Boot menu: **Read the boot menu** (password once), then add a "safe graphics" entry (+), move it up, F10, Save and rebuild | the list appears after the password; review lists the new entry; the menu shows it | — | |
| 10.7 | Reboot the VM | the menu shows the changes; waits 3 s; the new entry starts with nomodeset | — | the real proof |
| 10.8 | Themes: pick one, Use this theme, Save and rebuild, reboot | the menu is themed | — | |
| 10.9 | Backups: restore the oldest, F9, reboot | the original look and wait time | — | |
| 10.10 | Change something, then **Q** | "Before you go" asks; quitting prints the closing note | — | |
| 10.11 | **M**, and F1 on a setting | the manual opens, on the right page | — | |
| 10.12 | `Ctrl+Alt+F3`, log in, `sudo grubforge` | readable and usable on the text console | — | real tty |
| 10.13 | Anything that looks wrong, reads badly, or is slow | noted here as F-n | — | |

**Javier's verdict (10-02, ~16:05): "WOW!!!! it works wonders!!!!! I used, pressed, every possible option and it works great!!!!"**

Read back from the VM afterwards (grubForge's own run log `~/.local/share/grubforge/logs`, the backups, the journal), so the result rests on evidence, not only on the message:
- 3 runs, 15:54–16:03. 9 settings saves, 1 boot-order save, 2 rebuilds; each run's closing record says "everything saved is in the boot menu".
- 6 backups, one before each save, each with its boot-order copy.
- Final state: theme `starfield`, resolution `1024x768`, kernel options `quiet splash loglevel=3`, menu always shown, wait 10 s; `40_custom` holds his saved order.
- **The VM restarted at 16:03 after his changes and came up normally** (journal boot −1): GRUB built by 2.0 boots.
- The next start stopped at the firmware's own boot menu: the "UEFI Firmware Settings" entry did its job. Choosing KognogOS there started the system normally.

Rows 10.1–10.11 and 10.13: **PASS** (his message covers every option; the log shows saves, rebuilds, the boot order, a theme and a restart). **10.12 / 8.6 (real text console): PASS on Javier's word** ("Yes, go ahead!" in answer to "did the text console step happen"); it cannot be read back from the log. No findings reported.
