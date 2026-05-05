# grubForge — v1.0.1-alpha test results

Companion to `20260421 - Test Matrix for grubForge v1-0-1-alpha.md`.

## Run metadata

- **Package under test:** `grubforge-1.0.1-1-any.pkg.tar.zst` (built from `~/Programs/aur-grubforge/`)
- **Source commit:** `4490187 Fix theme apply worker pattern for Textual compatibility` (untagged, on top of `v1.0.0`)
- **Install method:** `sudo pacman -U` against the locally built package (reproduces AUR install layout)
- **Test run started:** 2026-04-24
- **Tester:** Javier (`jetomev`) + Claude (Anthropic), per `feedback_grubforge_workflow.md`

## Pre-test baseline (`/etc/default/grub` + backups dir, captured 2026-05-02 at start of §4)

Cleanup verification (§11) compares against these values. Do not edit during the run.

- `GRUB_DEFAULT=0`
- `GRUB_TIMEOUT=10`
- `GRUB_GFXMODE="1920x1080"`
- `GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet"`
- `GRUB_THEME="/boot/grub/themes/windows-11/theme.txt"`
- `GRUB_DISABLE_OS_PROBER=false`
- Backups: **7 backups** (14 files in `/var/lib/grubforge/backups/` — each backup is a paired `.bak` + `.bak.label`)
- Boot entries (per dashboard): 6
- `/etc/grub.d/40_custom`: state TBD (will check at start of §9 — currently presumed absent or empty since no boot-entries reorder has been done in this run)

**Amendments during run:**

- **2026-05-02 ~19:55 (between §4 capture and §7 launch):** Javier installed the `tela` GRUB theme via package manager (external to grubForge). Tela's post-install hook auto-set `GRUB_THEME="/boot/grub/themes/tela/theme.txt"` and ran `grub-mkconfig`. grubForge's Theme Browser correctly identified tela as active when refreshed via F5 — positive incidental validation of the active-theme indicator.
- **2026-05-02 20:13:49 (during 7.10):** Javier chose to follow the matrix's literal "apply the original theme" revert path and applied `windows-11` via Theme Browser. **Effective baseline for §11 GRUB_THEME is back to `windows-11`** (matches the original pre-test capture). The intermediate "tela as new baseline" amendment is rescinded.

## Section status

