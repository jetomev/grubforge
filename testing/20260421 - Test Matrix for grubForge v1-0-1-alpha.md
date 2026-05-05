# grubForge — v1.0.1 release test matrix

End-to-end verification for every `grubforge` screen, keybinding, file touch, and safety path. Designed to run against a **locally-built package installed via `pacman -U`**, reproducing the AUR install experience (launcher at `/usr/bin/grubforge`, Python package at `/usr/lib/grubforge/`, man page at `/usr/share/man/man1/grubforge.1.gz`).

## How to run

1. Work top to bottom; each section assumes the previous passed.
2. Tick the checkbox (`[x]`) next to each test as you verify it.
3. If a test fails, **stop** and file it as a finding (`F1`, `F2`, …) in the Test Results file — don't continue past a broken section until triaged.
4. Between tests that **change system state** (Config Editor save, theme apply, boot-entry save, backup restore), either revert with a saved backup or document the new state — each section notes what to revert.
5. The theme-apply worker regression is the **focus case** for this cycle — section 7 must pass cleanly.

## Conventions

- `$` — run as your regular user
- `#` — run as root (via `sudo`)
- **EXPECT:** — the observable outcome that makes the test pass
- **[claude]** — Claude runs this from a shell tool (file checks, version strings, directory listings)
- **[javier]** — Javier runs this in the TUI or an interactive shell; paste the observation back
- **[both]** — Claude prepares, Javier confirms on-screen

---

## 1. Baseline sanity

- [x] **1.1** `[claude]` `pacman -Q grubforge` reports `grubforge 1.0.1-1`
- [x] **1.2** `[claude]` `/usr/bin/grubforge` exists, mode 755, is the launcher shim `exec python /usr/lib/grubforge/main.py "$@"`
- [x] **1.3** `[claude]` `/usr/lib/grubforge/main.py` and `/usr/lib/grubforge/grubforge/` both present
- [x] **1.4** `[claude]` Python dependencies resolvable — `python -c "import textual, rich"` returns 0
- [x] **1.5** `[claude]` Man page installed at `/usr/share/man/man1/grubforge.1.gz`; `man grubforge` opens cleanly
- [x] **1.6** `[claude]` License installed at `/usr/share/licenses/grubforge/LICENSE`

---

## 2. Man page content accuracy

- [x] **2.1** `[claude]` Man page `.TH` header reports the current version (should read `v1.0.1`, not a stale badge) → **F1**
- [x] **2.2** `[claude]` SYNOPSIS reflects the **packaged** invocation (`sudo grubforge`), not `sudo python main.py` → **F2**
- [x] **2.3** `[claude]` USAGE section lists `grubforge` (full write) and `grubforge` without sudo (demo mode) — no `cd ~/Programs/grubforge && python main.py` relics → **F3**
- [x] **2.4** `[claude]` All five SCREENS sections present: Dashboard, Config Editor, Theme Browser, Backup & Restore, Boot Entries
- [x] **2.5** `[claude]` KEYBINDINGS section lists every binding used by the app (cross-check against each `BINDINGS = [...]` in `grubforge/screens/`) — see **M1**
- [ ] **2.6** `[javier]` Read the man page end-to-end; any section out of date with behaviour? Note as a finding

---

## 3. Launch & top-level navigation

> Run as your regular user first (demo mode), then as root (full access).

- [x] **3.1** `[javier]` `$ grubforge` — app launches; title bar shows "GrubForge" (or "grubForge" if rebranding lands); no traceback
- [x] **3.2** `[javier]` Demo-mode indicator visible somewhere (footer, dashboard, or title) when launched without sudo → **F4**
- [x] **3.3** `[javier]` Press `1` `2` `3` `4` `5` — each switches to Dashboard / Config Editor / Theme Browser / Backup & Restore / Boot Entries respectively
- [x] **3.4** `[javier]` Press `?` — help overlay appears; press `?` again or `Esc` to close → **F5** (close path works but not discoverable)
- [x] **3.5** `[javier]` Press `q` — app exits cleanly, terminal restored (no scrollback damage, no leftover escape codes)
- [x] **3.6** `[javier]` `$ sudo grubforge` — app launches with full-access indicator (no demo mode); no traceback → **F4** (no visible difference from demo)
- [x] **3.7** `[javier]` Resize the terminal while running — layout reflows without breaking; no dangling widgets → **F6** (Boot Entries panel cramped — deferred to v2+)

---

## 4. Dashboard (screen 1)

