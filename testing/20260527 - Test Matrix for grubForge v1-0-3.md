# grubForge — v1.0.3 release test matrix

Fix-verification matrix for the v1.0.3 UX hotfix batch. Each check confirms one of the 15 findings (F1–F15) from the v1.0.1-stable retest is closed. Companion to `20260526 - Test Results for grubForge v1-0-1-stable.md` (the finding source) and the full v1.0.1-alpha surface matrix.

## How to run

1. Test against a **clean install of grubforge v1.0.3-1 from AUR** (`yay -S grubforge` post-AUR-push) on an Arch host with `python-textual ≥ 8.2.7`. Launch **once without sudo** (read-only/demo mode — needed for F1) and **once with `sudo grubforge`** (write mode — needed for the regen/save/apply paths).
2. Tick each `[ ]` box as verified.
3. If anything fails, stop and log it in the v1.0.3 Test Results before continuing.

The fixes shipped in four thematic groups (commits `42488fd` G3, `1bbf39d` G1, `2932b49` G2, `f22303f` G4). The matrix is grouped the same way.

---

## 9. v1.0.3 UX hotfix verification

### 9.G1 — Refresh-on-show + Dashboard sync states (F3, F4, F5, F8, F10)

- [ ] **9.1** (F4) `sudo grubforge` → Config Editor (2). Clear `GRUB_THEME` (E, blank the value, Apply Edit, S, confirm). Switch to Dashboard (1). **Active Settings → GRUB_THEME shows the cleared/current value** with no manual R. *(Was: stale until manual R.)*
- [ ] **9.2** (F5) From the same session: Backup & Restore (4), press **N** to create a backup, confirm. Switch to Dashboard (1). **Backup count reflects the new total** (re-globbed, not the startup count). *(Was: stuck at startup value.)*
- [ ] **9.3** (F8) Themes (3) → apply a theme. Switch to Backup (4): the new auto-backup is listed without manual R. Switch to Dashboard (1): GRUB_THEME reflects the applied theme.
- [ ] **9.4** (F3) Config Editor (2), stage an edit (E → change value → Apply Edit) but **do NOT save**. Switch to Dashboard (1). **Sync row reads yellow "⚠ pending changes — press S in Config Editor to save"** (text and color agree). Save the edit, return to Dashboard: row returns to "✓ in sync" or "⚠ grub.cfg older". *(Was: "✓ in sync" text shown in yellow — mismatch.)*
- [ ] **9.5** (F10) On the Dashboard, press **R**. A bottom-right toast "Dashboard refreshed." appears. *(Was: silent.)*
- [ ] **9.6** (regression guard) On launch, **no popups appear before you press anything** — passive mount hints stay on the status line. *(Guards the G3-introduced startup-spray risk.)*

### 9.G2 — Ctrl+R as a true app-level action (F7, F11, F12, F13)

- [ ] **9.7** (F7) `sudo grubforge` → Dashboard (1). Press **Ctrl+R**. The "Regenerate grub.cfg" confirm dialog appears; confirm → grub-mkconfig runs and a success/failure toast fires. *(Was: silent no-op anywhere but Config Editor — even though the Dashboard Sync row tells you to press it.)*
- [ ] **9.8** (F7) Repeat 9.7 from Themes (3) and Boot Entries (5). Ctrl+R fires the same regen flow from each.
- [ ] **9.9** (F11) On the Dashboard, press **Ctrl+R** as the very first key after entering. It fires on the **first** press (confirm dialog appears immediately). *(Was: first press silent, second worked.)*
- [ ] **9.10** (F13) Config Editor (2), select a key, type a new value. Press keyboard **A**. The edit is staged (row shows "● pending"), identical to clicking "Apply Edit". *(Was: A rejected with "Apply isn't available" while the button worked.)*
- [ ] **9.11** (F13 guard) On Dashboard/Backup (no apply action), press **A**. A toast "Apply isn't available on this screen." appears — no crash.
- [ ] **9.12** (F12) Themes (3) → apply a theme. The confirm dialog and the post-apply message say **"press Ctrl+R to regenerate grub.cfg"** with **no "go to Config Editor"** instruction. Check the same in the Themes **H** help overlay step 5 and Boot Entries os-prober enable/scan messages.