| Section | Title | Status | Notes |
|---|---|---|---|
| 1 | Baseline sanity | pass | textual 8.2.3, rich 15.0.0; man page opens but content issues land in §2 |
| 2 | Man page content accuracy | fail (hotfix deferred) | 3 findings (F1–F3); hotfix batched to end of run (Javier's call — testing may surface behavior changes that affect doc wording); 2.6 (Javier's read) also deferred to the final man page pass |
| 3 | Launch & top-level navigation | pass with findings (hotfix deferred) | F4 (3.2 + 3.6 — no mode indicator), F5 (3.4 — overlay close not discoverable); F6 (3.7 — Boot Entries panel cramped) deferred to v2+ |
| 4 | Dashboard | pass with findings (hotfix deferred) | 4.2 + 4.3 pass (parse accurate; 7 backups confirmed via paired-file convention); F7 (4.1 — title box misaligned), F8 (4.1 — config file path missing); 4.4 covered by F4; M2 refinement on 4.3 |
| 5 | Config Editor — read | pass with findings (deferred) | All 17 keys present, descriptions/values render, raw `/etc/default/grub` preview works, commented-out keys visually distinct; F9 (5.1 + 5.5 — small-terminal layout cramping, right edit panel occludes content) deferred to v2+ alongside F6 |
| 6 | Config Editor — edit & save | pass | All 9 tests pass; GRUB_TIMEOUT 10→15→10 round-trip clean; +2 backups (193902 + 194122); validator rejected `abc` without writing (no phantom backup); grub-mkconfig regenerated grub.cfg (mtime 19:41:26); revert verified — /etc/default/grub matches pre-test baseline |
| 7 | Theme Browser (regression focus) | pass with findings — REGRESSION BUG DEAD **for theme-apply only**; **post-session reboot surfaced F13 (major)**; **§8 later revealed the same async-worker pattern alive in backup.py — see F14** | All 11 matrix tests pass in-session; **4 back-to-back theme applies succeeded with zero worker errors** (over-satisfies 7.9); F5 correctly detected externally-installed tela as active (incidental win); 7.10 reverted to windows-11 baseline via Theme Browser; 7.11 cancel path verified clean. **However:** Javier rebooted post-session and the bootloader displayed `tela` instead of `windows-11` — Theme Apply had updated `/etc/default/grub` but not regenerated `grub.cfg`. See F13. **Findings:** F11 (right panel cramped — deferred to v2+); F12 (Config Editor blocks empty-value save for GRUB_THEME — joins HF1); **F13 (Theme Apply silently leaves grub.cfg stale; Ctrl+R regen scoped to Config Editor only — joins HF1, MAJOR)**; M3 refinement on preamble |
| 8 | Backup & Restore | pass with findings — **MAJOR (F14)** | All 10 matrix tests functionally pass via keybindings (B / R / D / F5 / cancel-paths). 8.1 listed 18 backups (drift from session start; external activity over past days). 8.4 preview rendered. 8.7 destructive cleanup deleted all listed backups one-by-one via keybinding-D — backup-set is intentionally cleared (note for §11). **Findings:** **F14 (MAJOR — Backup screen buttons throw `WorkerError: Unsupported attempt to run an async worker` for Create/Restore/Delete; keybinding paths work; the 4490187 theme-apply fix did NOT propagate to backup.py — same broken `@work` + `run_worker(self.action_X())` pattern alive)**; F15 (keybindings inert until focus is inside the section — pressing `B` did nothing until Javier clicked into the panel); F16 (footer's `R Refresh` collides with section's `R Restore`; refresh-via-R doesn't work in §8); M4 (no backup retention cap — Javier asks: should we cap at e.g. 10?) |
| 9 | Boot Entries | pass — no new findings | All 10 matrix tests pass. **Dedup-on-display confirmed:** UI showed 1 row for the 3× duplicate `Arch Linux snapshots` entries on disk in `40_custom` (pre-test state); 9.5 Save wrote back the deduped state; 9.7 Restore Original wiped `40_custom` to stock template — the duplicate state has been absorbed cleanly. **Perms-strip mechanism (README:211) verified clean:** Save disabled `10_linux` / `30_os-prober` / `30_uefi-firmware` via `.grubforge_perms` sidecars; Restore Original consumed sidecars and restored mode 755. **Kernel-update implication of perms-strip not currently documented in user-facing copy** → folded into HF1 as a README/man-page doc clarifier (no code change). **Watch-for resolutions:** F13 confirmed scoped to Theme Apply only (Save Order regens grub.cfg correctly); F14 button paths all clean (boot_entries.py audit verified); F15 does NOT recur (bindings fired immediately on screen entry — F15 likely screen-local to backup.py); F16 recurs in shape (`R Restore Original` shadows footer `R Refresh`) — observed only, already covered by existing finding |
| 10 | Safety flow | pass with finding (F17) | 10.1/10.2 verified retrospectively across §6–§9. 10.3 indeterminate (post-§8.7 destructive cleanup wiped run-spanning backup history — matrix-process gap **M6**). 10.4 surfaces **F17** — demo-mode write attempts return `[Errno 13] Permission denied` rather than a graceful "read-only mode" message; same EPERM pattern across Backup screen `B` and Config Editor `S`. Pairs with **F4** under the same demo-mode-detection fix. 10.5 verified clean (validation errors surface in-app without tracebacks) |
| 11 | Cleanup & state verification | pass with finding (F18) + matrix gap (M5) | `/etc/default/grub`: 5/6 keys match pre-test exactly; **GRUB_GFXMODE drift** from `"1920x1080"` → `1920x1080,auto` cannot be conclusively attributed to grubForge (no surviving pre-test backup — see **M6**); Javier's call: log as **F18** for HF1 code investigation (audit `config_manager.py` save logic for unintended cross-key normalization; check whether theme apply touches GFXMODE). `/etc/grub.d/40_custom` cleanup successful (stock 212-byte template, no `.grubforge_perms` sidecars, auto-detect scripts back to 755) — but only after a remedial Restore Original cleanup; **matrix gap M5**: §9 ordering leaves the system in custom-order-active state because 9.8 (Create Custom Entry) saves AFTER 9.7 (Restore Original) — add explicit final-restore step at end of §9. 11.5 reboot deferred to post-HF1 retest (paired with F13 reboot validation) |

Status legend: `pending` / `pass` / `pass with findings` / `fail` / `skipped`.

---

## Findings

Numbered `F1`, `F2`, … one per failed test. Each finding records:

- **Test:** matrix ID (e.g., `7.6`)
- **Expected:** what the matrix said should happen
- **Actual:** what was observed (paste output / describe symptom)
- **Severity:** blocker / major / minor / polish
- **Proposed fix:** if obvious; otherwise `TBD`

### F1 — man page footer reports stale version

- **Test:** 2.1
- **Expected:** `.TH` footer reads `v1.0.1`
- **Actual:** footer reads `GrubForge v0.8.0   April 2026   GRUBFORGE(1)`
- **Severity:** major (public artifact wrong on stable release)
- **Proposed fix:** bump the `.TH` line in `grubforge.1` to `v1.0.1`; consider adding a release-prep checklist item or templating the version

### F2 — SYNOPSIS shows dev-tree invocation

- **Test:** 2.2
- **Expected:** `sudo grubforge` (the packaged launcher)
- **Actual:** `sudo python main.py`
- **Severity:** major (misleads packaged users; the man page ships *with* the package)
- **Proposed fix:** rewrite SYNOPSIS to `grubforge` / `sudo grubforge`

### F3 — USAGE section has dev-tree relics

- **Test:** 2.3
- **Expected:** `grubforge` (full write with sudo) and `grubforge` (demo without sudo)
- **Actual:** `cd ~/Programs/grubforge && sudo python main.py` and `cd ~/Programs/grubforge && python main.py`
- **Severity:** major (same root cause as F2 — man page wasn't updated when the launcher shim landed)
- **Proposed fix:** rewrite USAGE block to use the `grubforge` launcher form

### F4 — no demo-mode / full-access indicator anywhere in the UI

- **Test:** 3.2 (and corollary 3.6)
- **Expected:** demo-mode indicator visible somewhere (footer, dashboard, or title) when launched without sudo; full-access mode visibly distinct when launched with sudo
- **Actual:** no indicator visible in either mode — `grubforge` and `sudo grubforge` look identical; user has no signal whether destructive actions will write to disk or no-op
- **Severity:** major (silent state — risk of user thinking they edited config when they didn't, or vice versa)
- **Proposed fix:** add a small "DEMO" tag in red letters under the app title (top-left), shown only in demo mode (Javier's suggestion). Absence of the tag in sudo mode = full-access. Single fix covers both 3.2 and 3.6, plus likely 4.4 (dashboard demo-flag)

### F5 — help overlay (`?`) has no close-method hint

- **Test:** 3.4
- **Expected:** help overlay opens with `?` and closes intuitively (via `?` toggle or `Esc`)
- **Actual:** overlay opens correctly in the bottom-right; closes via `?`/`Esc` (assumed working — confirm at hotfix re-test), but the overlay itself contains no indication of how to close it. User has to guess
- **Severity:** minor (polish — discoverability gap, not a functional break)
- **Proposed fix:** add a hint line to the overlay text — e.g., "Press `?` or `Esc` to close" — and/or make the overlay click-to-close (Javier's suggestion). Hint line is the cheaper hit; click-to-close is additive

### F6 — Boot Entries right-panel cramped at smaller terminal sizes — DEFERRED to v2+

- **Test:** 3.7 (resize behavior)
- **Expected:** layout reflows cleanly across terminal sizes; no buttons hidden
- **Actual:** Boot Entries (screen 5) right panel — edit options + buttons — feels cramped at standard sizes; some buttons get hidden or clipped depending on terminal width
- **Severity:** minor (visual / discoverability — does not break functionality)
- **Proposed fix:** **DEFERRED to v2 or v3** per Javier's call. Window arrangement, button sizing, label naming all need a coherent rework — out of scope for v1.0.1. Carry forward as known issue and v2 backlog item; do NOT include in HF1

### F7 — Dashboard title-bar box drawing misaligned

- **Test:** 4.1 (visual observation during dashboard inspection)
- **Expected:** the `╔═══╗ / ║ … ║ / ╚═══╝` box around "GrubForge — System Overview" closes cleanly — corners (`╗`, `╝`) align with the right `║` on the title row
- **Actual:** the top/bottom `═══` rules are 1–2 characters shorter than the title row; the right `║` floats out past the corners. Box looks broken/unclosed
- **Severity:** minor (cosmetic, but visible on the home screen of a stable release)
- **Proposed fix:** width-calc bug in the title widget. Either compute box width from the rendered title length (incl. padding) or hard-pad the title row to match the box width

### F8 — Dashboard "Config file" row shows status only, no path

- **Test:** 4.1 (matrix asks for "config file path" + "config status")
- **Expected:** dashboard shows the config file **path** (`/etc/default/grub`) alongside the status (Found / Missing) — matching the format of the `grub.cfg` row, which shows both
- **Actual:** only the status appears — `Config file    ✓ Found`. Path is implicit/absent. The `grub.cfg` row by contrast reads `grub.cfg       ✓ /boot/grub/grub.cfg`
- **Severity:** minor (information-completeness gap; users have to *know* the standard path)
- **Proposed fix:** mirror the `grub.cfg` row format on the `Config file` row — `Config file    ✓ /etc/default/grub`

### F9 — Config Editor (screen 2) layout cramped at smaller terminal sizes — DEFERRED to v2+

- **Test:** 5.1 + 5.5
- **Expected:** all 17 managed keys remain visible/accessible across terminal sizes; right-side edit panel doesn't occlude the key list
- **Actual:** at smaller terminal widths the right edit panel covers part of the key list — keys exist and the count is correct, but some are hidden behind the panel until the terminal is widened
- **Severity:** minor (visual / discoverability — does not break functionality; keys are reachable when the terminal is large enough)
- **Proposed fix:** **DEFERRED to v2 or v3** per Javier's call. Same family as F6 (Boot Entries) — both screens need a coherent TUI layout pass. Carry forward as part of a unified v2 layout epic; do NOT include in HF1

### F12 — Config Editor rejects empty value when saving `GRUB_THEME` (and likely other optional keys)

- **Test:** 7.10 (matrix expects clear-via-Config-Editor as a valid revert path)
- **Expected:** Config Editor allows clearing optional keys like `GRUB_THEME` by saving an empty value (which means "no theme" — a legitimate GRUB state)
- **Actual:** validator rejects with "cannot save it empty" — the same error path used for required-but-blank inputs. No distinction between required keys (where empty is invalid) and optional keys (where empty = "unset")
- **Workaround used:** Javier reverted by applying `windows-11` via Theme Browser instead. Functional revert achieved, but the matrix-expected path is broken
- **Severity:** minor (workaround exists; only affects users who want to fully clear an optional key rather than overwrite it)
- **Proposed fix:** distinguish required vs optional keys in the validator. Likely lives in `config_manager.py` — check the schema for an `optional`/`required` flag (or add one if absent). For optional keys, treat empty input as either "comment out the line" or `KEY=""` — both are valid GRUB states. Affects (at least) `GRUB_THEME`, `GRUB_BACKGROUND`, possibly `GRUB_TERMINAL_INPUT`/`OUTPUT`. Other optional keys to be enumerated at hotfix time

### F11 — Theme Browser (screen 3) right-panel cramped at smaller terminal sizes — DEFERRED to v2+

- **Test:** 7.2
- **Expected:** detail header / color palette / theme.txt preview render fully across terminal sizes
- **Actual:** right-side detail panel gets clipped at smaller terminal widths — "very uncomfortable" per Javier
- **Severity:** minor (visual; doesn't break functionality)
- **Proposed fix:** **DEFERRED to v2 or v3** per Javier's call. Third confirmed surface in the same family — F6 (Boot Entries) + F9 (Config Editor) + F11 (Theme Browser) all show the same cramped-right-panel pattern at smaller widths. Strong signal that the v2 layout work is one coherent epic across multiple screens, not three isolated fixes

### F10 — Title bar uses legacy "GrubForge" instead of canonical "grubForge"

- **Test:** 3.1 (matrix accepts either spelling; project memory mandates "grubForge")
- **Expected:** "grubForge" — lowercase g, capital F — matching the canonical project name (memory: "grubForge (lowercase g, capital F — this is the canonical spelling; update README/PKGBUILD/GitHub to match)")
- **Actual:** title bar reads "GrubForge" (legacy). Per Javier (2026-05-02): "Title Brand, inside the app, and in all documents and code files is 'grubForge'."
- **Severity:** minor (branding consistency, but stable-release-relevant)
- **Proposed fix:** sweep `GrubForge` → `grubForge` across:
  - App title widget (visible string on dashboard)
  - All `*.md` in repo (README, etc.)
  - Source files (`*.py`) — anywhere "GrubForge" appears as a label/title/string
  - Man page (already touched by F1–F3 hotfix)
  - PKGBUILD comments / co-author lines if any
  - **EXCLUDE** the legacy vault folder name (`~/Google Drive/Rullynastre/GrubForge/`) — Obsidian links may depend on it (per established memory rule)

### F14 — Backup screen buttons (Create / Restore / Delete) throw `WorkerError: Unsupported attempt to run an async worker`

- **Test:** 8.2 (Create Backup button), 8.5 (Restore button), 8.6 (Delete button)
- **Reproduction:** open §4 Backup & Restore, click any of the three action buttons. Each fails with the same trace — `WorkerError: Unsupported attempt to run an async worker` raised from `textual/worker.py:344` — and the action name in the trace identifies the broken handler (`action_create_backup`, `action_restore_backup`, `action_delete_backup`)
- **Expected:** button presses behave identically to keybindings — open the confirm dialog, then perform the action on accept
- **Actual:** button presses crash the Textual worker. **Keybinding paths (`B` / `R` / `D`) work correctly** because they go through Textual's action dispatch (which handles `@work`-decorated methods natively); the buttons go through `on_button_pressed` which manually wraps the already-decorated coroutine in another `run_worker` call — the double-wrapping is what newer Textual rejects
- **Root cause (verified in source):** `grubforge/screens/backup.py:141-147` calls `self.run_worker(self.action_X(), exclusive=True)` for each button, where `action_X` is decorated with `@work` at lines 151, 174, 206. This is the **same broken pattern** that commit `4490187` (the "regression fix" v1.0.1 was supposed to ship) repaired in `themes.py` — but that commit only touched `themes.py` (one file, +13 -12) and did not audit the rest of the codebase. The "regression bug confirmed dead" claim from §7 was therefore scoped narrower than we knew
- **Severity:** **major** — three of the most-used destructive actions in the app are broken via the most-discoverable input method (the buttons). v1.0.0 shipped this bug; v1.0.1 was supposed to fix it but the fix landed only on theme-apply
- **Scope audit (done now, before §9):**
  - `backup.py` — **broken** (3 actions, listed above)
  - `themes.py` — fixed in 4490187 (action_apply_theme reworked to a sync shim → separate `_apply_theme_worker` async method, no `@work` decorator)
  - `config_editor.py` — `@work` used at lines 222 (`action_save_changes`) and 293 (`action_regen_grub`), but `on_button_pressed` (line 181) only routes to sync helpers (`_stage_edit`, `_clear_pending`); the `@work` methods are reached only via keybindings (S, Ctrl+R) which is the correct Textual path. **Safe.** This is why §6 passed cleanly — those tests went through keybindings
  - `boot_entries.py` — already uses the correct post-4490187 pattern (separate `_*_worker` methods, no `@work` stacking). **Safe.** §9 should not surface F14
- **Proposed fix:** apply the 4490187 pattern to all three actions in `backup.py`. Concretely:
  1. Drop `from textual import work` and the `@work` decorators from `action_create_backup`, `action_restore_backup`, `action_delete_backup`
  2. Convert each `action_X` to a sync shim that calls `self.app.run_worker(self._x_worker(), exclusive=True)`
  3. Move the existing async body into a private `_x_worker` method (not decorated)
  4. In `on_button_pressed`, change `self.run_worker(self.action_X(), exclusive=True)` → `self.action_X()` (matches the themes.py fix)
- **Process gap exposed:** add a "grep for `@work` and `run_worker` together; verify no double-wrapping anywhere" step to the release checklist. This whole class of bug is mechanically detectable

### F15 — Section keybindings inert until focus is inside the section panel

- **Test:** 8.2 (initial `B` press)
- **Expected:** when §4 Backup & Restore is open, footer-advertised section bindings (`B`, `R`, `D`, `F5`) should fire on keypress
- **Actual:** Javier pressed `B` after navigating to §4 with `4`; nothing happened. Only after clicking inside the section panel did `B` start firing (which then surfaced F14). The footer bottom row showed the binding as available the whole time
- **Severity:** minor — workaround (click first) exists, but the footer is misleading and discoverability suffers
- **Proposed fix:** ensure section bindings are bound at screen scope (not at the inner widget that requires focus), so a fresh navigation to §4 immediately accepts the bindings. Same family as F13's "lift bindings to global scope" — both are "binding scope vs. footer promise" mismatches

### F16 — Footer keybindings collide with section-local bindings; refresh-via-`R` broken in §4 (Javier proposes button-label hints + non-colliding section keys)

- **Test:** general observation across §4 Backup & Restore (and likely a pattern across the app)
- **Expected:** the footer row at the bottom of every screen advertises bindings that work consistently regardless of which section is active
- **Actual:** footer reads `1 Dashboard  2 Config  3 Themes  4 Backup  5 Boot Entries  │  E Edit  S Save  R Refresh` on every screen, but in §4 Backup the section binds `R` to **Restore** — section binding wins, so `R` no longer refreshes. The footer's promise is silently broken on this screen. (`F5` keybinding for refresh still works — see 8.8 — so functional refresh is not lost, just the advertised path)
- **Javier's proposed fix (this is the design call):**
  1. **Footer bindings are universal** — `1`–`5` for nav, `E Edit`, `S Save`, `R Refresh` (and any others in that group) must work on every screen with the same meaning
  2. **Section-specific bindings should not collide** with footer bindings — pick keys that are free across the app (e.g., `X` for Restore, `D` for Delete, `N` for New Backup)
  3. **Section bindings should be exposed inside the buttons themselves**, not in a fourth footer slot — e.g., button labels read `Restore (x)`, `Delete (d)`, `New Backup (n)`. This keeps the footer reserved for global navigation/actions while making local bindings discoverable at the point of use
- **Severity:** minor (functional workaround via F5 exists), but the inconsistency is a discoverability defect on a stable release. Closely related to F13 (lift `(A)pply` / `(S)ave` / `Ctrl+R` to global scope) — both are part of one keybinding-architecture pass. **Recommend bundling F13 + F16 (and F15) into a single keybinding-architecture commit inside HF1** rather than three separate fixes
- **Proposed fix (concrete):** audit all screen-level `BINDINGS` for collisions with `app.py` global bindings; rebind §4's actions to non-colliding letters; render binding hints in button label suffixes (e.g., via Textual's button label string `f"Restore (x)"`); ensure all global bindings work from any screen via app-level scope

### F17 — Demo-mode write attempts surface OS errno instead of a graceful read-only message

- **Test:** 10.4 (verified across both write paths — Backup screen create + Config Editor save)
- **Expected:** when running `grubforge` without sudo, write actions are either greyed out / hidden / produce a clear "read-only mode" message — no silent failures, no EPERM tracebacks
- **Actual:** write attempts produce a status-line message exposing the OS errno verbatim:
  - Backup screen `B` keybinding (after focus): `x Backup failed: [Errno 13] Permission denied`
  - Config Editor `S` save: same `[Errno 13] Permission denied` shape
  - App does not crash; no Python traceback; the message is single-line in the status area
- **Severity:** minor (write fails safely; no data corruption; no traceback) but a discoverability/UX defect on a stable release
- **Proposed fix:** detect no-sudo launch at startup (e.g., `os.geteuid() != 0`) and set a `read_only_mode` flag on the app. Key UI behavior off it:
  - Best: pre-emptively grey out / disable destructive buttons + section bindings, with a footer hint like "Read-only mode — relaunch with sudo to enable writes"
  - Acceptable: replace EPERM-derived status messages with "Read-only mode — relaunch with sudo to enable backups" / "...to enable saves" / etc.
- **Pair with F4:** F4 (no demo-mode indicator anywhere in UI) and F17 (no graceful demo-mode write message) are both downstream of the same gap — grubForge doesn't carry a `read_only_mode` flag through the UI. **Single commit closes both** — F4 adds the visible "DEMO" badge (Javier's red-tag suggestion), F17 routes write attempts through a graceful message gate. Same detection path, same flag

### F18 — `/etc/default/grub` GRUB_GFXMODE drift from pre-test baseline (Javier's call: code investigation in HF1)

- **Test:** 11.2 (compare current `/etc/default/grub` against pre-test baseline keys)
- **Expected:** all 6 tracked GRUB keys match pre-test values
- **Actual:** 5 of 6 match exactly. **GRUB_GFXMODE drifted** from `"1920x1080"` (pre-test, captured 2026-05-02 at start of §4) to `1920x1080,auto` (post-test, observed 2026-05-05 at §11.2). Two changes: quote-stripping AND an `,auto` fallback suffix were introduced somewhere during the run
- **Severity:** minor — `1920x1080,auto` is a valid GRUB setting (try 1920x1080 first, fall back to auto); functional regression is none. But if grubForge is silently mutating keys other than the one being edited, that's a code defect worth catching
- **Attribution gap:** cannot be conclusively traced to grubForge. Three possible sources:
  1. **grubForge save logic** — `config_manager.py` may normalize cross-key fields when saving any key (would be a real defect)
  2. **Theme apply path** — Theme Browser writes to `/etc/default/grub` and may rewrite the whole file rather than patching one line; if so, value normalization could happen as a side effect
  3. **External writer** — tela's post-install hook (mentioned in Run metadata) ran `grub-mkconfig` and may have edited `/etc/default/grub`; a system update during the 12-day test window could have done the same
- **Why we can't tell:** §8.7 destructively cleared the backup-set, including any pre-test backup that would have let us diff and confirm exactly when the drift was introduced. **Matrix gap M6** captures this lesson for next run
- **Proposed fix (Javier's call: code investigation in HF1):**
  1. Read `grubforge/config_manager.py`'s save function — does it write the whole file (rewriting all keys) or patch the single edited key? If it rewrites, are values normalized en route?
  2. Read `grubforge/themes_manager.py` (or wherever Theme Apply touches `/etc/default/grub`) — same question. Theme apply writing to GFXMODE would be a clear scope-creep bug
  3. If a normalization is found and is intentional, document it in the man page; if unintentional, fix the save path to patch only the target key
  4. Either way: add a release-checklist step — pre-test, capture a checksum/diff of `/etc/default/grub`; post-test, diff against it. Catches this whole class of drift mechanically

### F13 — Theme Apply silently leaves `grub.cfg` stale; regen action (Ctrl+R) is scoped to Config Editor only

- **Test:** post-session reboot verification (not a numbered matrix test; surfaced organically by Javier on 2026-05-03 after the §7 run on 2026-05-02)
- **Reproduction:** during 7.10, Javier applied `windows-11` via Theme Browser. grubForge correctly reflected `windows-11` as the active theme on the dashboard and in the Theme Browser indicator. Javier rebooted; **the bootloader displayed `tela`, not `windows-11`.** Returning to grubForge post-reboot, `windows-11` was still shown as active (because `/etc/default/grub` did contain it). The mismatch is between `/etc/default/grub` (current) and `grub.cfg` (stale). Theme Apply had updated the former but not regenerated the latter.
- **Expected:** applying a theme via Theme Browser should result in the bootloader using that theme on next boot. Either by (a) Theme Apply auto-running `grub-mkconfig`, or (b) Theme Apply prompting the user to regenerate, or (c) at minimum, the user being able to trigger regen from the Theme Browser screen itself (Ctrl+R)
- **Actual:** Theme Apply writes `/etc/default/grub` but does not invoke `grub-mkconfig`, and there is no in-screen affordance to regen. Ctrl+R (the regen keybinding) is scoped to the Config Editor screen only — the user must navigate away to fix what they thought they had just applied. From any other screen, the system gives no indication that `grub.cfg` is now out of sync with `/etc/default/grub`
- **Severity:** **major** — silent integrity bug. The user has clear visual confirmation that the theme is applied (Theme Browser active indicator, Dashboard reflects the new theme) but the bootloader does not see the change. This contradicts the safety promise of the app and is exactly the class of failure that erodes trust in a bootloader tool. F4 (no demo-mode indicator) is in the same family — both are silent-state defects
- **Proposed fix (Javier's call):** make `(A)pply`, `(S)ave`, and `Ctrl+R (regenerate grub.cfg)` available from **every** screen, not just the screen where the action originates. Concretely:
  - Move Ctrl+R from Config Editor's screen-level `BINDINGS` into the app-level bindings in `grubforge/app.py` (alongside `1`, `2`, `3`, `4`, `5`, `q`, `?`)
  - Audit Apply / Save bindings for the same global-scoping treatment
  - **Stronger fix to consider:** Theme Apply should either auto-trigger regen, OR open a confirm dialog ("Theme written to /etc/default/grub. Regenerate grub.cfg now?"). The auto-regen route is more aligned with grubForge's safety model — the user already confirmed the destructive action; the regen is the natural completion of it
  - Whichever fix lands, the dashboard should also expose a "grub.cfg out of sync with /etc/default/grub" indicator (compare mtimes, or a content-derived stamp). This catches the same class of bug from any path that writes `/etc/default/grub` without regen — including external tools

---

## Matrix refinements

Numbered `M1`, `M2`, … one per ambiguous, missing, or over-broad test in the matrix. These feed back into the next matrix revision rather than the code.

### M1 — 2.5 scope on `app.py` global bindings

- **Issue:** Test 2.5 says "cross-check against each `BINDINGS = [...]` in `grubforge/screens/`" but the man page also documents app-level bindings (defined in `grubforge/app.py`). The screen-level cross-check passes; app-level coverage is implicit.
- **Observation:** `app.py` defines `1` `2` `3` `4` `5` `q` `?` `ctrl+c`. The man page covers all except `ctrl+c` (the hidden quit alias, `show=False` in code and consistently hidden in the app's footer too — so omission is intentional).
- **Proposal:** Either widen 2.5 to include `app.py`, or add a `2.5b` for app-level bindings. Decide whether `show=False` bindings should appear in the man page at all (current convention: no — match the app's own UI).

### M2 — 4.3 backup-count cross-check command counts paired metadata files

- **Issue:** Test 4.3 says cross-check the dashboard count against `ls /var/lib/grubforge/backups/ | wc -l`. But each backup is stored as a paired `.bak` (data) + `.bak.label` (metadata), so the naive `ls | wc -l` returns **2× the actual backup count**, falsely flagging every run as a mismatch.
- **Observation:** dashboard reports 7 backups; `ls .../ | wc -l` returns 14; `ls .../*.bak | wc -l` returns 7 (true backup count). Dashboard is correct.
- **Proposal:** rewrite 4.3's command to `ls /var/lib/grubforge/backups/*.bak | wc -l` so it counts actual backups, not paired files. Apply same fix to 8.3 if it uses the same naive pattern.

### M3 — §7 preamble enumerates themes that may not match installation reality

- **Issue:** §7 preamble states "System already has `starfield` and `windows-11` in `/boot/grub/themes/` — both should appear." This was true at matrix creation (2026-04-21) but became stale by run time — `tela` and four catppuccin variants were installed in between. The fixed list misled the test plan (planned around starfield/windows-11; reality had 7 themes).
- **Observation:** test execution was unaffected (the regression test cares about the worker fix, not the specific theme names), but the planning was tighter than it needed to be. Externally-installed tela also surfaced an incidental win — grubForge correctly detected it as active on F5 refresh.
- **Proposal:** rewrite the §7 preamble to: "System has at least one GRUB theme installed at `/boot/grub/themes/` (test will adapt to whatever is present). The test apply target should be a theme **other** than the current `GRUB_THEME` so the transition is observable." Move theme enumeration out of the matrix; let the runtime list be the source of truth.

### M5 — §9 ordering leaves system in custom-order-active state (9.8 saves AFTER 9.7's Restore Original)

- **Issue:** Matrix §9 sequence is 9.5 Save → 9.6 verify → 9.7 Restore Original → 9.8 Create Custom Entry → 9.9 os-prober → 9.10 F5. Step 9.8 ("create custom entry... save; regenerates") writes a fresh `/etc/grub.d/40_custom`, recreates `.grubforge_perms` sidecars, and re-strips `+x` from `10_linux`/`30_os-prober`/`30_uefi-firmware`. The matrix never tells the tester to re-run Restore Original at the end of §9 — so the system enters §10/§11 in custom-order-active state, with auto-detect scripts disabled
- **Observation:** caught at start of §11 — `/etc/grub.d/40_custom` was 3505 bytes (the 9.8 custom-entry state) instead of the expected stock template; sidecars present. A remedial `sudo grubforge` → `5` → `R` cleanup was needed before §11.4 could pass
- **Proposal:** add **9.11** to the matrix — "Press `R` Restore Original to clean up after 9.8's custom entry; verify `/etc/grub.d/40_custom` is back to stock template and no `.grubforge_perms` sidecars remain." Fold into next matrix revision

### M6 — §11 baseline diff requires a survival backup preserved BEFORE §8.7's destructive cleanup

- **Issue:** Matrix §11.2 says "Confirm /etc/default/grub is back to its pre-test state (use a diff against a backup taken before the test run)." But §8.7 destructively clears the entire backup-set — including any backup that would have served as the pre-test diff target. This contradiction between §8 and §11 was not visible until §8 actually ran
- **Observation:** caught at §11.2 — GRUB_GFXMODE drift detected (`"1920x1080"` → `1920x1080,auto`) but cannot be attributed (grubForge save? theme apply? external writer?). Without a pre-test survival backup, the §11 diff is reduced to per-key spot checks against the matrix preamble's static baseline values, which loses fidelity
- **Proposal:** add **section 0** to the matrix — "Pre-test snapshot. Copy `/etc/default/grub` and `/etc/grub.d/40_custom` to a tester-controlled location OUTSIDE `/var/lib/grubforge/backups/` (e.g., `/tmp/grubforge-pretest/`). §11 diffs against this snapshot. The snapshot is exempt from §8.7's destructive cleanup because it lives outside the backups directory." Fold into next matrix revision. **Process win:** captures the F18-class drift mechanically next time

### M4 — Backup retention policy: cap the number of stored backups (Javier's question during 8.3)

- **Issue:** grubForge currently retains every backup it creates indefinitely. Over a few days of normal use the directory grew from 7 to 18+. There is no FIFO eviction, no max-count cap, no age-based rotation. Javier asked: "shouldn't we have a limit of backups? maybe no more than 10?"
- **Observation:** unbounded growth is fine on a personal workstation but ugly on a stable release — the Backup screen scroll grows, the directory grows, and most older backups are stale duplicates. The §8.7 destructive cleanup test exists precisely because there's no automatic mechanism
- **Proposal:** **decision needed for v1.0.1.** Two paths:
  - **Option A (HF1 polish):** add a `MAX_BACKUPS` constant in `backup_manager.py` (default 10), evict the oldest `.bak` + `.bak.label` pair when the cap is exceeded after a new backup is created. Small surface, small code, useful UX
  - **Option B (deferred to v2+):** treat retention policy as a configurable preference (max count + max age + manual exclusions); ships in a settings/preferences pass that doesn't exist yet
- **Recommendation:** Option A for HF1 if Javier wants it now — it's a single function, mechanically straightforward, and addresses a real growth problem. Option B is a feature, not a fix. Final call is Javier's

---

## Hotfix batches

After a section completes, group its findings into a hotfix batch (`HF1`, `HF2`, …) for the next code pass. Each batch lists which findings it closes and the resulting commit(s).

### HF1 — drafted, not yet committed

Will land at end of run (after §11), closing:
- **Man page accuracy:** F1, F2, F3
- **UX gaps from §3:** F4 (DEMO indicator) — **bundle with F17** (demo-mode write produces graceful read-only message instead of EPERM); single commit, single `read_only_mode` detection path, single flag, both fixes ride together
- **§3 polish:** F5 (overlay close hint)
- **Dashboard cosmetics from §4:** F7, F8
- **Rebrand sweep across app/docs/code:** F10
- **Config Editor empty-value validator for optional keys:** F12
- **Keybinding architecture (bundle as one commit):** F13 (lift `(A)pply`/`(S)ave`/`Ctrl+R` to global app bindings; Theme Apply also auto-regens or prompts; "grub.cfg out of sync" indicator on dashboard — **major**) + F15 (section bindings inert until inner focus) + F16 (footer bindings universal; section bindings non-colliding; in-button label hints like `Restore (x)`)
- **Async-worker pattern fix in backup.py (apply 4490187 idiom):** F14 — convert `action_create_backup`, `action_restore_backup`, `action_delete_backup` to sync shims + private `_*_worker` async helpers; remove `@work` from action methods; `on_button_pressed` calls `self.action_X()` directly without `run_worker` wrap — **major**
- **Config-mutation scope investigation:** F18 — audit `config_manager.py` save logic and theme-apply path for unintended cross-key normalization (GRUB_GFXMODE drift `"1920x1080"` → `1920x1080,auto` observed at §11.2 cannot be attributed; investigate, fix if grubForge is the source, document if intentional)
- **Doc clarifier (no F-number, no code change):** add a "while custom boot order is active" warning to README and man page — kernel-update post-install hooks running `grub-mkconfig` produce a `grub.cfg` without auto-detected linux entries until Restore Original is run. README:211 mentions the mechanism; this adds the operational caveat

Excludes **F6, F9, F11** (TUI layout — deferred to v2+).

**Matrix refinements addressed in next matrix revision (not in HF1 commits):** M1, M2, M3, M5 (§9 cleanup ordering), M6 (§11 needs survival pre-test snapshot outside the backups dir).

**Open decision (Javier's call):** **M4** — backup retention cap. If Option A (HF1 polish), add to this batch as `MAX_BACKUPS=10` FIFO eviction in `backup_manager.py`. If Option B (defer), carry to v2+ feature backlog.

**Process gap caught by F14:** add to release checklist — `grep -rn "@work" grubforge/` and `grep -rn "run_worker" grubforge/` and verify no double-wrapping (no `run_worker(self.method())` where `method` is `@work`-decorated). This whole class of bug is mechanically detectable.
