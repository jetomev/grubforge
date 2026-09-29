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
| **§4 installed package** | **PASS**, all five — installed through `nog`, then again from the AUR |
| **New findings** | none in grubForge. One in nog, from installing it (below). |

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

## §4 — the installed package (2026-09-29)

| ID | Result |
|---|---|
| 4.1 | **PASS** — `makepkg` from the signed release asset: sha256 `2680d4a8…`, signature good, headless mount OK, helper refusal checks OK. The asset downloaded back from GitHub matched the local build. The recipe was first proven by rebuilding v1.1.1's asset byte-for-byte. |
| 4.2 | **PASS** — installed with `nog install ./grubforge-1.1.2-1-any.pkg.tar.zst` (nog 1.5.1, classed Tier 2). `grubforge 1.1.2-1`, `__version__` 1.1.2, man page `grubForge v1.1.2`. |
| 4.3 | **PASS** — helper `root:root 755`, owned by `grubforge 1.1.2-1`; `org.kognogos.grubforge.manage` registered. |
| 4.4 | **PASS** — the installed app labels this desktop's entries `KognogOS`. |
| 4.5 | **PASS** — AUR RPC `1.1.2-1` (the index lagged the push by several minutes); README badges decoded from camo read `Version: 1.1.2` and `aur: v1.1.2-1`. |

**Public install path:** reinstalled from the AUR with a clean build — signature verified, `check()` passed, `1.1.2-1` installed.

### Observed, not new

- The desktop's boot menu lists **"KognogOS snapshots" twice.** This is consistent with [#20](https://github.com/jetomev/grubforge/issues/20) (unmanaged generators duplicated after a saved custom order) on a desktop known to be in frozen-entries mode. Not investigated further in this release.

### Finding in nog, not grubForge

`nog install grubforge` handed off to yay correctly, but yay stopped at its *"Packages to cleanBuild?"* menu. With no terminal attached there is nobody to answer it, and nog has no way to pass yay's `--noconfirm`. In a normal terminal this is simply answered, so it is not a bug in ordinary use. It does mean an AUR install through nog cannot be scripted. The reinstall was done with `yay -S grubforge --noconfirm --rebuild --sudoflags=-A` for that reason. Filed as [nog#26](https://github.com/jetomev/nog/issues/26).

## Not run, and why

- **§1 was not repeated on the tagged build.** The code is identical to what was tested; the Debian VM also needed manual console recovery last time.
- **#28 is not addressed.** An entry found by os-prober whose title lacks "windows" is still credited to this system. Stated in the release notes.
