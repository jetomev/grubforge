# grubForge — v1.0.3 test results

Dogfood results for the v1.0.3 UX hotfix batch. Companion to `20260527 - Test Matrix for grubForge v1-0-3.md`. Verifies all 15 findings (F1–F15) from the v1.0.1-stable retest are closed.

**Outcome: PASS — shipped v1.0.3-1 (2026-05-27).** GitHub tag `v1.0.3` + release live; AUR `grubforge` at `1.0.3-1`; Issues #2–#16 closed; milestone v1.0.3 closed.

## Method

Two-layer verification:

1. **Textual `Pilot` automated tests** (headless, run during development) — exercised the logic of every group: feedback `popup=False` flag + no startup spray; `_reload_view` firing on every screen switch; Dashboard R toast; F3 pending-state render; app-level `action_global_regen` invoking `regenerate_grub` from Themes *and* Dashboard; global `A` staging a Config Editor edit; "Apply isn't available" on screens without it; help modal toggle/Esc/q-without-quit; `DEFAULT_FOCUS` on every screen; real `4`→`n` keypresses firing `create_backup`; `E` auto-select; preview nested in `VerticalScroll`; DEMO badge in logo content.
2. **Real-hardware dogfood** (Javier, local dev build) — demo/read-only pass + `sudo` write-mode pass, then a clean package-install smoke.

## Results by group

### G1 — Refresh-on-show + Dashboard sync states (F3, F4, F5, F8, F10) — PASS
- **F4/F5/F8** (9.1–9.3): write-mode — after a Config Editor save, the Dashboard reflected the new GRUB_TIMEOUT and the Backup count incremented (auto-backup before write), with no manual R. ✓
- **F3** (9.4): staging an edit and switching to the Dashboard showed the yellow **"⚠ pending changes — press S in Config Editor to save"** sync state; after saving it cleared. ✓
- **F10** (9.5): Dashboard **R** produced a "Dashboard refreshed." toast. ✓
- **Regression guard** (9.6): no popups fired at launch — passive `on_mount` hints stay on the status line (Pilot-confirmed; demo pass clean). ✓

### G2 — Ctrl+R as a true app-level action (F7, F11, F12, F13) — PASS
- **F7/F11** (9.7–9.9): write-mode — **Ctrl+R from the Dashboard** ran the real `grub-mkconfig` and reported the success toast. Demo mode confirmed the same dispatch reaches the regen handler from any screen (hits the read-only guard). ✓
- **F13** (9.10): keyboard **A** staged a Config Editor edit (demo + write). "Apply isn't available" still fires cleanly on screens without an apply action (Pilot). ✓
- **F12** (9.12): no "go to Config Editor" cross-screen instructions remain (grep-verified across themes/boot_entries + help overlay). ✓

### G3 — Unified feedback surface (F9) — PASS
- **F9** (9.13): all action feedback surfaced in consistent bottom-right popups *and* the status line — Javier confirmed "all messages updated in Dashboard, and showed in bottom right popups." ✓
- **F9 icons** (9.14): unicode icon set (`✓ ● ⚠ ✗`) canonical across all screens. ✓

### G4 — Discrete widget bugs (F1, F2, F6, F14, F15) — PASS
- **F1** (9.15): DEMO badge renders in read-only mode (logo box `height: auto`). ✓
- **F2** (9.16): **?** opens a real modal; toggles closed; Esc closes; **q closes it without quitting the app**. ✓
- **F6** (9.17): backup preview scrolls (wrapped in `VerticalScroll`). ✓ (Pilot-confirmed nesting; demo pass.)
- **F14** (9.18): **E** with no selection auto-selects the first key. ✓
- **F15** (9.19–9.20): **N/X/D** (Backup) and **K/J/N/X** (Boot Entries) fire on screen entry without a panel click (`DEFAULT_FOCUS`). ✓

### Regression — version sync + global keys (9.21, 9.22) — PASS
- Sidebar reads **v1.0.3**, `__version__` `1.0.3`, man page `.TH` v1.0.3. ✓ (Fixed the stale in-app `v1.0.1` string that had persisted through v1.0.2.)
- With a list/table focused on entry, **1–5** nav / **q** / **?** still work. ✓

## Packaging

- Hardened PKGBUILD `check()` from an import smoke to a **headless mount** under Textual's test harness — proven in the real fakeroot build (`grubforge headless mount OK`). Catches CSS-parse / on_mount failures at build time.
- Built package carries **no `__pycache__`/`.pyc`** (the v1.0.2 install-conflict class stays closed).
- Local install: clean upgrade `1.0.2-2 → 1.0.3-1`, no file conflicts.

## Observations / backlog (not v1.0.3 blockers)

- **S from the Dashboard.** When the Dashboard shows "⚠ pending changes", pressing **S** there reports "Save isn't available on this screen" — correct per the screen-scoped dispatcher, and the message itself says "press S in Config Editor." But the natural reflex is to press S where the prompt appears. **v1.0.4 candidate:** route **S from the Dashboard** to whichever screen holds pending edits. New behavior, outside the F1–F15 scope.

## Pass criteria

All 9.1–9.20 (the 15 findings) verified; regression guards 9.6/9.11/9.22 hold; 9.21 version sync confirmed before tag. **Release approved and shipped.**
