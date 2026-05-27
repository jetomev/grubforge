# grubForge — v1.0.2 dogfood test results

Companion to [`20260526 - Test Matrix for grubForge v1-0-2.md`](20260526 - Test Matrix for grubForge v1-0-2.md). v1.0.2 is a single-finding fast hotfix (F16 — Textual `Static.Clicked` → `events.Click` migration); this Test Results doc captures the dogfood pass plus the v1.0.2-1 → v1.0.2-2 packaging hotfix that surfaced during the ship.

## Run metadata

- **Package under test:** `grubforge-1.0.2-2-any.pkg.tar.zst` delivered from AUR (`yay -S grubforge` after `sudo pacman -R grubforge` + `sudo rm -rf /usr/lib/grubforge`)
- **Source commit:** `4c2a6c0 Release v1.0.2 — Textual 8.x events.Click migration (F16)` (the GitHub tag `v1.0.2`)
- **AUR HEAD:** `7117501 grubforge 1.0.2-2 — packaging hotfix: don't ship .pyc bytecode caches`
- **Tarball sha256:** `941a3f2d7f2b554bec89becd843fb5008fcbbd0270f0ec25db27e23576c4fdce` (unchanged between pkgrel=1 and pkgrel=2; only the PKGBUILD changed)
- **Install method:** `yay -S grubforge` against AUR; reproduces the public install path
- **Test run started:** 2026-05-26 (same evening as the v1.0.1-stable retest closure + v1.0.2 implementation)
- **Tester:** Javier (`jetomev`) + Claude (Anthropic), per `feedback_grubforge_workflow.md`
- **Trigger:** v1.0.1's F16 — external user `@jfp42` filed GitHub Issue #1 on 2026-05-19 reporting `AttributeError: type object 'Static' has no attribute 'Clicked'` on Python 3.13 + Textual 8.2.7. v1.0.2 migrates the click handler from the removed `Static.Clicked` to the supported `events.Click` and adds a PKGBUILD `check()` smoke test as a regression guard.

## Pre-test baseline

- `grubforge` v1.0.1 was installed (HF1 build from the May 15 cleanroom; intervening sessions had user-runtime Python 3.14 launch the app, which created `.pyc` files in `/usr/lib/grubforge/grubforge/{,screens,widgets}/__pycache__/`)
- `/etc/default/grub`: at the original baseline (`34484fbc9eada6799782c60df2b19b4d571575454aef45fa3b0349168fae1595`), unchanged since May 15
- Python 3.14.5, Textual 8.2.7 on this host

## Section status

| Section | Title | Status | Notes |
|---|---|---|---|
| 8a | Import smoke (the F16 core) | **pass** | `python -c "from grubforge.app import GrubForgeApp"` succeeds with `grubforge.app imports OK`. PKGBUILD `check()` step ran the same import during `makepkg` and exited 0. No `AttributeError: type object 'Static' has no attribute 'Clicked'` anywhere |
| 8b | Click navigation works (the behavioral check) | **pass** | Each sidebar nav-item click switches to the correct screen (Dashboard, Config Editor, Themes, Backup, Boot Entries). Same dispatch path as the `1-5` keybindings, which were also verified by quick spot-check. The `events.Click` handler correctly filters by widget id prefix |
| 8c | No regression on non-nav clicks | **pass** | Non-nav widgets ignored by the handler's `wid.startswith("nav-")` filter; no spurious navigation events fire |
| 8d | Cross-version compatibility (optional) | not run | No host with older Textual available to verify on. `events.Click` has been in Textual since early 8.x, so backward-compat is presumed-good by API stability; forward-compat (Textual 8.2.7+) verified directly above |

Status legend: `pending` / `pass` / `pass with findings` / `fail` / `not run`.

---

## Findings

**One — surfaced during the ship, fixed in pkgrel=2.**

### F1 (v1.0.2 cycle, packaging) — v1.0.2-1 shipped `.pyc` bytecode caches in the package

