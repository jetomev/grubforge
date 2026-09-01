# grubForge — v1.1.1 release test matrix

Verification matrix for the **root-only `grub.cfg`** fix — the change that closes [#23](https://github.com/jetomev/grubforge/issues/23), reported by [@jfp42](https://github.com/jfp42).

grubForge reads the boot menu as your user. Where `/boot/grub/grub.cfg` is readable only by root, that read failed, the failure was swallowed, and grubForge reported **"Boot entries 0 detected"** — an empty boot menu, stated as fact, for a file it had never managed to open.

This matrix covers four things: that an unreadable file no longer looks like an empty one, that the privileged read works, that the helper does not hand back more than it should, and that **nothing changes at all** where `grub.cfg` is world-readable.

## How to run

1. Sections **11.A–11.C** run on **Arch**, against an installed grubForge v1.1.1. The unreadable condition is simulated — see 11.A.
2. Section **11.D** runs on a **Debian 13 VM**, which is the environment the bug was reported from and the only place the non-Arch install path can be tested at all.
3. Section **11.E** is the regression slice: on a normal Arch box nothing about this release should be visible to the user.
4. Tick each `[ ]` as verified. **A failure in 11.C blocks the release** — that section is the security boundary.

> **11.A changes permissions on your real `/boot/grub/grub.cfg`.** Note the original mode before you start and put it back afterwards. Getting this wrong does not stop the machine booting — GRUB reads the file as firmware, long before permissions apply — but leaving it world-readable is exactly the exposure this release exists to avoid.

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
- [ ] **11.9** Select an entry and reorder it (**K**/**J**), then **S** to save. The custom order writes correctly, proving the blocks returned by the helper are complete enough to rewrite `40_custom`. *(This is the check that a "titles only" fix would have failed.)*
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

- [ ] **11.26** On an Arch box with a world-readable `grub.cfg`, run through Boot Entries: reorder, rename, restore original, create a custom entry. No password is requested for reading at any point, and behaviour is identical to v1.1.0.
- [ ] **11.27** Backups, Config Editor, Themes, os-prober and `Ctrl+R` regeneration all behave as in v1.1.0 — this release touched the read path only.
- [ ] **11.28** `sudo grubforge` still works and still shows the yellow **ROOT** badge.

## Build-time checks

- [ ] **11.29** Version agrees across `grubforge/__init__.py`, `grubforge/app.py`, `grubforge.1` `.TH`, README version badge, README AUR cache-buster, and the AUR `PKGBUILD` + `.SRCINFO`.
- [ ] **11.30** `grep -rn "run_worker(self\.action_" grubforge/` returns nothing.
- [ ] **11.31** Constants duplicated between the package and the helper still match, `_extract_block()` included.
- [ ] **11.32** README documents `install-helper.sh` under "Other distributions", and the path it writes matches the polkit policy and `privilege.py`.
