# grubForge v2.0.0: Test Results (2026-10-02)

The matrix itself carries every result row: `20261002 - Test Matrix for grubForge v2-0-0.md`. This page is the summary.

**Tests: 78** (25 boot-entry checks + 53 new), all passing. **Warnings: 0** (they were 32 under `-W default` until the test folders were cleaned up with their session).

| Section | Result |
|---|---|
| §1–§7 screens and flows (real saves, restores and theme installs in the KognogOS VM) | PASS |
| §8 text console, incl. 8.7 nothing cut off at 100 columns | PASS (8.6 on Javier's word) |
| §9 other distributions: Debian 13, Ubuntu 24.04, Fedora 44, openSUSE Tumbleweed | PASS, a real save reached `grub.cfg` in each |
| §10 Javier's run, KognogOS VM, real package upgrade 1.1.3 → 2.0.0rc1, ending with a restart | PASS — "it works wonders" |

## Findings (all fixed before release, each with a test that fails on the old code)

| ID | Issue | What |
|---|---|---|
| F-1 | [#29](https://github.com/jetomev/grubforge/issues/29) | Debian: an unset list setting was staged as a change |
| F-2 | [#30](https://github.com/jetomev/grubforge/issues/30) | Debian/Ubuntu: `/etc/default/grub.d` silently overrode a save |
| F-3 | [#31](https://github.com/jetomev/grubforge/issues/31) | Fedora: Boot menu offered what doesn't apply; GRUB's own entries missing |
| F-4 | [#32](https://github.com/jetomev/grubforge/issues/32) | openSUSE: empty `GRUB_BACKGROUND=` treated as a change, then rewritten |
| F-5 | [#33](https://github.com/jetomev/grubforge/issues/33) | buttons, labels and the changed mark cut off at 100 columns |

## Gaps found outside grubForge
- **nog** cannot install a package file from disk; the rc packages went in with `pacman -U`.
- Test VMs: Fedora's guest agent is confined by SELinux and openSUSE ships it with command running switched off; both are handled in `scripts/make-test-vms.sh` (test VMs only).
