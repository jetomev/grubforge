# grubForge — v1.0.1-stable retest results

Companion to `20260421 - Test Matrix for grubForge v1-0-1-alpha.md` (same matrix, applied to the post-HF1 stable build instead of the alpha).

## Run metadata

- **Package under test:** `grubforge-1.0.1-1-any.pkg.tar.zst` delivered from AUR (`yay -S grubforge` after `sudo pacman -R grubforge` + `/etc/nog`-style cleanroom)
- **Source commit:** `21fb69b v1.0.1 — HF1 batch closes 15 findings + M4` (the GitHub tag `v1.0.1`); `main` HEAD `9f8aa75` carries the docs catch-up commit but is NOT in the v1.0.1 release tarball
- **Install method:** `yay -S grubforge` against AUR; reproduces the public install path users see
- **Test run started:** 2026-05-15 (Block #1–#4); resumed 2026-05-16 (Block #5–#6); concluded 2026-05-26 (Block #7–#9 after the nog v1.0.4 detour)
- **Tester:** Javier (`jetomev`) + Claude (Anthropic), per `feedback_grubforge_workflow.md`
- **Trigger:** v1.0.1 shipped to AUR + GitHub on 2026-05-05 *without* runtime regression retest — Javier's explicit call: "We will retest another day, and generate another version. Anything that breaks goes into v1.0.2." This run is that retest. Findings here are the v1.0.2 fix scope.

## Pre-test baseline

Captured fresh after clean-room reinstall on 2026-05-15:

- `grubforge` version `1.0.1-1` (HF1 binary, different content from the pre-HF1 build that was on disk prior)
- `/etc/default/grub`: 2101 bytes, sha256 `34484fbc9eada6799782c60df2b19b4d571575454aef45fa3b0349168fae1595`
- `/etc/grub.d/40_custom`: 3505 bytes (user's custom boot entries from prior sessions)
- `/etc/grub.d/`: 10_linux, 30_os-prober, 30_uefi-firmware restored to mode 755 (no `.grubforge_perms` sidecars)
- `/var/lib/grubforge/backups/`: 4 backups accumulated during Block #4's Config Editor save tests (2 of original GRUB_THEME, 2 of cleared GRUB_THEME) — provided live material for Block #5's restore/delete tests

> **F18 watch-for (from v1.0.1-alpha):** `GRUB_GFXMODE 1920x1080,auto` drift state was preserved on disk at session start. Not caused by this run; carried over from v1.0.1-alpha §11. No reproduction observed during this retest.

## Section status

| Section | Title | Status | Notes |
|---|---|---|---|
| 1 | Baseline sanity | pass | grubforge 1.0.1, man page header `v1.0.1`, /etc/nog clean — HF1 versioning landed |
| 2 | Man page content accuracy | pass | F1/F2/F3 v1.0.1-alpha HF1 fixes verified: .TH header reads `v1.0.1`, SYNOPSIS shows `grubforge`/`sudo grubforge` (no dev-tree relics), USAGE clean. Test 2.6 (Javier's content read) deferred to a later man-page pass |
| 3 | Launch & navigation | fail — 2 v1.0.2 findings | F1 (DEMO badge missing), F2 (help "overlay" is notify toast). 3.6 superficially passes only because the badge is also absent in sudo mode — the feature isn't visible at all |
| 4 | Dashboard | pass + 1 v1.0.2 finding (refresh) | F7/F8/F13 v1.0.1-alpha HF1 fixes verified: title-box centred, Config file row shows path, Sync indicator renders. But F3 (Sync color/text mismatch in pending state) and F4 (Active Settings stale on resume) surfaced during deeper exercise |
| 5 | Config Editor — read | pass | All 17 managed keys listed |
| 5 + 7.10 | Config Editor — validator round-trip + save | pass + 1 v1.0.2 finding | F12 v1.0.1-alpha HF1 fix verified (validator accepts empty for optional keys, rejects for required). Cleared GRUB_THEME → saved → committed correctly (4 backups created, /etc/default/grub modified — diff against `/tmp/grubforge-pretest/grub` confirmed it). But F4/F5 surfaced: Dashboard doesn't refresh Active Settings or Backup count after the save mid-session |
| 6 | Config Editor — edit & save | pass | Round-trip clean (per Block #4 Phase B) |
| 7 | Theme Browser | pass + 1 v1.0.2 finding | F4/F5 v1.0.1-alpha HF1 fixes (theme apply worker pattern, F13 first round) verified. F12 v1.0.2 (popup directs user to Config Editor for Ctrl+R regen — encodes the F7 limitation) found |
| 8 | Backup & Restore — button paths | pass + 1 v1.0.2 finding | F14 v1.0.1-alpha HF1 fix verified (Create/Restore/Delete buttons all fire without WorkerError). F6 v1.0.2 found (preview pane non-scrollable). Auto-pre-restore backup feature confirmed working as a positive observation |
| 8 (priority) | Backup screen N keybinding without focus | fail — 1 v1.0.2 finding | F15 v1.0.2 — HF1's `priority=True` fix did NOT take effect; N still inert until panel is clicked |
| 9 | Boot Entries | not directly run | Boot order / custom entry creation paths not exercised this retest. Block #7 universal-bindings sweep confirmed S on Boot Entries fires `action_save_order` correctly with the expected confirmation dialog text |
| 10 | Safety flow | not directly run | F17 v1.0.1-alpha HF1 fix (demo-mode friendly messages instead of EPERM) verified via Block #9; all three write paths (Backup Create, Config save, Theme Apply) emit `Read-only mode — relaunch with sudo to <action>.` cleanly |
| 11 | Cleanup & state verification | not run | Test article state preserved across sessions; section 11 would have wiped via §8.7 anyway. Pre-test snapshot at `/tmp/grubforge-pretest/grub` lost to reboot between sessions |
| F13 reboot validation | F13 reboot validation | **pass** | Real-world reboot with tela theme active: GRUB menu rendered tela at boot. End-to-end theme apply → grub.cfg regen → bootloader displays new theme works correctly |
| Universal-bindings sweep | (new section) | pass + 6 v1.0.2 findings | Dispatcher mechanism healthy (`n/a` cells correctly emit notifies). But F9/F10/F11 (inconsistent feedback location, Dashboard R silent, Dashboard Ctrl+R first-press silent) + F13 v1.0.2 (Config Editor A keyboard mismatch) + F14 v1.0.2 (Config Editor E no-key-selected edge) found |
| Section 16/17 | (n/a) | n/a | grubforge doesn't have nog-style sections 15–17. Listed here only for ordering reference |

Status legend: `pending` / `pass` / `pass with findings` / `fail` / `not run`.

---

## v1.0.1-alpha HF1 fixes verified working in this retest

For completeness, the HF1 fixes from v1.0.1-alpha (closed 14 of 18) that landed correctly and are confirmed on the v1.0.1-stable AUR binary:

- **F1** (v1.0.1-alpha) — man page .TH header reads v1.0.1 ✓
- **F2** (v1.0.1-alpha) — SYNOPSIS shows `grubforge`/`sudo grubforge`, no dev-tree ✓
- **F3** (v1.0.1-alpha) — USAGE section clean, no dev-tree ✓
- **F7** (v1.0.1-alpha) — Dashboard title-box centred and closed ✓
- **F8** (v1.0.1-alpha) — Config file row shows `/etc/default/grub` ✓
- **F12** (v1.0.1-alpha) — Validator accepts empty for optional keys, rejects for required ✓
- **F13** (v1.0.1-alpha, first round) — Theme apply → grub.cfg regen → reboot shows new theme ✓
- **F14** (v1.0.1-alpha) — Backup screen Create/Restore/Delete buttons fire without WorkerError ✓
- **F17** (v1.0.1-alpha) — Demo-mode write attempts emit friendly read-only messages ✓

**Cleared (not present in v1.0.1):**

- **F4** (v1.0.1-alpha — DEMO badge in sidebar) — DID NOT land in v1.0.1. The code is in `app.py:213-219` with correct conditional logic but the badge is not visible in either demo or sudo mode. **Re-opened as v1.0.2 F1.**
- **F5** (v1.0.1-alpha — help overlay close hint) — Partially closed: HF1 added the hint text inside a `self.notify(...)` call, but the underlying widget is still a notification toast, not a proper modal. **Re-opened as v1.0.2 F2.**
- **F13** (v1.0.1-alpha, second round — universal Ctrl+R from any screen) — Partially closed: dispatcher pattern works (non-supporting screens emit "not available" notifies), but only Config Editor implements `action_regen_grub` so Ctrl+R from other screens does nothing. **Re-opened as v1.0.2 F7.**
- **F15** (v1.0.1-alpha — Backup screen keybindings require focus-into-panel) — DID NOT land. N still inert until panel is clicked. **Re-opened as v1.0.2 F15.**

---

## Findings — v1.0.2 scope

Numbered F1–F15. Each follows the structured format.

### F1 — DEMO badge not rendering in demo mode

- **Test:** 3.2 (and corollary 3.6)
- **Expected:** Red "DEMO" tag visible in the sidebar under the logo when launched without sudo; absent when launched with sudo
- **Actual:** Not visible in either mode. Sidebar shows logo/title without the badge
- **Severity:** major (silent state — defeats the v1.0.1-alpha F4 intent; user can't tell at a glance whether destructive actions will write or no-op)
- **Code:** `app.py:213-219` — `_logo(read_only)` builds the right string with Catppuccin Mocha `[bold #f38ba8 reverse] DEMO [/...]` styling. Logic correct (`read_only_mode = os.geteuid() != 0`). Issue is at render layer.
- **Proposed fix:** inspect `grubforge.css` for `#sidebar-logo` height constraint that may be clipping the third line containing the badge. Alternatively, verify Rich `reverse` style renders correctly in the chosen Static widget — may need to switch widget primitive or reposition the badge to a separate element.

### F2 — Help "overlay" is a notification toast, not a modal

- **Test:** 3.4
- **Expected:** `?` toggles a help overlay; Esc closes; close-hint visible
- **Actual:** `?` shows a notify toast (no toggle — stacks); Esc has no effect; popup auto-dismisses after 8 seconds (Textual's default notify timeout). The body text contains "Press Esc to close (auto-dismisses in 8s)" but the close action it advertises doesn't work because it's the wrong widget primitive.
- **Severity:** major (multiple sub-failures, wrong widget primitive)
- **Code:** `app.py:163-171` uses `self.notify(...)` with `timeout=8`
- **Proposed fix:** replace with a proper `ModalScreen` subclass:
  ```python
  class HelpScreen(ModalScreen):
      BINDINGS = [
          Binding("?", "dismiss", show=False),
          Binding("escape", "dismiss", show=False),
          Binding("q", "dismiss", show=False),
      ]
  ```
  `action_show_help` pushes via `self.push_screen(HelpScreen())`. If already-shown, dismiss instead of stack (proper toggle). Standard Textual pattern.

### F3 — Sync indicator color/text mismatch in pending-changes state

- **Test:** 4.1c (extended)
- **Expected:** Sync row color and text agree — green ✓ "in sync" when clean, yellow ⚠ "grub.cfg older" when drift
- **Actual:** When app has pending unsaved edits, Sync row reads `✓ in sync` (text) but rendered in **yellow color**. Two states conflated into a misleading display.
- **Severity:** minor (visual inconsistency, not data-loss)
- **Proposed fix:** introduce a third state — `⚠ pending changes` (text + yellow) when app has uncommitted edits, distinct from `⚠ grub.cfg older` (disk-side drift). Reserve `✓ in sync` for fully clean state. Likely a few-line change to the Sync row's reactive computation in Dashboard.

### F4 — Dashboard Active Settings doesn't refresh after Config Editor saves

- **Test:** 4.1b after 7.10
- **Expected:** After a Config Editor save commits to `/etc/default/grub`, visiting Dashboard re-reads the file and shows current values
- **Actual:** `GRUB_THEME /boot/grub/themes/windows-11/theme.txt` displayed even when disk has the cleared state (confirmed via sha256 of `grub_20260515_204425_674039.bak` = `1a39557d...`; that backup of the cleared state was captured at the moment of observation, so disk WAS cleared but Dashboard showed stale).
- **Severity:** major (users believe their saves didn't take effect when they did)
- **Proposed fix:** invalidate Active Settings cache on `on_screen_resume` of Dashboard; re-read `/etc/default/grub` each time the screen is shown.

### F5 — Dashboard Backup count doesn't refresh after backups are created

- **Test:** 4.1d after 7.10 and 8.2 (Create button)
- **Expected:** `Backup count N saved in /var/lib/grubforge/backups` reflects current directory contents
- **Actual:** Shows `0 saved` even with 4 backups on disk after Config Editor saves; later showed 4 while disk had 6 (after Create + Restore auto-backup + Delete cycle).
- **Severity:** major (Backup screen entry-point label is permanently wrong post-startup)
- **Proposed fix:** re-glob `/var/lib/grubforge/backups/*.bak` on Dashboard `on_screen_resume`; bind count to current value, not a startup-cached counter.

### F6 — Restore preview pane non-scrollable

- **Test:** 8.5 (extended)
- **Expected:** Ability to scroll the preview pane to see the entire backup content (~41 lines)
- **Actual:** Arrow keys, PgDn/PgUp, mouse wheel — none scroll the preview pane. Cap at ~21 lines visible. The backup list panel scrolls fine with arrows; the preview panel uses a different widget type that doesn't have a scroll handler.
- **Severity:** minor (user can't visually verify the lower portion of a backup — GRUB_THEME, GRUB_GFXMODE, GRUB_DISABLE_OS_PROBER all live below the fold)
- **Proposed fix:** wrap the preview Static in a `ScrollableContainer`, or use a `RichLog` / `TextArea` widget that has built-in scroll bindings.

### F7 — Ctrl+R "universal" binding only fires regen from Config Editor

- **Test:** 4.1 + Block #7 + F13 reboot validation
- **Expected per HF1:** Ctrl+R triggers grub-mkconfig regen from **any** screen
- **Actual:** Only Config Editor responds. From Dashboard/Themes/Backup/Boot Entries the binding fires `action_global_regen` → dispatches to a screen-local `action_regen_grub` method that only Config Editor implements → silent no-op or "not available" notify. The Sync indicator on Dashboard literally tells the user "press Ctrl+R to regenerate" and Ctrl+R from Dashboard does nothing.
- **Severity:** major (defeats HF1's headline behavior, misleading Sync prompt)
- **Code:** `app.py:163` `action_global_regen` calls `_dispatch(["action_regen_grub"], "Regenerate grub.cfg")` which is screen-local
- **Proposed fix:** refactor `action_global_regen` to **run `grub-mkconfig` directly at app level**, not dispatch to active screen. Similar shape for `action_global_refresh` (Dashboard's R fires silently — see F10) — these "universal app actions" should not depend on screen-local methods. F7 + F11 + F12 all close with one architectural fix.

### F8 — Screens don't auto-refresh after state-changing actions

- **Test:** 4.1 + 7.x after theme apply + Block #5
- **Expected:** After an action that changes disk state (theme apply, config save, Ctrl+R regen), the visible app state updates
- **Actual:** After theme apply: Backup screen didn't show the new auto-backup; Dashboard didn't show new GRUB_THEME until manual `R`. After Ctrl+R regen completed: Config Editor still showed stale GRUB_THEME until manual `R` press. Dashboard on resume after Config Editor save: still showed `windows-11` until manual `R` press.
- **Severity:** major (broader pattern that unifies F4 + F5)
- **Proposed fix:** every screen re-reads its disk state on `on_screen_resume`. Post-action handlers (theme apply, config save, Ctrl+R regen) explicitly call refresh on completion. F4 + F5 + F8 collapse into one design fix.

### F9 — Inconsistent feedback location across global bindings

- **Test:** Block #7 universal-bindings sweep
- **Expected:** Consistent feedback location for all global-binding outcomes
- **Actual:** "Isn't available on this screen" notifies fire as **bottom-right popups**. But successful action feedback fires as **blue text at the bottom of the screen**:
  - Config Editor S (no pending changes): "- No pending changes to save" (blue text bottom)
  - Config Editor R: "- Config reloaded from disk" (blue text bottom)
  - Themes R refresh: blue text bottom
  - Backup R refresh: blue text bottom
  - Boot Entries R refresh: blue text bottom
- **Severity:** minor (UX inconsistency — Javier's call: "all this message should appear in popups on the bottom right, as the other popups, to maintain certain visual and function standard and logic/consistency")
- **Proposed fix:** route both success and failure feedback for global bindings through the same notify popup pattern. Single helper function for "global binding status" emits everywhere.

### F10 — Dashboard R has no visible feedback

- **Test:** Block #7 Dashboard R
- **Expected:** Some indication that refresh fired (status message, brief animation, etc.)
- **Actual:** Pressing R on Dashboard produces no visible message. Action DOES fire (confirmed May 16 when manual R post-theme-apply correctly updated GRUB_THEME and Sync indicator), but user has no signal that anything happened.
- **Severity:** minor
- **Proposed fix:** emit "Dashboard refreshed" notify (or blue-text if F9 lands the other direction). Consistent with F9's resolution.

### F11 — Dashboard Ctrl+R first press silent, second press emits notify

- **Test:** Block #7 Dashboard Ctrl+R
- **Expected:** First press emits "Regenerate grub.cfg isn't available on this screen" notify (per F7's current dispatch behavior)
- **Actual:** First Ctrl+R: silent. Second Ctrl+R: shows the notify.
- **Severity:** minor (notify dedup/timing artifact; becomes moot once F7 fix lands and Ctrl+R fires the actual regen)
- **Proposed fix:** investigate why the first press doesn't reach the dispatcher. Likely first-press eaten by focus state or race-condition with binding registration. F7's fix supersedes this.

### F12 — Themes Apply popup directs user to Config Editor for Ctrl+R regen

- **Test:** Block #7 Themes A (Apply)
- **Expected:** Apply popup describes what apply does without cross-screen instructions
- **Actual:** Popup says "Go to Config Editor and press Ctrl-R to regenerate grub.cfg after applying" — encodes the F7 limitation right into user-facing flow text. The natural workflow (apply → regen) requires switching screens.
- **Severity:** minor (incidental documentation of the F7 bug)
- **Proposed fix:** once F7 lands (Ctrl+R works from any screen), update the popup to either (a) auto-regen on apply, (b) offer a "Regenerate now (Ctrl+R)" button inline, or (c) simply say "press Ctrl+R to regenerate" without the cross-screen instruction.

### F13 — Config Editor `A` keybinding rejects but "Apply Edit" button works

- **Test:** Block #7 Config Editor A
- **Expected:** Keyboard `A` fires the same action as the on-screen "Apply Edit" button
- **Actual:** Keyboard `A` shows the "Apply isn't available on this screen" notify, but clicking the "Apply Edit" button DOES apply the change. Dispatch mismatch.
- **Severity:** major (Javier's call: "The A - press should execute the same command as the button, I think.")
- **Code:** the screen widget has an apply method but the global dispatcher (`action_global_apply` → `_dispatch(["action_apply_theme"], "Apply")`) looks for `action_apply_theme` only. Config Editor has `action_apply_edit` (probably).
- **Proposed fix:** extend the dispatcher's lookup list to `["action_apply_edit", "action_apply_theme"]`, OR rename the screen widget's apply method to match. Same pattern probably applies to S (lookup is already `["action_save_changes", "action_save_order"]` — proves the multi-name pattern works).

### F14 — Config Editor `E` without key selected focuses Edit area but no-ops

- **Test:** Block #7 Config Editor E
- **Expected:** Pressing E with no key selected gives a meaningful response (error notify "select a key first", or auto-select first key, or just no-op silently)
- **Actual:** Cursor focuses the Edit area but there's nothing to edit. Confusing.
- **Severity:** minor (UX edge case)
- **Proposed fix:** either reject with "Select a key first" notify, OR auto-select the first key, OR no-op silently with no UI change.

### F15 — Backup screen N keybinding still requires focus-into-panel

- **Test:** Block #8 (F15 v1.0.1-alpha retest)
- **Expected per v1.0.1-alpha HF1:** N fires Create Backup dialog on screen entry without needing a panel click first; `priority=True` added to BINDINGS
- **Actual:** N is inert until you click into the backup-list area. Then it fires.
- **Severity:** minor (workflow works after the click, but inconvenient and contradicts HF1's promise)
- **Proposed fix:** inspect `screens/backup.py` BINDINGS declaration vs `screens/themes.py:27` (which uses `priority=True` correctly for the H install help binding — that one works). Likely needs to move the binding to Screen-level rather than container-level. ~5 lines.
- **Also:** verify X (restore) and D (delete) on Backup screen exhibit the same pattern in next session — likely same fix covers all three.

---

## Cross-validation: imports / smoke / source dives

- **Imports smoke:** `python -c "import grubforge"` clean (no module-level errors). Implicit via `yay -S grubforge` install success.
- **CSS file:** `grubforge/grubforge.css` present and packaged. Need direct inspection to resolve F1 (sidebar-logo height).
- **App-level bindings:** confirmed in `app.py:70` for `?`, `q`, `ctrl+c`, `1-5` navigation, `e`/`s`/`a`/`r`/`ctrl+r` global dispatchers. Dispatcher pattern in `app.py:178-200` works as designed (notify on missing method).
- **Demo-mode strings:** `_set_status("Read-only mode — relaunch with sudo to ...", "warn")` calls present across `screens/backup.py`, `screens/boot_entries.py`, `screens/config_editor.py`, `screens/themes.py` — F17 verification was therefore expected to pass and did.

---

## v1.0.2 hotfix batch — preliminary grouping

15 findings → likely 4-5 thematic fix groups. Sketch for the v1.0.2 design conversation (next):

1. **Dashboard / screen refresh** (F3, F4, F5, F8, F10): `on_screen_resume` re-read, unified status display, F3's third "pending changes" state
2. **Global bindings architecture** (F7, F11, F12, F13): move regen + refresh to app-level (not screen-dispatched); extend Apply dispatcher to include `action_apply_edit`; update Themes Apply popup text after F7 fix
3. **Feedback surface unification** (F9): all global-binding outcomes (success, error, not-available) through one notify popup helper
4. **Discrete widget bugs** (F1 CSS, F2 ModalScreen replacement, F6 ScrollableContainer, F14 E edge, F15 priority)

Plus optional: address the smaller F11/F12/F14 edges naturally in their parent groups.

Conservative scope estimate: **~250-350 lines** across `app.py`, `screens/dashboard.py`, `screens/backup.py`, `screens/config_editor.py`, `screens/themes.py`, and `grubforge.css`. Phase-commit pattern from nog's discipline applies — single Phase commit per group, then docs/version bump commit, then tag.

---

## Findings summary table

| # | Title | Severity | Group |
|---|---|---|---|
| F1 | DEMO badge not rendering | major | Discrete widget |
| F2 | Help "overlay" is notify toast | major | Discrete widget |
| F3 | Sync color/text mismatch in pending | minor | Dashboard refresh |
| F4 | Dashboard Active Settings stale | major | Dashboard refresh |
| F5 | Dashboard Backup count stale | major | Dashboard refresh |
| F6 | Restore preview non-scrollable | minor | Discrete widget |
| F7 | Ctrl+R only fires from Config Editor | major | Global bindings |
| F8 | No auto-refresh after state changes | major | Dashboard refresh |
| F9 | Feedback location inconsistent | minor | Feedback surface |
| F10 | Dashboard R has no visible feedback | minor | Feedback surface |
| F11 | Dashboard Ctrl+R first press silent | minor | Global bindings |
| F12 | Themes popup encodes F7 limitation | minor | Global bindings |
| F13 | Config Editor A keyboard mismatch | major | Global bindings |
| F14 | Config Editor E no-key-selected edge | minor | Discrete widget |
| F15 | Backup N priority regressed | minor | Discrete widget |

**Severity:** 6 major + 9 minor = 15 total.

---

## Next-session handoff

**Pick up at:** v1.0.2 hotfix batch design conversation. Group findings by theme (sketch above), agree on scope + sequence, then execute.

### Open findings remaining

All 15 listed above; none deferred to v2+ from this run (the discrete widgets are all reasonable to fix in v1.0.2).

### Open hotfix batches

v1.0.2 batch — drafted thematically above, not yet implemented.

### Sections remaining (none — retest complete)

All 9 blocks of the regression slice are complete. Block #6's F13 reboot validation closed clean via the May 16 → May 17 reboot. No further regression-slice work pending.

### Watch-fors

- **Verify X and D on Backup screen exhibit same F15 priority issue** — only N was tested today. Same screen, same fix expected. Quick verification next session before fix lands.
- **F1 CSS investigation needs direct file read** — `grubforge.css` and the Static widget definition for `#sidebar-logo` should be inspected to determine the exact constraint clipping the badge.
- **F11 may be a Textual focus-timing artifact** — could become moot if F7 fix runs the regen at app level instead of dispatching. Don't fix F11 in isolation; treat F7's fix as the closing change for both.

### Test article state

- **Installed:** `grubforge 1.0.1-1` (still from May 15 cleanroom; AUR hasn't moved)
- **Repo HEAD:** `9f8aa75` on `main` — same as start of run; no commits this run
- **AUR HEAD:** `8e3870c` on `master` — unchanged; v1.0.1-1 still live
- **Disk state:** `/etc/default/grub` at original baseline (`34484fbc...`); `.grubforge_perms` sidecars present from intervening sessions (May 18–21 Javier work); 10_linux/30_os-prober/30_uefi-firmware at mode 644 (disabled); `40_custom` unchanged at 3505 bytes
- **Backups on disk:** unknown current count (sudo required to verify; not blocking — Block #5 had verified 4 → 6 → 5 cycle correctly across May 15-16)
- **Pre-test snapshot:** lost to reboots (recapture if needed next session for §11)
- **Reminder:** **read this Test Results doc + the May 15 vault log (`grubForge - (12) Part 11.md`) first next session**, before memory or repo inspection.
