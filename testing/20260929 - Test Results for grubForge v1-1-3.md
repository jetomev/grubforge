# Test Results — grubForge v1-1-3

**Date:** 2026-09-29
**Matrix:** `20260929 - Test Matrix for grubForge v1-1-3.md`

---

## Summary

| | |
|---|---|
| **§1 automated** | **PASS**, 25/25. Against v1.1.2: **fails** on the os-prober Linux case, then crashes on the new fields, as it should |
| **§2 this desktop** | **PASS**, all four |
| **§3 gates** | **PASS** — double-wrap, `_extract_block`, constants, pass-through ↔ parser patterns, helper refusals (non-root `read-entries` included), tests 25/25, version sync 1.1.3 |
| **§4 installed package** | **PASS**, all four — through `nog`, then again from the AUR |
| **New findings** | none. #20 became *visible* (below) |

---

## §2 — this desktop

This desktop is the legacy case: its custom order was saved by an older grubForge, before origin lines existed.

| Entry | Source shown |
|---|---|
| KognogOS | KognogOS (guessed) · custom order |
| Windows 11 / Windows Recovery | OS Prober (guessed) · custom order |
| Advanced options for KognogOS | KognogOS (guessed) · custom order |
| UEFI Firmware Settings | UEFI (guessed) · custom order |
| KognogOS snapshots | BTRFS Snapshots (guessed) · custom order |
| KognogOS snapshots | **BTRFS Snapshots** — straight from `41_snapshots-btrfs` |

The last two rows are [#20](https://github.com/jetomev/grubforge/issues/20) on screen: one copy frozen into the custom order, one still emitted by the snapshots script grubForge never switched off. v1.1.2 showed two identical lines; v1.1.3 shows why there are two.

- **2.2** — the helper's output parses to the identical list. The only non-block lines it passed were section markers and `# This file is managed by grubForge.`
- **2.3** — a `40_custom` rendered from these real entries, emitted by `sh`, carries 7 origin lines; `grub-script-check` accepts it with and without them, and rejects a deliberately unterminated `menuentry` (exit 1), so the checker was genuinely checking.
- **2.4** — screenshot reviewed: the longest label, *"BTRFS Snapshots (guessed) · custom order"*, fits the list and the detail pane.

## §4 — the installed package

| ID | Result |
|---|---|
| 4.1 | **PASS** — sha256 `3507a660…` (matches the asset downloaded back from GitHub), signature good; `check()`: headless mount OK, helper refusals OK, **25/25 tests**. |
| 4.2 | **PASS** — `nog install ./grubforge-1.1.3-1-any.pkg.tar.zst` → `1.1.3-1`; helper `root:root 755` and byte-identical to the v1.1.3 source. |
| 4.3 | **PASS** — the installed app shows the same sources as §2. |
| 4.4 | **PASS** — AUR RPC `1.1.3-1` about 2 minutes after the push; README badges decoded from camo read `Version: 1.1.3` and `aur: v1.1.3-1`. |

**Public install path:** reinstalled from the AUR with a clean build — signature verified, all three `check()` stages passed, `1.1.3-1` installed. (Done with `yay … --noconfirm` directly; `nog install` of an AUR package cannot run without a terminal — nog #26.)

## Not run, and why

- **No real save on a real system.** A save writes `/etc/grub.d/40_custom`, switches scripts off and regenerates `grub.cfg`. On this desktop that is blocked by #20 (it would freeze the duplicate snapshots entry in), and the Debian VM needed manual console recovery last time. The mechanism was covered instead by running the generated file through `sh` exactly as `grub-mkconfig` does and checking the result with GRUB's own parser. **The first real save will be a user's.** The change to the file is comment lines only, after the two lines the shell executes.
- **Debian not re-run.** Nothing Debian-specific changed; the helper path was covered by §1.8 and §2.2.
