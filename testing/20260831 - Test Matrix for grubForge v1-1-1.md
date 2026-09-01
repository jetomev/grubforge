# grubForge — v1.1.1 release test matrix

Verification matrix for the **root-only `grub.cfg`** fix — the change that closes [#23](https://github.com/jetomev/grubforge/issues/23), reported by [@jfp42](https://github.com/jfp42).

grubForge reads the boot menu as your user. Where `/boot/grub/grub.cfg` is readable only by root, that read failed, the failure was swallowed, and grubForge reported **"Boot entries 0 detected"** — an empty boot menu, stated as fact, for a file it had never managed to open.

This matrix covers four things: that an unreadable file no longer looks like an empty one, that the privileged read works, that the helper does not hand back more than it should, and that **nothing changes at all** where `grub.cfg` is world-readable.

## How to run

1. Sections **11.A–11.C** run on **Arch**, against an installed grubForge v1.1.1. The unreadable condition is simulated — see 11.A.
2. Section **11.D** runs on a **Debian 13 VM**, which is the environment the bug was reported from and the only place the non-Arch install path can be tested at all.
3. Section **11.E** is the regression slice: on a normal Arch box nothing about this release should be visible to the user.
4. Tick each `[ ]` as verified. **A failure in 11.C blocks the release** — that section is the security boundary.

> **11.D was already run** on 2026-08-31, on a purpose-built Debian 13 VM (`debian13-grubforge`), and its evidence is recorded in the companion results document. Re-run it only if the code changes again. **11.9 has since been run and passed** (2026-09-01, on the Debian VM — see the F5 warning below for why it could not be run on Arch). The work still outstanding is **11.C and the 11.E regression slice**, which matters because this release rewrote a path every user walks on every launch.

> **11.A changes permissions on your real `/boot/grub/grub.cfg`.** Note the original mode before you start and put it back afterwards. Getting this wrong does not stop the machine booting — GRUB reads the file as firmware, long before permissions apply — but leaving it world-readable is exactly the exposure this release exists to avoid.

> ⚠ **STOP — 11.A and 11.B cannot be run on a UEFI Arch machine, and they fail *silently*.** (F5, found 2026-09-01.)
>
> If `/boot` is the EFI System Partition it is FAT32, which stores no Unix permissions at all. The mode `stat` reports is invented from the `fmask` mount option. So:
>
> - `sudo chmod 600 /boot/grub/grub.cfg` **exits 0 and changes nothing.** `stat` still reports the old mode.
> - `sudo mount -o remount,fmask=0177 /boot` **also succeeds and is also ignored** — the FAT driver refuses mask changes on remount. `/proc/mounts` still shows the original `fmask`.
>
> grubForge only uses the privileged helper when reading `grub.cfg` raises `PermissionError`. On a world-readable FAT32 file that read never fails, so **the code under test is never executed** — while every step appears to pass.
>
> **Before running 11.A, prove the setup actually took:**
> ```
> findmnt -no FSTYPE /boot          # vfat here means STOP, use the Debian VM
> head -1 /boot/grub/grub.cfg       # must fail with Permission denied as your normal user
> ```
> If that `head` succeeds, the unreadable condition was never created and 11.A–11.B are invalid on this machine. Run them on `debian13-grubforge` instead, where `grub.cfg` is genuinely `600` on a real filesystem and no simulation is needed.

---

## 11. v1.1.1 — a boot menu it was not allowed to read

### 11.A — Unreadable and empty are different answers

Record the starting mode first: `stat -c '%a %U:%G' /boot/grub/grub.cfg`

- [ ] **11.1** With `grub.cfg` readable as normal (`chmod 644`), launch `grubforge`. The Dashboard shows **Boot entries N detected** with the real count. Nothing about this release is visible.
- [ ] **11.2** `sudo chmod 600 /boot/grub/grub.cfg`, then relaunch. The Dashboard **no longer says "0 detected"**. It reads *"⚠ readable only by root — open Boot Entries to unlock"*.
- [ ] **11.3** No password dialog appears merely from launching the app or sitting on the Dashboard. *(Being asked for a password just to open a program is worse than the message.)*
- [ ] **11.4** Open **Boot Entries (5)**. A password dialog appears **on opening the screen, with no key pressed** — not after an F5, not after any other prompting. *(v1.1.1 pre-release hooked this to `on_mount`, which fires once at startup for every screen; the dialog never appeared and the user had to press F5 to get it. `_reload_view()` is the hook that fires when a screen is shown.)*
- [ ] **11.5** Cancel the dialog. The list shows *"Cannot read /boot/grub/grub.cfg"* and names the reason — **not** *"No boot entries found."* The two must never be confused again.
- [ ] **11.6** Press **F5**. The dialog is offered again rather than silently reporting a refreshed empty list.

### 11.B — The privileged read

- [ ] **11.7** With `grub.cfg` still at `600`, open Boot Entries and **authenticate**. The full boot menu loads, and the status line reports the number of entries loaded.
- [ ] **11.8** The entries match what `sudo grep -c '^menuentry' /boot/grub/grub.cfg` reports for top-level entries — same titles, same order, submenus with their children.
- [x] **11.9** Select an entry and reorder it (**K**/**J**), then **S** to save. The custom order writes correctly, proving the blocks returned by the helper are complete enough to rewrite `40_custom`. *(This is the check that a "titles only" fix would have failed.)* — **PASSED 2026-09-01 on the Debian VM**, not on Arch, for the reason in the F5 warning above. `40_custom` went from empty to 5 complete blocks and the VM rebooted from the regenerated menu with an identical kernel command line. Evidence: `20260901 - Test Results for grubForge v1-1-1-aur.md`.
- [ ] **11.10** `sudo chmod 644 /boot/grub/grub.cfg` and relaunch. No password is requested for the boot menu any more. **Restore your original mode now.**

### 11.C — The security boundary *(failures here block the release)*

- [ ] **11.11** `sudo /usr/lib/grubforge/grubforge-helper read-entries | head -1` — the first line is a `menuentry` or `submenu`, never a `set`, `insmod`, `if` or comment line.
- [ ] **11.12** The output is **smaller than the file**: compare `sudo /usr/lib/grubforge/grubforge-helper read-entries | wc -c` against `sudo wc -c < /boot/grub/grub.cfg`.
- [ ] **11.13** Make a canary copy containing a fake password hash, point the helper at it in a scratch checkout, and confirm neither `password_pbkdf2`, `superusers`, nor the hash string appears in the output. **Use a canary file, never your real bootloader config.**
- [ ] **11.14** `sudo /usr/lib/grubforge/grubforge-helper read-entries /etc/shadow` — refused with *"read-entries takes no arguments"*. The verb accepts no path and cannot be pointed anywhere.
- [ ] **11.15** `sudo /usr/lib/grubforge/grubforge-helper read-config` — refused with *"unknown verb"*. The vocabulary is still closed.
- [ ] **11.16** `/usr/lib/grubforge/grubforge-helper read-entries` as a normal user — refused, *"must run as root"*.
- [ ] **11.17** The two copies of `_extract_block()` still agree — run the drift diff in `RELEASE-CHECKLIST.md`. Only docstrings may differ.

### 11.D — Debian 13, the reported environment

Run on a stock Debian 13 install. **Take no hardening steps** — the question this section answers is whether an ordinary Debian user is affected, or only someone who locked the file down themselves.

- [ ] **11.18** **The headline question.** On a freshly installed, untouched Debian 13: `ls -l /boot/grub/grub.cfg`. Record the mode verbatim. If it is `600`, every Debian user has been seeing an empty boot menu, and this is far more serious than one report.
- [ ] **11.19** From a clone, launch grubForge as a normal user **without** running `install-helper.sh`. It reports that the helper is not installed **and names `sudo sh install-helper.sh` as the fix** — the old message named only the Arch package, which is useless here.
- [ ] **11.20** Run `sudo sh install-helper.sh`. It reports both files installed, `root:root`, helper `755`, policy `644`.
- [ ] **11.21** Run `sh install-helper.sh` **without** sudo — refused, exit status 1, nothing written.
- [ ] **11.22** Relaunch grubForge as a normal user. The read-only badge is gone; capability is `polkit`.
- [ ] **11.23** Open Boot Entries. A **graphical password dialog** appears. *(Debian's administrator group is `sudo`, not `wheel` — this is the check that `auth_admin_keep` resolves correctly off Arch, which cannot be verified any other way.)*
- [ ] **11.24** Authenticate with the ordinary user's own password. The boot menu loads with the real entries.
- [ ] **11.25** `pkaction --action-id org.kognogos.grubforge.manage --verbose` reports the same exec path and `auth_admin_keep`.

### 11.E — Nothing changed where nothing should change

The read path is walked by every user on every launch. This release rewrote it. Run this section on a **normal Arch box with a world-readable `grub.cfg`**, where the correct outcome is that you cannot tell v1.1.1 from v1.1.0.

**Boot Entries — the screen that changed most**

- [ ] **11.26** Open Boot Entries. Entries appear immediately, **no password is requested**, and the status line reads *"Loaded N boot entries from /boot/grub/grub.cfg"*.
- [ ] **11.27** The count and titles match `grep -c '^menuentry' /boot/grub/grub.cfg` plus submenus, and every submenu shows its child count.
- [ ] **11.28** Source labels are right — Arch Linux, Windows via OS Prober, UEFI, snapshots — i.e. `_guess_source()` still receives real titles.
- [ ] **11.29** **K**/**J** reorder, then **S** to save. `/etc/grub.d/40_custom` is written with the grubForge header and the entries in the new order.
- [ ] **11.30** **N** renames an entry; the new title survives a save and reappears after **F5**.
- [ ] **11.31** **X** restores the original order; `40_custom` returns to its pre-grubForge state.
- [ ] **11.32** Create a custom entry from a template. It appears in the list and writes correctly.
- [ ] **11.33** Leave Boot Entries for another screen and come back several times. No password is ever requested, and no duplicate load or flicker — `_reload_view()` now does more than it used to.
- [ ] **11.34** Press **F5** repeatedly. Each press reports *"Boot entries refreshed."* and nothing is asked for.

**Dashboard — the other file that changed**

- [ ] **11.35** The Dashboard shows **Boot entries N detected** with the real number, in the normal colour — not the yellow permission warning.
- [ ] **11.36** With `/boot/grub/grub.cfg` temporarily renamed away, the Dashboard reports *"Not found (run grub-mkconfig)"* — the missing-file case must not be confused with the unreadable one. **Put it back.**
- [ ] **11.37** Sync status still shows all three states correctly: pending changes, `grub.cfg` older than `/etc/default/grub`, and in sync.

**Everything else this release should not have touched**

- [ ] **11.38** Backup create / restore / delete, each with its password prompt, exactly as in v1.1.0.
- [ ] **11.39** Config Editor: edit a value, save, and `Ctrl+R` regenerate. The boot menu rebuilds.
- [ ] **11.40** Theme browser applies a theme and prompts to regenerate.
- [ ] **11.41** os-prober scan and enable behave as before.
- [ ] **11.42** `sudo grubforge` still works, shows the yellow **ROOT** badge, and asks for nothing.
- [ ] **11.43** Over SSH with no authentication agent, grubForge degrades honestly — read-only, with the reason naming `sudo` — and the boot menu still **displays**, because reading never needed permission here.

## Build-time checks

- [ ] **11.44** Version agrees across `grubforge/__init__.py`, `grubforge/app.py`, `grubforge.1` `.TH`, README version badge, README AUR cache-buster, and the AUR `PKGBUILD` + `.SRCINFO`.
- [ ] **11.45** `grep -rn "run_worker(self\.action_" grubforge/` returns nothing.
- [ ] **11.46** Constants duplicated between the package and the helper still match, `_extract_block()` included — run the drift diff in `RELEASE-CHECKLIST.md`.
- [ ] **11.47** README documents `install-helper.sh`, and the path it writes matches the polkit policy and `privilege.py`.
- [ ] **11.48** The signed release tarball verifies: `gpg --verify grubforge-1.1.1.tar.gz.asc grubforge-1.1.1.tar.gz`.
- [ ] **11.49** The tarball contains `install-helper.sh`, `helper/grubforge-helper` and `polkit/`, and `__init__.py` inside it reads 1.1.1.
