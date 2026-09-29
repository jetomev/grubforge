# Test Matrix — grubForge v1-1-2

**Date:** 2026-09-29
**Scope:** one fix — boot entry labels read the system name from `/etc/os-release` instead of assuming "Arch Linux" ([#27](https://github.com/jetomev/grubforge/issues/27)), commit `776079e`.
**Not in scope:** where the *source* underneath the label comes from — that is [#28](https://github.com/jetomev/grubforge/issues/28), the next release.

---

## 1 · The fix, on the reporter's system

| ID | Check | EXPECT |
|---|---|---|
| 1.1 | Boot Entries on stock Debian 13 | `10_linux` entries read `Debian GNU/Linux` |
| 1.2 | `20_linux_xen` on Debian | `Debian GNU/Linux (Xen)` |
| 1.3 | Other sources on Debian | OS Prober / UEFI / BTRFS Snapshots / Custom unchanged |

## 2 · The fix, elsewhere

| ID | Check | EXPECT |
|---|---|---|
| 2.1 | This desktop (KognogOS, built on Arch) | `KognogOS` — not `Arch Linux` |
| 2.2 | Arch `os-release` sample | `Arch Linux`, unchanged from v1.1.1 |
| 2.3 | Fedora's unquoted `NAME=Fedora Linux` | parsed as `Fedora Linux` |
| 2.4 | No readable `os-release` | neutral `This system` |
| 2.5 | Real `grub.cfg` on this desktop, parsed read-only | every entry parsed, nothing written |

## 3 · Release gates (`RELEASE-CHECKLIST.md`)

| ID | Check | EXPECT |
|---|---|---|
| 3.1 | `run_worker(self.action_…)` double-wrap grep | no hits |
| 3.2 | Helper path in policy, `privilege.py`, PKGBUILD, `install-helper.sh` | all `/usr/lib/grubforge/grubforge-helper` |
| 3.3 | `MAX_BACKUPS`, `MANAGED_SCRIPTS` in app and helper | identical |
| 3.4 | `_extract_block` in app and helper | code identical, docstrings may differ |
| 3.5 | Helper refuses as non-root / unknown verb / no verb | non-zero exit, all three |
| 3.6 | Helper, policy, installer changed since v1.1.1? | unchanged |
| 3.7 | Version sync: `__init__.py`, `app.py`, man page, README badge, PKGBUILD, `.SRCINFO` | all `1.1.2` |
| 3.8 | Headless mount | app mounts under Textual's test harness |

## 4 · The installed package

| ID | Check | EXPECT |
|---|---|---|
| 4.1 | `makepkg` from the signed release asset | signature good, `check()` passes |
| 4.2 | Installed version | `grubforge 1.1.2-1`, `__version__` 1.1.2 |
| 4.3 | Helper after install | `root:root`, not user-writable, policy registered |
| 4.4 | Installed app reads this desktop | `10_linux` entries labelled `KognogOS` |
| 4.5 | AUR RPC and README badge | both report `1.1.2-1` |
