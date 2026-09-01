# Test Results — grubForge v1-1-1 (11.9 and the AUR cut)

**Date:** 2026-09-01
**Scope:** the one outstanding check from the v1.1.1 release (matrix item 11.9), plus the AUR cut it was gating.
**Continues:** `20260831 - Test Results for grubForge v1-1-1.md`, whose handoff listed 11.9 as item 1.

---

## Summary

| | |
|---|---|
| **11.9** | **PASS**, on Debian 13 — with a reboot as the final proof |
| **AUR cut** | v1.1.1-1 pushed |
| **New findings** | F5 (matrix step unrunnable on UEFI Arch), F6 (`nog` cannot install a local package file), F7 (AUR badge cached the previous version — fixed same session) |
| **Still not run** | 11.26–11.28, the Arch regression slice |

---

## 11.9 — reorder and save a menu read through the privileged helper

**Result: PASS.** Run on the `debian13-grubforge` VM: Debian 13 trixie, XFCE on display `:0`, Textual 2.1.2, `/boot` on the root filesystem, `grub.cfg` at `600 root:root`. The installed helper was byte-identical to the v1.1.1 source (`sha256 d03175c9fa6f34c22cc395193a2cff6d2a638bb03c324a65c9f69cbbe8c60b3d`), so the code under test was the code that shipped.

The user genuinely could not read `grub.cfg`, which is what puts the app on the fixed path rather than the direct-read path.

### What was done

