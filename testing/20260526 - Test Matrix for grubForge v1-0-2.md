# grubForge — v1.0.2 release test matrix

Focused regression-guard checks for the v1.0.2 fast hotfix (F16 only — Textual `Static.Clicked` → `events.Click` migration). Companion to the full `20260421 - Test Matrix for grubForge v1-0-1-alpha.md` which covers all 11 sections of the v1.0.x test surface; THIS file adds only the new Textual-API-compat section that v1.0.2 introduces.

## How to run

1. Test against a **clean install of grubforge v1.0.2-1 from AUR** (`yay -S grubforge` post-AUR-push) on an Arch host with **`python-textual ≥ 8.2.7`** installed. The 8.2.7+ Textual is what triggered v1.0.1's F16 break — verifying on it is the whole point.
2. Tick each `[ ]` box as verified.
3. If anything fails, stop and file a finding before continuing.

---

## 8. Textual API compatibility (v1.0.2)

Regression guard for v1.0.1's F16 — `Static.Clicked` removed in Textual 8.x. Without these checks, a future Textual API break could silently ship an unimportable package again.

### 8a. Import smoke (the F16 core)

- [ ] **8.1** `python -c "from grubforge.app import GrubForgeApp"` exits 0 with `grubforge.app imports OK` on Python ≥3.10 + Textual ≥8.2.7. **No `AttributeError: type object 'Static' has no attribute 'Clicked'`** anywhere in the traceback (was the v1.0.1 F16 signature).
- [ ] **8.2** PKGBUILD `check()` step runs the same import during `makepkg` and exits 0. Look for `==> Starting check()...` in the build log followed by the success line. Verifies the regression guard fires on every install, not just on the maintainer's machine.

### 8b. Click navigation works (the behavioral check)

The F16 fix replaces the `on_static_click(Static.Clicked)` handler with `on_click(events.Click)`. The new handler must catch sidebar nav clicks identically.

- [ ] **8.3** Launch `grubforge` (or `sudo grubforge`). Click directly on the **"🏠 Dashboard"** label in the sidebar (don't use the `1` keybinding). Screen switches to Dashboard.
- [ ] **8.4** Click on **"🔧 Config Editor"** in the sidebar. Screen switches to Config Editor.
- [ ] **8.5** Click on **"🎨 Themes"**. Screen switches to Themes.
- [ ] **8.6** Click on **"🗂 Backup & Restore"**. Screen switches to Backup.
- [ ] **8.7** Click on **"🖥 Boot Entries"**. Screen switches to Boot Entries.
- [ ] **8.8** Verify keybindings still work: press `1` (Dashboard), `2`, `3`, `4`, `5` cycling through. Same dispatch as the click path; this confirms the rest of `app.py` is healthy after the F16 surgery.

### 8c. No regression on non-nav clicks

- [ ] **8.9** Click an arbitrary non-nav widget (e.g., a button label, a Static showing "Press ? for help"). Nothing unexpected happens — no navigation, no error. The `on_click` handler's `wid.startswith("nav-")` filter rejects non-nav clicks harmlessly.

### 8d. Cross-version compatibility (optional but valuable)

If you have access to a host with an older Textual version installed:

- [ ] **8.10** Repeat 8.1 (import smoke) on Textual <8.2.7. `events.Click` has been in Textual since early 8.x, so the new code should work on both old and new — the fix is forward-AND-backward compat. Skip if no older Textual available.

---

## Pass criteria for v1.0.2 release

- All of 8a (import smoke + PKGBUILD check()) and 8b (click navigation works) must pass.
- 8c (no regression on non-nav clicks) should pass.
- 8d is informational; v1.0.2 PKGBUILD doesn't pin `python-textual` lower bound, so confirming backward-compat reduces risk for users still on older Textual.

If 8.1 or 8.2 fails: the F16 fix didn't actually land in the AUR build. Halt the release; investigate.

If 8.3–8.7 fail (clicks don't navigate): the `events.Click` migration broke the nav handler. Likely cause: event propagation is different in newer Textual, or the widget id check has changed semantics. Revert and reapproach.

---

## Out of scope for this matrix

- v1.0.1 sections 1–11 (full app surface): covered by `20260421 - Test Matrix for grubForge v1-0-1-alpha.md` and the v1.0.1-stable retest results (`20260526 - Test Results for grubForge v1-0-1-stable.md`). v1.0.2 introduces only the F16 fix; no behavioral changes elsewhere. Re-running the full matrix is unnecessary for this hotfix.
- v1.0.3 UX batch (F1–F15): deferred to a separate Test Matrix + Test Results pair when that cycle runs.