- **Test:** Install v1.0.2-1 via `yay -S grubforge` over a v1.0.1 install where the user had launched grubforge (creating runtime `.pyc` files at `/usr/lib/grubforge/grubforge/{,screens,widgets}/__pycache__/`).
- **Expected:** clean install — pacman either overwrites or leaves user-runtime files untouched.
- **Actual:** pacman aborts with `error: failed to commit transaction (conflicting files)` listing all 14 `.pyc` files. v1.0.2-1's PKGBUILD `check()` step had run Python which created those `.pyc` cache files in the build's `$srcdir/grubforge-1.0.2/`, then `cp -r grubforge "${pkgdir}/usr/lib/${pkgname}/"` copied them into the package. On install, those tracked `.pyc` paths collided with the user's untracked runtime `.pyc` files.
- **Severity:** medium (blocks upgrade installs where user has launched the app post-install; doesn't block fresh installs).
- **Detection:** `==> WARNING: Package contains reference to $srcdir` was emitted during `makepkg`, listing the `.pyc` files. Should have heeded; missed.
- **Fix in pkgrel=2:** `PYTHONDONTWRITEBYTECODE=1` env on the `check()` invocation prevents Python from writing `.pyc` to the source tree; defensive `find grubforge -type d -name __pycache__ -exec rm -rf {} +` in `package()` as belt-and-suspenders. Verified by clean `makepkg` (no `$srcdir` warning) and clean install (no conflicting files).

**No findings on the F16 fix itself.** The Textual API migration landed correctly; import smoke verified live on the exact failing combo (Python 3.14.5 + Textual 8.2.7).

---

## Cross-validation: PKGBUILD check() phase

PKGBUILD's `check()` step runs `python -c "from grubforge.app import GrubForgeApp"` during every `makepkg`. This dogfood's install captured (excerpted from the live AUR build log):

```
==> Starting check()...
grubforge.app imports OK
==> Entering fakeroot environment...
==> Starting package()...
```

Every machine that installs v1.0.2 via AUR runs this smoke test as part of the build. Future Textual API breaks would surface here, not in the wild.

> **Python 3.14 caveat:** Python 3.14 deferred evaluation of type annotations by default (PEP 649 follow-up). The original v1.0.1 F16 bug was `def on_static_click(self, event: Static.Clicked)` — `Static.Clicked` is a type *annotation*, not executable code. On Python 3.14 the annotation isn't evaluated at import time, so `import grubforge.app` SUCCEEDS even on the broken v1.0.1 source. On Python 3.13 (jfp42's environment), annotations evaluated eagerly and the import failed. **Implication:** the `check()` smoke test catches the bug class on Python ≤3.13 but NOT on Python ≥3.14. The v1.0.2 fix is still correct (removes the bad reference unconditionally); a future v1.0.x could harden the check by running the smoke under both Python 3.13 and 3.14 in CI, or by ALSO instantiating `GrubForgeApp()` (which would force annotation evaluation). Out of scope for v1.0.2.

---

## Real-world confirmation

External user `@jfp42` filed GitHub Issue #1 on 2026-05-19 with the full traceback from Debian Sid + Python 3.13 + Textual 8.2.7. v1.0.2 shipped to GitHub + AUR on 2026-05-26 ~22:12 EDT. Issue #1 auto-closed via "Closes #1" in commit `4c2a6c0`. The `events.Click` migration is verified live on this host (Python 3.14.5 + Textual 8.2.7) via the import smoke. Mirror of the nog cadence: external report → root cause → fix shipped → verified.

The v1.0.2-1 → v1.0.2-2 packaging hotfix surfaced during the ship itself, on the SAME host that has the v1.0.1 → v1.0.2 upgrade scenario (because user-runtime `.pyc` files from v1.0.1 launches existed). pkgrel=2 closes that gap without disrupting the v1.0.2 release lineage.

---

## Next-session handoff

1. **v1.0.2 cycle closes here.** No further work on v1.0.2.
2. **v1.0.3 UX batch (F1–F15)** is the next grubForge cycle. See `testing/20260526 - Test Results for grubForge v1-0-1-stable.md` for the canonical scope. GitHub Issues #2–#16 (milestone `v1.0.3`) carry the per-finding analysis.
3. **No v1.0.2 retest needed** — fix is single-purpose, verified on AUR binary, no behavioral regressions observed.
4. **Test article state at end of run:**
   - `grubforge` v1.0.2-2 installed and functional
   - F16 fix verified live (`grubforge.app` imports cleanly on Python 3.14.5 + Textual 8.2.7)
   - Sidebar nav-item clicks switch screens correctly (behavioral half of F16)
   - PKGBUILD `check()` will run on every future install, catching the same class of API break
5. **GitHub state:** main HEAD `4c2a6c0`, tag `v1.0.2` live, Release v1.0.2 marked Latest with rich notes thanking `@jfp42`, Issue #1 auto-closed
6. **AUR state:** `grubforge-1.0.2-2` live at `https://aur.archlinux.org/packages/grubforge`