### 9.G3 — Unified feedback surface (F9)

- [ ] **9.13** (F9) On each screen, trigger a success action (e.g. **R** refresh on Config Editor / Themes / Backup / Boot Entries). Feedback appears as a **bottom-right toast** (consistent with the "isn't available" dispatcher popups) **and** updates the in-screen status line — not blue text only. *(Was: success = blue status-line text; "not available" = toast — two different locations.)*
- [ ] **9.14** (F9) Confirm status icons are consistent unicode (`✓ ● ⚠ ✗`) across all screens — no ASCII `>> !! xx` drift on Themes / Boot Entries.

### 9.G4 — Discrete widget bugs (F1, F2, F6, F14, F15)

- [ ] **9.15** (F1) Launch **without sudo**. The sidebar shows a red reverse **DEMO** badge under "GRUB TUI Manager v1.0.3". Launch **with sudo**: badge absent. *(Was: never rendered — clipped by the logo box height.)*
- [ ] **9.16** (F2) Press **?**. A centered help **modal** opens (not a toast). Press **?** again → it closes (toggle, doesn't stack). Reopen, press **Esc** → closes. Reopen, press **q** → closes **and the app does NOT quit**. The modal lists nav, universal actions, and per-screen keys.
- [ ] **9.17** (F6) Backup & Restore (4), select a backup with a long config (~40 lines). **Scroll the preview pane** with arrows / PgDn-PgUp / mouse wheel — the lower lines (GRUB_THEME, GRUB_GFXMODE, GRUB_DISABLE_OS_PROBER) become visible. *(Was: capped ~21 lines, no scroll.)*
- [ ] **9.18** (F14) Config Editor (2) on fresh entry (no row selected). Press **E**. The first key (GRUB_DEFAULT) is auto-selected and its detail shown, with the edit input focused — not an empty edit box. *(Was: focused empty input, nothing to edit.)*
- [ ] **9.19** (F15) Enter Backup & Restore (4) via the **4** key. **Without clicking anywhere**, press **N** → the Create Backup dialog (or read-only warning) fires immediately. Repeat for **X** and **D**. *(Was: inert until you clicked the list panel.)*
- [ ] **9.20** (F15) Same check on Boot Entries (5): **K / J** reorder, **N** rename, **X** restore — all respond on entry without a panel click.

### 9.regression — version sync + global keys still work

- [ ] **9.21** Sidebar logo reads **v1.0.3**; `grubforge --version` (or `python -c "import grubforge; print(grubforge.__version__)"`) reads **1.0.3**; man page `.TH` reads **v1.0.3**.
- [ ] **9.22** With a list/table focused on entry (F15 side-effect), the global keys still work: **1–5** navigate, **q** quits from a normal screen, **?** opens help. Focusing the primary widget didn't capture these.

---

## Pass criteria for v1.0.3 release

- **All of 9.1–9.20** (the 15 findings) must pass.
- **9.6, 9.11, 9.22** (regression guards) must pass — these protect against the new mechanisms (unified feedback, app-level dispatch, focus-on-show) introducing fresh breakage.
- **9.21** version sync must pass before tag.

If a Ctrl+R check (9.7–9.9) fails: the app-level regen worker isn't firing — check `action_global_regen` is `@work` and `regenerate_grub` is imported in `app.py`.

If a focus check (9.19–9.20) fails but the action works after a click: `DEFAULT_FOCUS` isn't being applied in `_switch_to`, or the id is wrong for that screen.

---

## Out of scope

- Full app surface (v1.0.1 sections 1–11): unchanged behavior outside the 15 findings; covered by the v1.0.1-alpha matrix. Spot-check during the regen/save flows above.
- F16 (Textual API compat): shipped in v1.0.2; its regression guard (PKGBUILD `check()` import smoke) still runs on every build.
