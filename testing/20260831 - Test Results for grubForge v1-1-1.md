# grubForge — v1.1.1 test results

**Date:** 2026-08-31 (Monday evening)
**Hosts:** KognogOS desktop (Arch) for the automated checks; a purpose-built **Debian 13 (trixie) VM** for the reported environment
**Build:** local checkout, helper and policy installed into their packaged locations inside the VM via `install-helper.sh`
**Tested against:** `testing/20260831 - Test Matrix for grubForge v1-1-1.md`

Companion to the matrix. Records what was verified, what was deliberately not run, and the findings — including one that only appeared because the fix was tested in the environment it was reported from.

---

## Verdict

**Ship the code.** The fix works end to end on stock Debian 13: an ordinary user opens Boot Entries, a graphical polkit dialog appears unprompted, and the real boot menu loads. The security boundary holds — the helper withholds 59% of the file and every verb refusal fires.

**Two caveats, stated plainly:**

1. The **Arch interactive walkthrough (11.1–11.10, 11.26–11.28) was not run by hand.** Its substance was covered by automated tests against a real `grub.cfg` and a deliberately unreadable copy, but nobody sat in the TUI on Arch and reordered a boot entry read through the helper. See *Not run*.
2. The **AUR package is not cut.** Publicly promised as following the code, not accompanying it.

---

## The discovery that mattered more than the bug

The report was written as though it were one person's unusual setup. It is not.

| Fact | Value |
|---|---|
| Distribution | Debian GNU/Linux 13 (trixie), stock install, all defaults |
| Kernel | 6.12.94+deb13-amd64 |
| `grub-common` | 2.12-9+deb13u2 |
| `/boot/grub/grub.cfg` | **`-rw------- root root`** |
| GRUB password configured | **no** — `password_pbkdf2` / `superusers` match count: 0 |
| Hardening applied | none |

Debian ships the file root-only by default. **Every Debian user running grubForge has been shown an empty boot menu and told it was accurate.** `@jfp42` is not an edge case; he is the one who wrote in.

---

## What was verified

### Environment (11.D)

| Fact | Value |
|---|---|
| User | `grubforge`, member of `sudo` |
| polkit | `pkexec` present; agent `polkit-mate-authentication-agent-1` running (PID 1381) |
| polkit admin identity | Debian's `sudo` group — `auth_admin_keep` resolved correctly off Arch |
| Textual | Debian's `python3-textual` **2.1.2-1**, installed from `trixie/main` |
| `pip3` | **not installed at all** |

### The bug, and that it is fixed (11.A / 11.B) — **pass**

- Dashboard no longer reports `0 detected`; it names the permission problem.
- Boot Entries asks for permission **on opening the screen**, no key pressed *(only after F1 below was fixed)*.
- Authenticating as the ordinary user loads the real boot menu — confirmed visually in the VM.
- Automated equivalence check on Arch: parsing the helper's output and parsing the whole file produce **identical entry counts, identical titles in identical order, and identical raw blocks**.

### The security boundary (11.C) — **pass**

| Check | Result |
|---|---|
| 11.11 | First line returned is `menuentry 'Debian GNU/Linux' …` — never a `set`, `insmod`, `if` or comment |
| 11.12 | Helper returns **2269 bytes of a 5581-byte file — 3312 bytes (59%) withheld** |
| 11.13 | `set default` appears twice in the file, **zero times** in the output. On a synthetic config carrying a fake `password_pbkdf2` hash, neither the hash, nor `password_pbkdf2`, nor `superusers` appeared in the output, while all three menu entries and both submenu children came through intact |
| 11.14 | `read-entries /etc/shadow` → *"read-entries takes no arguments"* |
| 11.15 | `read-config` → *"unknown verb 'read-config' — refusing"* |
| 11.16 | as a normal user → *"must run as root"* |
| 11.17 | `_extract_block()` byte-identical between package and helper; only docstrings differ |

The `insmod` count (28 in file, 12 returned) is not a leak — those 12 are inside `menuentry` blocks, where they belong. The 16 in the header were withheld.

### The non-Arch install path (11.D) — **pass**

| Check | Result |
|---|---|
| 11.19 | Message names `sudo sh install-helper.sh`, not only the Arch package |
| 11.20 | Helper `-rwxr-xr-x root root`; policy `-rw-r--r-- root root` |
| 11.21 | `sh install-helper.sh` without root → refused, exit 1, nothing written |
| 11.22–11.24 | Capability `polkit`; graphical dialog; ordinary user's own password; entries loaded |
| 11.25 | `implicit active: auth_admin_keep`, `exec.path -> /usr/lib/grubforge/grubforge-helper`, `allow_gui -> true` |

