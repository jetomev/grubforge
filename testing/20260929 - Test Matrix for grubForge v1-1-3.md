# Test Matrix — grubForge v1-1-3

**Date:** 2026-09-29
**Scope:** [#28](https://github.com/jetomev/grubforge/issues/28) — read each boot entry's source from `grub.cfg` instead of guessing it, and keep it through a saved custom order. Ruling: *"Source" means where the entry originally came from.*

---

## 1 · Automated — `tests/test_boot_entry_sources.py` (25 checks)

| § | Covers | EXPECT |
|---|---|---|
| 1 | Sources from `### BEGIN` markers: this system, os-prober Linux + Windows, UEFI inside an `if`, snapshots, submenu | all read, none guessed |
| 2 | Save → run `40_custom` through `sh` as grub-mkconfig does → re-read | order, origins, "· custom order", blocks unchanged; a second save is byte-identical |
| 3 | Entries created in grubForge; someone's own hand-written `40_custom` | "Custom", not guessed |
| 4 | An order saved by v1.1.2 or earlier (no origin lines) | "(guessed) · custom order", and still marked guessed after the next save |
| 5 | No markers at all | os-prober "(on /dev/…)" titles recognised; everything marked guessed |
| 6 | Rename | keeps origin and custom-order state |
| 7 | A malformed source | never written into `40_custom` |
| 8 | Privileged helper `read-entries` | password hash withheld; same sources as a direct read; pass-through accepts only the fixed shapes |
| — | **Same file against v1.1.2** | **must FAIL** — otherwise it is not testing the change |

## 2 · On this desktop (KognogOS, real `grub.cfg`, read-only)

| ID | Check | EXPECT |
|---|---|---|
| 2.1 | Direct parse | every entry has a source; the pre-v1.1.3 saved order reads "(guessed) · custom order" |
| 2.2 | Parse through the helper's output | identical to 2.1 |
| 2.3 | Saved order built from the real entries, emitted by `sh`, checked with `grub-script-check` | GRUB syntax OK; a deliberately broken file is rejected |
| 2.4 | Boot Entries screen, headless screenshot at 140×42 | labels legible, not clipped |

## 3 · Release gates

Everything in `RELEASE-CHECKLIST.md`, including the new pass-through gate and test gate; version sync at 1.1.3.

## 4 · Installed package

| ID | Check | EXPECT |
|---|---|---|
| 4.1 | `makepkg` from the signed asset | signature good; `check()` runs the 25 tests and passes |
| 4.2 | Install through `nog` | `1.1.3-1`, helper `root:root 755`, policy registered |
| 4.3 | Installed app on this desktop | same sources as 2.1 |
| 4.4 | AUR RPC and README badge | `1.1.3-1` |