- [x] **4.1** `[javier]` Dashboard shows: config file path, config status (found / missing), grub.cfg path, boot entries count, active GRUB settings, backup count → **F7** (title box misaligned), **F8** (config file path missing)
- [x] **4.2** `[javier]` Active settings displayed match what's actually in `/etc/default/grub` (spot-check 3 values)
- [x] **4.3** `[claude]` Cross-check the backup count on screen against `ls /var/lib/grubforge/backups/ | wc -l` → see **M2** (paired-file convention)
- [x] **4.4** `[javier]` When launched in demo mode, dashboard clearly flags mock/read-only state (or "is_mock" style indicator) → covered by **F4**

---

## 5. Config Editor (screen 2) — read

- [x] **5.1** `[javier]` Key list shows all 17 managed keys (`GRUB_DEFAULT`, `GRUB_TIMEOUT`, … `GRUB_SAVEDEFAULT` — full list in `config_manager.py`) → **F9** (right edit panel occludes some keys at small terminal sizes — deferred to v2+)
- [x] **5.2** `[javier]` Each key row shows current value + description
- [x] **5.3** `[javier]` Raw `/etc/default/grub` preview panel renders (read-only preview)
- [x] **5.4** `[javier]` Commented-out keys are visually distinguishable from active keys
- [x] **5.5** `[javier]` Scrolling through all 17 keys works; no key is truncated off-screen at standard terminal sizes (80x24, 120x40) → **F9** (size-dependent occlusion — deferred to v2+)

---

## 6. Config Editor (screen 2) — edit & save

> Run as root (`sudo grubforge`). Pick a safe key to toggle (e.g., `GRUB_TIMEOUT` 5 → 7, or `GRUB_DISABLE_OS_PROBER` false → true → false). **Revert before exiting the section.**

- [x] **6.1** `[javier]` Select a key, press `E` — edit input appears, focused
- [x] **6.2** `[javier]` Change the value, commit the edit — pending-edit indicator appears on that row
- [x] **6.3** `[javier]` Press `S` (Save) — confirm dialog appears; accept
- [x] **6.4** `[claude]` After save, `/etc/default/grub` reflects the new value (grep the key); a fresh timestamped backup exists in `/var/lib/grubforge/backups/` with timestamp ≈ the save moment
- [x] **6.5** `[javier]` Press `R` (Reload) — pending indicators clear; displayed values re-read from disk
- [x] **6.6** `[javier]` Try an **invalid** value for `GRUB_TIMEOUT` (e.g., `abc` or `-99`) — validator rejects; save is blocked with a clear error message
- [x] **6.7** `[javier]` Press `Ctrl+R` — `grub-mkconfig` runs; output visible (either in-app or the shell behind); `/boot/grub/grub.cfg` mtime updated
- [x] **6.8** `[javier]` **Revert** the test change: set the key back to its original value, save, confirm
- [x] **6.9** `[claude]` After revert, `/etc/default/grub` matches the pre-test state

---

## 7. Theme Browser (screen 3) — **regression focus for the theme-apply worker fix**

> The untagged fix on HEAD (`4490187`) rewrote the theme-apply worker pattern for Textual compatibility. This section is the regression test for that fix. System already has `starfield` and `windows-11` in `/boot/grub/themes/` — both should appear.