---

## Findings

### F1 — the password dialog never appeared; the user had to press F5 *(fixed, before release)*

The auto-prompt was hooked to the screen's `on_mount`. In this app every screen is mounted at startup and shown by toggling `display`, so `on_mount` fires once for all screens before the user has opened anything — and the dialog never arrived when Boot Entries was actually opened. The screen showed *"Cannot read /boot/grub/grub.cfg"* and sat there; F5 worked because `action_refresh` asked explicitly.

Moved to `_reload_view()`, which `_switch_to()` already calls every time a screen is shown, with a comment in `app.py` saying exactly that. The hook existed and was not used. Also moved onto `self.app.run_worker(…, group="grubcfg-read")` to match every other worker in the file and to avoid cancelling an in-flight os-prober scan.

**This is the finding that justified the VM.** Every automated test passed with the bug present, because none of them opened a screen.

### F2 — the README's install instructions were wrong for Debian *(fixed, before release)*

"Other distributions" said `pip install textual rich`. On Debian 13 `pip3` is not installed, and current Debian refuses `pip install` into the system Python (PEP 668). Meanwhile Debian **does** package `python3-textual`. The advice sent users down a path that does not exist while ignoring the one that does.

Rewritten as a Debian/Ubuntu section using `apt`, and a generic section using a virtual environment.

### F3 — Fedora and openSUSE use `/boot/grub2/`, and are unsupported → **[#24](https://github.com/jetomev/grubforge/issues/24)** *(deferred to after 2026-09-14)*

`GRUB_CFG_PATH` is `/boot/grub/grub.cfg` in both the package and the helper, and the theme directory and `grub-mkconfig` invocation are hardcoded the same way. The Dashboard alone resolves `/boot/grub2/` — and nothing else uses that resolver, so on Fedora the Dashboard reports a real boot-entry count while every other screen points somewhere that does not exist. A working-looking dashboard with broken screens is a worse failure than an honest one at launch.

Pre-existing and app-wide, deliberately not fixed inside a read-path release: changing that constant in one copy and not the other is precisely the drift `RELEASE-CHECKLIST.md` treats as a security bug.

### F4 — Textual version skew on Debian *(noted, not a defect)*

Debian ships Textual 2.1.2; grubForge is developed against 8.x. It ran correctly on 2.1.2 for every path exercised, but only Dashboard and Boot Entries were exercised. Recorded in the README rather than claimed as full compatibility.

---

## Not run, and why

| Matrix item | Reason |
|---|---|
| 11.1–11.10 (Arch, interactive) | Covered by automated tests against the real `grub.cfg` and a `chmod 000` copy — the raising of `GrubCfgUnreadable`, the `None` vs `0` distinction, and raw-block equality. Nobody drove the TUI on Arch by hand. |
| **11.9** (reorder and save a menu read through the helper) | **Not run anywhere.** Raw-block equality was proven structurally, so the data needed to rewrite `40_custom` is present, but no save was performed from a helper-read menu. This is the highest-value remaining check. |
| 11.26–11.28 (Arch regression slice) | Not run. The read path changed for everyone, and only the Debian path was exercised interactively. |
| 11.29 (AUR `PKGBUILD` / `.SRCINFO`) | AUR cut deferred; version synced across the six in-repo surfaces only. |

---

## Next-session handoff (read this first)

1. **Run 11.9 first.** Lock `grub.cfg` to `600` on Arch, open Boot Entries, authenticate, reorder an entry, save, and confirm `40_custom` is written correctly. It is the one check that would catch the helper returning blocks that look right but are not complete. Restore the original mode afterwards.
2. **Then the Arch regression slice (11.26–11.28)** — this release touched a path every user goes through.
3. **Then the AUR cut**: bump `PKGBUILD`, regenerate `.SRCINFO`, `makepkg -si` smoke, push, verify with a fresh helper install.
4. ~~File F3 as its own issue~~ — filed as **[#24](https://github.com/jetomev/grubforge/issues/24)**, scheduled for after 2026-09-14.
5. The Debian VM (`debian13-grubforge`, user `grubforge`) is kept — it is the only place the non-Arch path can be tested, and it will be needed again for F3.
