# Test Results — grubForge v1-1-2

**Date:** 2026-09-29
**Matrix:** `20260929 - Test Matrix for grubForge v1-1-2.md`

---

## Summary

| | |
|---|---|
| **§1 on Debian** | **PASS** — run 2026-09-15 on the `debian13-grubforge` VM against `776079e`, the same code this release ships |
| **§2 elsewhere** | **PASS** — including a finding: KognogOS was mislabelled too |
| **§3 gates** | **PASS**, all eight |
| **§4 installed package** | recorded after the AUR cut, below |
| **New findings** | none |

---

## §1 — Debian (2026-09-15)

Measured before and after the change on stock Debian 13:

| Source | v1.1.1 | v1.1.2 |
|---|---|---|
| `10_linux` | Arch Linux | **Debian GNU/Linux** |
| `20_linux_xen` | raw script name | **Debian GNU/Linux (Xen)** |
| OS Prober, UEFI, BTRFS Snapshots, Custom | — | unchanged |

**Why this counts for today's release:** nothing in `grubforge/` changed between `776079e` and the release except the version strings. The Debian run was not repeated today.

## §2 — elsewhere (2026-09-29)

| ID | Result |
|---|---|
| 2.1 | **PASS** — this desktop reads `KognogOS`. v1.1.1 reads `Arch Linux` here too: **the bug was never Debian-only.** Any system built on Arch but named differently was mislabelled. |
| 2.2 | **PASS** |
| 2.3 | **PASS** — `Fedora Linux` |
| 2.4 | **PASS** — `This system` |
| 2.5 | **PASS** — 7 entries parsed from the live `grub.cfg`, read-only |

## §3 — release gates

All eight **PASS**. One false alarm worth recording: a literal search for the helper path found it in three of four files. `install-helper.sh` and the PKGBUILD build the same path from two parts (`HELPER_DIR=/usr/lib/grubforge` + `/grubforge-helper`; `${pkgdir}/usr/lib/${pkgname}/grubforge-helper`). All four agree.

## Not run, and why

- **§1 was not repeated on the tagged build.** The code is identical to what was tested; the Debian VM also needed manual console recovery last time.
- **#28 is not addressed.** An entry found by os-prober whose title lacks "windows" is still credited to this system. Stated in the release notes.