- [x] **7.1** `[javier]` Screen 3 opens; theme list populates with `starfield` and `windows-11` (and any others present) — see **M3** (system has 7 themes, not 2)
- [x] **7.2** `[javier]` Selecting a theme updates the right panel: detail header, color palette, `theme.txt` preview → **F11** (right panel cramped at small terminal sizes — deferred to v2+)
- [x] **7.3** `[javier]` Press `H` — help overlay (theme installation guide) appears; press `H` again to close
- [x] **7.4** `[javier]` Press `F5` — theme list refreshes without errors (BONUS: correctly identified externally-installed `tela` as the active theme — positive validation of active-theme detection)
- [x] **7.5** `[javier]` Select a theme, press `A` (Apply) — confirm dialog appears
- [x] **7.6** `[javier]` **Accept apply** — **no hang, no traceback, no "Worker … has already been started" error.** Status line reports success
- [x] **7.7** `[claude]` After apply, `GRUB_THEME=...` in `/etc/default/grub` points at the chosen theme's `theme.txt`; a fresh backup exists in `/var/lib/grubforge/backups/` (verified: 4 transitions traced through 4 chronological backups)
- [x] **7.8** `[javier]` Active-theme indicator updates on the chosen theme
- [x] **7.9** `[javier]` Apply a **different** theme back-to-back (don't re-launch the app) — confirms the worker can run more than once per session (the exact bug the fix targets) — **OVER-SATISFIED: 4 back-to-back applies succeeded, zero worker errors. Regression bug confirmed dead.**
- [x] **7.10** `[javier]` **Revert** — apply the original theme, or clear `GRUB_THEME` via Config Editor, depending on pre-test state (reverted to `windows-11` via Theme Browser apply at 20:13:49; `[claude]` confirmed `GRUB_THEME=windows-11`. **Clear-via-Config-Editor path BLOCKED → F12**)
- [x] **7.11** `[javier]` Cancel path: select a theme, press `A`, **decline** the confirm dialog — nothing changes on disk; status shows cancelled (verified: backup count unchanged after decline)

---

## 8. Backup & Restore (screen 4)

- [x] **8.1** `[javier]` Backup list opened; **18 backups** at section launch (drift from session-start count of 15 — external activity over past days touched `/etc/default/grub` and triggered auto-backups)
- [x] **8.2** `[javier]` Pass via keybinding (after focus). **F15** — initial `B` press did nothing; only after clicking into the section panel did `B` fire. **F14** (MAJOR) — clicking the Create Backup button afterwards threw `WorkerError: Unsupported attempt to run an async worker` (`action_create_backup`)
- [x] **8.3** `[claude]` After keybinding-B succeeded, new `grub_*.bak` + `grub_*.bak.label` pair appeared in `/var/lib/grubforge/backups/`; size matches `/etc/default/grub`
- [x] **8.4** `[javier]` Select-a-backup preview panel rendered correctly
- [x] **8.5** `[javier]` Pass via keybinding (`R`). **F14** — Restore button path threw the same `WorkerError` (`action_restore_backup`)
- [x] **8.6** `[claude]` After keybinding-R restore, `/etc/default/grub` content matched the restored backup (diff = 0)
- [x] **8.7** `[javier]` Pass via keybinding (`D`). **F14** — Delete button path threw the same `WorkerError` (`action_delete_backup`). Destructive cleanup: keybinding-D deleted entries one-by-one until backup-set went **18 → 0** (intentional; documents in §11 that post-§8 count is low by design, not a leak)
- [x] **8.8** `[claude]` After keybinding-D deletions, the deleted entries no longer present in `/var/lib/grubforge/backups/` (set reached 0; ~1 fresh auto-backup appeared from `/etc/default/grub` mtime change during keybinding-restores)
- [x] **8.9** `[javier]` `F5` refresh works and matches disk state. **F16** — the footer-advertised `R Refresh` is shadowed in §4 by the section's `R Restore` binding; refresh-via-`R` is silently broken on this screen (functional refresh preserved via `F5`)
- [x] **8.10** `[javier]` Cancel paths verified: declining the Restore confirm dialog and the Delete confirm dialog leaves filesystem state untouched

---

## 9. Boot Entries (screen 5)

- [x] **9.1** `[javier]` Boot Entries opened; entries list parsed from `/boot/grub/grub.cfg`; count matched dashboard. **Snapshots-dedup question answered: 1 row.** UI deduplicates the 3× `Arch Linux snapshots` entries that were on disk in `40_custom` (mtime Apr 3 20:11 — pre-test state). No finding — implicit dedup is correct behavior
- [x] **9.2** `[javier]` Each entry shows title + type (Linux / Chainload / Submenu / etc.)
- [x] **9.3** `[javier]` `K`/`J` reorder + pending-reorder indicator work
- [x] **9.4** `[javier]` `N` rename + pending-rename indicator work
- [x] **9.5** `[javier]` `S` Save → confirm dialog → accepted → `/etc/grub.d/40_custom` written + `grub-mkconfig` ran. **F13 watch-for answered:** Save Order properly regens grub.cfg — F13 remains scoped to Theme Apply only
- [x] **9.6** `[claude]` `/etc/grub.d/40_custom` mode 755 (3739 bytes, mtime May 5 17:38), reflects new order/names. **Side effect (intentional, README:211):** `10_linux`, `30_os-prober`, `30_uefi-firmware` had +x stripped and `.grubforge_perms` sidecars created (8-byte octal-mode files). **Same approach as grub-customizer; fully reversed by 9.7.** Operational caveat to add to docs in HF1: while custom order is active, kernel-update post-install hooks running `grub-mkconfig` will produce a `grub.cfg` without auto-detected linux entries — new kernels won't surface in the menu until Restore Original or manual entry add
- [x] **9.7** `[javier]` `R` Restore Original → confirm → original order restored. `/etc/grub.d/40_custom` reset to stock template (212 bytes, mtime May 5 17:40); `.grubforge_perms` sidecars consumed; +x restored on `10_linux`, `30_os-prober`, `30_uefi-firmware`. Round-trip clean
- [x] **9.8** `[javier]` Create-custom-entry template flow worked (template selected → entry appears → save → regenerates)
- [x] **9.9** `[javier]` os-prober integration — Windows detected and surfaced as a boot entry; clean handling
- [x] **9.10** `[javier]` `F5` refresh re-parsed `grub.cfg` cleanly. **F14 watch-for answered:** all button paths in §9 (Save button, Restore Original button, Create Custom Entry button) worked without `WorkerError` — boot_entries.py audit (handoff) confirmed correct on the test article. **F15 watch-for answered:** all bindings (`K J N S R F5`) fired immediately on screen entry — F15 (focus-required-first) does NOT recur in §9, suggests the bug is screen-local to backup.py rather than a global pattern. **F16 watch-for:** §9's section `R` (Restore Original) shadows the footer's `R Refresh` — same shape as §8; observed, not re-logged (already covered by F16's "footer bindings universal" recommendation)

---

## 10. Safety flow — end-to-end invariants

- [x] **10.1** `[retrospective]` Confirm dialog precedes every destructive action — verified across 6.3 (Save), 7.5 (Apply), 8.5/8.7 keybinding paths (Restore/Delete), 9.5 (Save Order), 9.7 (Restore Original), 9.8 (Create Custom Entry save)
- [x] **10.2** `[retrospective]` Declining leaves state untouched — verified in 7.11 (cancel theme apply), 8.10 (cancel restore + delete dialogs), §9 cancel paths
- [⚠] **10.3** `[claude]` **Indeterminate.** Pre-§8.7 monotonic-timestamp behavior was consistent with matrix expectation (each Save/Apply/Restore in §6/§7 produced a fresh backup with strictly increasing timestamps). Post-§8.7 timeline only has the 1 surviving auto-backup from /etc/default/grub mtime change during keybinding-restore in §8 — destructive cleanup wiped the rest. Side effect of 8.7's intentional behavior, not a defect — flagged as **M6** matrix gap (§11 needs a survival backup preserved before §8.7)
- [x] **10.4** `[javier]` Demo-mode write attempts surface a status-line message but expose the OS errno: Backup screen `B` keybinding shows `x Backup failed: [Errno 13] Permission denied`; Config Editor `S` save shows the same `[Errno 13] Permission denied`. Not silent (✓), not a traceback (✓), but not the matrix-expected "clear read-only mode message" — logs as **F17** (paired with F4 in the same demo-mode-detection commit)
- [x] **10.5** `[javier]` Validation errors surface in-app cleanly — verified in 6.6 (`GRUB_TIMEOUT=abc` rejected without traceback). Note: F12's empty-value rejection on `GRUB_THEME` is a validator scope defect, not a 10.5 failure (the rejection itself was handled gracefully)

---

## 11. Cleanup & state verification

- [x] **11.1** `[javier]` App exited cleanly after the cleanup re-launch (`sudo grubforge` → `5` → `R` → `q`)
- [⚠] **11.2** `[claude]` `/etc/default/grub` is functionally clean — 5 of 6 tracked keys match pre-test exactly (GRUB_DEFAULT=0, GRUB_TIMEOUT=10, GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet", GRUB_THEME points at windows-11, GRUB_DISABLE_OS_PROBER=false). **One drift detected** on GRUB_GFXMODE: pre-test was `"1920x1080"`, current is `1920x1080,auto`. Cannot attribute to grubForge conclusively (no surviving pre-test backup — see **M6**); logged as **F18** for HF1 code investigation per Javier's call
- [x] **11.3** `[claude]` `GRUB_THEME="/boot/grub/themes/windows-11/theme.txt"` matches pre-test value exactly
- [⚠] **11.4** `[claude]` `/etc/grub.d/40_custom` is at the **stock template** (212 bytes, mtime 2026-05-05 18:09), not the pre-test state (which had 6 entries + 3× duplicate `Arch Linux snapshots`, mtime 2026-04-03 20:11). **By design — Restore Original wipes 40_custom rather than reverting to a previous version.** Auto-detect scripts (`10_linux`, `30_os-prober`, `30_uefi-firmware`) are mode 755 and contribute to grub.cfg again — so the boot menu will still surface 6 entries on next regen. Net cleanup is correct; pre-test 3× duplicates absorbed as a side-effect win. **Matrix gap** logged as **M5**: §9 ordering (9.8 saves AFTER 9.7's restore) leaves the system in custom-order-active state unless an explicit final-restore step is added. No `.grubforge_perms` sidecars present — pristine
- [ ] **11.5** `[javier]` Optional reboot — skipped this session (will validate at retest after HF1 commits land, alongside F13's reboot validation per the regression list)

---

## Findings to carry forward

Any test that fails gets a finding number (`F1`, `F2`, …) recorded in the companion Test Results file (`20260421 - Test Results for grubForge v1-0-1-alpha.md`). Each finding notes:

- What the test expected
- What actually happened (paste the output / describe the symptom)
- Severity (blocker / major / minor / polish)
- Proposed fix direction (if obvious)

Matrix-refinement observations (a test that was ambiguous, missing, or over-broad) are tracked with `M1`, `M2`, … in the same Results file.
