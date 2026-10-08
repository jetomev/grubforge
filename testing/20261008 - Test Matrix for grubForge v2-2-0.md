# Test Matrix — grubForge v2-2-0

**Started:** 2026-10-08.
**Scope:** Javier's findings from running grubForge inside hypeForge Settings (2026-10-08) and the button format he asked for on 2026-10-03:
- **F-6 (#38):** Help had no number; "1-5 screens" in the bottom bar was confusing → **1-6 menu**, numbers and Ctrl keys made by forgekit 0.10.0 from the menu itself.
- **F-7 (#39):** "Boot menu" → **Boot Menu** (the screen's name).
- **#40:** the `--hypeforge` start option (no Quit of its own inside hypeForge Settings), and button labels as **"Words In Title Case (k)"**.

**Build under test:** grubForge 2.2.0 with python-forgekit 0.10.0 (both unreleased at the time of writing).
**Where:** this desktop (KognogOS) for everything that only looks and presses keys; a real save and rebuild only on a safe path (§5).
**Who:** §1 Claude (automated). §2–§6 Javier, at the keyboard. Leave a row's Result empty until it's been run; anything that looks wrong goes in §7 as F-n.

---

## 1 · Automated (Claude)

| ID | Suite | Checks | Result | Notes |
|---|---|---|---|---|
| 1.1 | `tests/test_boot_entry_sources.py` | 25 | PASS (10-08) | unchanged |
| 1.2 | `tests/test_v2_settings.py`, `test_v2_bootmenu.py`, `test_v2_themes_backups.py` | 53 | PASS (10-08) | incl. every button label still fits at 100 columns |
| 1.3 | `tests/test_v220.py` (new): numbers and Ctrl keys reach every entry, Help is 6, Quit has none; no clashing letters; the bar says "1-6 menu"; the tab reads "Boot Menu"; under `--hypeforge` no Quit, Q / Ctrl+Q do nothing, Settings' close (SIGUSR1) shows grubForge's own question and the answer closes it; the command line takes `--hypeforge` / `--hypeForge` and `--help` doesn't list it; every button label in Javier's format and every key in a label really bound | 22 | PASS (10-08) | 12 fail on the 2.1.0 code; the other 10 (already given by forgekit 0.10.0) were each seen to fail with that piece switched off |
| 1.4 | Warnings with `-W always` | 3 → 3 | PASS (10-08) | PyGObject deprecation notices, none from grubForge |
| 1.5 | `grep -rn "run_worker(self\.action_" grubforge/` | empty | PASS (10-08) | |

## 2 · Keys, on its own in a terminal

Start it the usual way: `grubforge`.

| ID | Do | EXPECT | Result | Notes |
|---|---|---|---|---|
| 2.1 | Look at the menu bar | Overview · Settings · **Boot Menu** · Themes · Backups · Help · Quit, one letter underlined in each | | |
| 2.2 | Press **1**, **2**, **3**, **4**, **5** in turn (not while typing in a field) | Overview, Settings, Boot Menu, Themes, Backups | | |
| 2.3 | Press **6** | the Help menu opens (Manual, Keys, License, About); **Esc** closes it | | F-6 |
| 2.4 | Press **Ctrl+O**, **Ctrl+E**, **Ctrl+B**, **Ctrl+T**, **Ctrl+K**, **Ctrl+H** | each goes to the entry with that letter underlined; Ctrl+H opens Help | | |
| 2.5 | Ctrl+H twice in a row | Help opens, then closes; never two Help menus stacked | | forgekit #47 |
| 2.6 | Look at the bottom bar on the Overview and on Themes | says **1-6 menu**, never "1-5 screens" | | F-6 |
| 2.7 | Press **?** | the Keys list: "1-6, Ctrl+letter · go to a menu entry (Help is 6)", and under the Quit line "not there inside hypeForge Settings"; nothing wraps | | |
| 2.8 | Boot Menu screen | its heading reads **Boot Menu** | | F-7 |
| 2.9 | Change one setting, press **Q** | "Before you go": **Save First** · **Quit Without Saving** · **Stay (Esc)** | | |
| 2.10 | **Esc**, then **Q** again and **Quit Without Saving** | grubForge closes; the closing note says changes were left unsaved | | |

## 3 · Inside hypeForge Settings

Open hypeForge's Settings and go to grubForge's page (Settings starts it with `--hypeforge`).

| ID | Do | EXPECT | Result | Notes |
|---|---|---|---|---|
| 3.1 | Look at grubForge's menu bar | no **Quit**; Help is still there | | #40 |
| 3.2 | Press **Q**, then **Ctrl+Q** | nothing happens; grubForge stays | | #40 |
| 3.3 | Press **1** to **6**, and the Ctrl letters from 2.4 | the same as on its own (2.2–2.4) | | F-6, keys through the pane |
| 3.4 | Look at the bottom bar | **1-6 menu** | | |
| 3.5 | With nothing changed, close Settings | grubForge closes at once, no question | | |
| 3.6 | Change one setting (don't save), then close Settings | grubForge's own "Before you go" appears inside the page | | |
| 3.7 | Answer **Stay (Esc)** | grubForge and Settings both stay open; your change is still there | | |
| 3.8 | Close Settings again, answer **Quit Without Saving** | grubForge closes, and Settings with it | | |
| 3.9 | Change a setting, **Save Changes (s)**, **Save** (not rebuild), then close Settings | "Saved changes are not in the boot menu yet": **Rebuild and Quit** · **Quit Anyway** · **Stay (Esc)** | | safe path only: see §5 |

**Also on its own in a terminal (optional):** `grubforge --hypeForge` (any capitals). No Quit, Q does nothing. To close it the way Settings does, from a second terminal: `kill -USR1 $(pgrep -f 'grubforge.*--hypeforge')`. Closing the terminal window also ends it.

## 4 · Button labels (Javier's format)

Every action button: the name in Title Case, then its key in brackets when it has one.

| ID | Where | EXPECT | Result | Notes |
|---|---|---|---|---|
| 4.1 | Bar at the bottom, after a change | **Save Changes (s)** · **Discard Changes** | | |
| 4.2 | Bar at the bottom, saved but not rebuilt | **Rebuild Boot Menu (F9)** · **Why?** | | |
| 4.3 | Overview | **Rebuild It Now (F9)** · **What This Means** (only when needed); **Start This Entry** · **Wait Time** · **Pick a Theme** · **Back Up Now** | | |
| 4.4 | Boot Menu | **Move Up (Shift+↑)** · **Move Down (Shift+↓)** · **Rename (F2)** · **Remove** · **Start This First** · **Add an Entry (+)** · **Find Other Systems (f)** · **Back to the Original Order** | | |
| 4.5 | Boot Menu windows | Rename: **Rename** · **Cancel (Esc)**. Add an entry: **Edit by Hand** · **Add Entry** · **Cancel (Esc)**. Find other systems: **Turn the Search On** · **Search Now** · **Close (Esc)**. Remove: **Remove (y)** · **Cancel (n)** | | the password note now sits in the text, not on the button |
| 4.6 | Themes | **Use This Theme** · **Stop Using a Theme** · **Install a Theme (i)** · **Where to Get Themes**; its window: **Choose** · **Install** · **Cancel (Esc)** | | |
| 4.7 | Backups | **Restore (r)** · **Back Up Now (n)** · **Show Whole File** · **Delete (d)**; Restore asks with **Restore (y)** · **Cancel (n)** | | |
| 4.8 | The review before saving (F10) | **Save** · **Save and Rebuild** · **Cancel (Esc)** | | |
| 4.9 | Press the key shown on 4.4, 4.6, 4.7 (F2, +, F, I, R, N, D) | each does what its button does | | |
| 4.10 | Every screen at a small window (about 100 columns) | no button label cut off | | |

## 5 · Save and rebuild still work (safe path)

In the KognogOS VM, or on this desktop with a harmless change you set back afterwards (for example the wait time, then back to what it was).

| ID | Do | EXPECT | Result | Notes |
|---|---|---|---|---|
| 5.1 | Settings ▸ Start-up: pick another wait time, **Save Changes (s)** | the review (old → new), your password in grubForge's box; then "Saved · not in the boot menu yet" | | |
| 5.2 | **F9** (or **Rebuild Boot Menu (F9)**) | rebuild progress; the bar clears | | |
| 5.3 | Set the wait time back, **F10**, **Save and Rebuild** | one review, one password, done | | |
| 5.4 | Inside Settings: 3.9, then **Rebuild and Quit** | the password; the rebuild; grubForge closes | | |

## 6 · Words on the outside

| ID | Do | EXPECT | Result | Notes |
|---|---|---|---|---|
| 6.1 | `grubforge --version` | `grubForge 2.2.0` | | |
| 6.2 | `grubforge --help` | the usage; **no** mention of hypeforge | | it's for Settings |
| 6.3 | `man grubforge` | v2.2.0; keys **1 – 6** (6 is Help); "3 - Boot Menu"; no hypeforge | | |
| 6.4 | **M** (manual) ▸ Getting started | "1 – 6", Ctrl + the underlined letter, and the "Inside hypeForge Settings" part | | |
| 6.5 | README on GitHub (after the push) | version 2.2.0; "Inside hypeForge Settings"; keys 1 – 6 | | |

## 7 · Findings

| ID | What | Issue | Status |
|---|---|---|---|
| | | | |