Boot Entries was opened as the normal user, authenticated through polkit, one entry was moved with **K**/**J**, and the order was saved with **S**.

### Evidence

| Check | Before | After |
|---|---|---|
| `40_custom` size | 5 lines, `sha256 894dd8e4…` | 50 lines / 2457 bytes, `sha256 0bbb40c3…` |
| Entries in `40_custom` | none (stock Debian header) | 5 blocks, reordered — UEFI Firmware Settings moved to the top |
| Braces | — | 5 open, 5 close, balanced |
| Body lines | — | 3 `linux`, 3 `initrd`, 3 `search` |
| Shebang and exec bit | `#!/bin/sh`, executable | unchanged — GRUB would ignore the file otherwise |

The `linux`/`initrd`/`search` count of 3 against 4 boot entries is correct, not a shortfall: *UEFI Firmware Settings* legitimately has none, using `fwsetup` instead. That entry was preserved with its `fwsetup` body intact.

Kernel command lines survived verbatim, including `resume=UUID=a5d05379-c8f4-43af-83b0-d315b1d33b62` on the normal entry and `single dis_ucode_ldr` on the recovery entry. Submenu nesting was preserved, with both children inside *Advanced options*.

### Generators

grubForge disabled exactly the two generators whose entries it took over — `10_linux` and `30_uefi-firmware` — recording their original permissions in `10_linux.grubforge_perms` and `30_uefi-firmware.grubforge_perms` so the change is reversible. No duplication was produced.

`20_linux_xen`, `25_bli`, `30_os-prober` and `41_custom` still run, but emit nothing on this VM. **Issue #20 is therefore not disproven by this run** — it bites where an unmanaged generator actually produces entries, which this VM has none of.

### Save triggers regeneration

`40_custom` was written at `18:29:22.560`; `grub.cfg` was rewritten at `18:29:23.252`. The save regenerated the menu 0.7 s later, unprompted.

### The proof that matters

The VM was rebooted and came back over SSH in roughly 35 seconds. `/proc/cmdline` on the fresh boot read:

```
BOOT_IMAGE=/boot/vmlinuz-6.12.94+deb13-amd64 root=UUID=2be9abfa-107d-4d28-b325-05620d9b422b ro quiet splash resume=UUID=a5d05379-c8f4-43af-83b0-d315b1d33b62
```

That is, character for character, the `linux` line grubForge had written into `40_custom`. A fix that returned titles without bodies could not have produced a bootable menu at all. **This is the check the release needed, and it passes.**

---

## F5 — matrix step 11.9 is unrunnable on UEFI Arch, and fails silently

The v1.1.1 matrix instructs: *"Lock `grub.cfg` to `600` on Arch."* On a standard UEFI Arch system this cannot be done, and — the dangerous part — **nothing reports an error**.

`/boot` is the EFI System Partition, formatted FAT32. FAT32 stores no Unix permissions; the mode shown by `stat` is synthesized from the `fmask` mount option. Two things follow:

1. `sudo chmod 600 /boot/grub/grub.cfg` exits **0** and changes nothing. `stat` still reports `755`.
2. `sudo mount -o remount,fmask=0177 /boot` also succeeds and is also ignored — the FAT driver does not accept mask changes on remount. `/proc/mounts` still shows `fmask=0022`.

Both were run on the desktop and both behaved exactly this way.

Because grubForge only falls back to the helper when reading `grub.cfg` raises `PermissionError`, and that read can never fail on a world-readable FAT32 file, **the helper read path cannot be exercised on a UEFI Arch machine at all** — short of unmounting `/boot` and remounting it with different masks.

**Why this matters more than a wording fix:** a tester following the matrix would set the permission, see no error, run the test, and record a pass — having never executed the code under test. The step does not merely fail; it fails while looking like it succeeded.

**Correction for the matrix:** 11.9 belongs under Debian, not Arch. It is a check on the root-only-`grub.cfg` path, and the Debian VM is where that path is real. Any future Arch variant must first assert that the read actually failed, rather than assuming the `chmod` took.

---

## F6 — `nog` cannot install a locally built package file

`nog install` always builds a `-S` command (`src/pacman.rs:90`, `src/aur.rs:151`), which takes package *names* from a configured repository. There is no path to `pacman -U <file>`.

Installing a locally built `.pkg.tar.zst` is a step in the release process for every Forge package, so this gap is hit on every release, and the only way through is raw `pacman` — which the working agreement otherwise rules out on this machine.

Encountered today installing `grubforge-1.1.1-1-any.pkg.tar.zst` before running 11.9. Filed against `nog`, not grubForge.

---

## F7 — the README AUR badge advertised 1.1.0 after 1.1.1 went live → **[#26](https://github.com/jetomev/grubforge/issues/26)** *(fixed and closed same session)*

Caught by Javier asking whether the badge had been updated. It had — and that was the problem.

`README.md` already carried the cache-buster `?v=1.1.1`, exactly as `RELEASE-CHECKLIST.md` required. Yet decoding the camo URL from the rendered README and fetching it three times returned `aur: v1.1.0-1` every time, while shields.io returned `aur: v1.1.1-1` for the byte-identical URL.

The checklist listed the buster among the **version surfaces**, all of which are updated in the docs commit — which lands *before* the AUR push. So camo fetched the badge under the fresh `?v=1.1.1` key while the AUR still held 1.1.0, and cached that for its five-day `max-age`. The AUR push then changed the AUR but not the cache key.

**The cache-buster did its job perfectly and cached the wrong answer.** The defect was the order of operations, not the value — which is precisely why a checklist gate written about this exact badge did not catch it.

Fixed in `c17772e`: the badge now uses the full `pkgver-pkgrel` (`?v=1.1.1-1`) and is confirmed serving `aur: v1.1.1-1`. The checklist moves the buster to a post-push step and adds the command to read back what camo is actually serving, because a clean `git push` is not evidence here.

This is the third finding today of the same shape — F5, F6 and F7 are all mechanisms that reported success while doing the wrong thing, or not running at all.

---

## AUR cut — v1.1.1-1

Pre-flight, all read-only, all passed:

- `sha256` of the release tarball matches the asset GitHub actually serves (`b4bb8b1f…`) — checked against a freshly downloaded copy, not the one already on disk
- `gpg --verify` passes: good signature from `32E1D2AB9380BFD6BFE3BC1EAC2A3407CC070F9E`
- `makepkg --printsrcinfo` matches `.SRCINFO`
- `git ls-files` returns exactly `PKGBUILD`, `.SRCINFO`, `.gitignore` — packaging only
- `makepkg` build clean; the headless-mount smoke and the helper refusal checks both pass

There is no root `PKGBUILD` in the grubForge repo, so the divergence hazard described in the release rules does not apply here.

---

## Environment notes for next time

The `debian13-grubforge` VM now has `openssh-server` installed, and the desktop reaches it as `grubforge-vm` (key `~/.ssh/id_ed25519_grubforge-vm`, host alias in `~/.ssh/config`). Setup and verification can be driven over SSH; only the interactive TUI steps need the VM window, because grubForge runs `pkexec --disable-internal-agent` by design and the password box must come from the desktop's polkit agent (`polkit-mate-authentication-agent-1`, already running there).

The VM's `40_custom` is left in its reordered state. Use **Boot Entries → Restore Original** to reset it; a backup of the original sits at `~/11.9-baseline/40_custom.before`.

---

## Still outstanding

1. **11.26–11.28, the Arch regression slice.** The read path changed for every user and has still only been driven by hand on Debian.
2. **Issue #20** remains open and untested — this VM has no unmanaged generator that emits entries.
3. **Issue #24** (Fedora / openSUSE / RHEL) deferred to after 2026-09-14.
