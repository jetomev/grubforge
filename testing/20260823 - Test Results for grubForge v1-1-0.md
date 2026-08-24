# grubForge — v1.1.0 test results

**Date:** 2026-08-23 (Sunday evening)
**Host:** KognogOS desktop, Arch, Plasma 6 / Wayland on tty1, `polkit-kde-authentication-agent-1` running
**Build:** local checkout at `d4a3eac`, helper and policy installed manually to their packaged locations
**Tested against:** `testing/20260823 - Test Matrix for grubForge v1-1-0.md`

Companion to the matrix. Records what was verified, what was deliberately not run and why, and the five findings.

---

## Verdict

**Ship.** The privilege model works end to end on real hardware, the security boundary holds under hostile input, and three findings were fixed during the run. Two findings are pre-existing behaviour outside this release's scope and are filed as issues.

The release's central claim — *grubForge no longer needs `sudo`* — was demonstrated by editing this machine's live `/etc/default/grub` as an unprivileged user and rebuilding the boot menu, with no `sudo grubforge` at any point.

---

## What was verified

### Environment (10.A)

Checked before writing any code, rather than assumed:

| Fact | Value |
|---|---|
| pkexec | version 127 |
| polkit admin identity | `unix-group:wheel` (`/usr/share/polkit-1/rules.d/50-default.rules:11`) |
| User in `wheel` | yes |
| Authentication agent | `polkit-kde-authentication-agent-1`, PID 5247 |

This is what makes the public promise on #18 accurate: because polkit's admin group is `wheel` and the user is in it, the dialog asks for **the user's own password, not root's**.

`pkaction --action-id org.kognogos.grubforge.manage --verbose` reports `implicit active: auth_admin_keep` and the expected exec path. Helper is `root:root 755`.

### The authorisation flow (10.B) — **pass**

- **10.5–10.7** Confirm dialog announced the password in advance; a **graphical** dialog appeared (not a terminal prompt); the user's own password was accepted; backup created.
- **10.8** New backup is `root:root 644` and **byte-identical** to `/etc/default/grub` (`diff -q`).
- **10.10–10.11** `GRUB_TIMEOUT` changed 10→5 in the Config Editor. Backup **and** config write happened with **one** prompt. `Ctrl+R` regenerate immediately afterwards proceeded with **no second prompt** — `auth_admin_keep` working as designed.
- **10.12** The temporary authorisation **expired on its own** during the session; `pkcheck --list-temp` was empty a few minutes later. It is not a session-long grant.
- **10.37** Backups written by v1.0.x (dating back to 2026-05-15) still list with their original labels and timestamps.

The value was later changed back to 10 through the app, and `grub.cfg` confirmed at `set timeout=10`.

### The security boundary (10.C) — **pass**

All refusals exercised against the **installed** helper through `pkexec`, not the source copy.

| Check | Input | Result |
|---|---|---|
| 10.16 | Cancel the password dialog | *"Cancelled — nothing was changed."*, warning styling, nothing written |
| 10.17 | `regenerate` while unprivileged | refused, *"must run as root"* |
| 10.18 | `definitely-not-a-verb` | refused, *"unknown verb … refusing"* |
| 10.19 | `backup-delete ../../../<canary>` | refused, **canary survived** |
| 10.20 | `backup-restore ../../../<canary>` | refused, **canary survived** |
| 10.21 | `script-enable ../../../bin/sh`, `script-disable 00_header` | both refused by name |
| 10.22 | `write-config` with `id > /tmp/gf-pwned` on stdin | refused at line 2; config checksum unchanged; **`/tmp/gf-pwned` never created** |
| 10.23 | `write-custom-40` without `#!/bin/sh` | refused |
| 10.24 | after successful writes | no stray `.grubforge-*` temp files; config still `root:root 644` |

Traversal checks used a canary file rather than a real system path, per the matrix. If validation had been broken, the test would have destroyed something disposable.

**Worth recording:** the refusals in 10.19–10.23 ran while the polkit authorisation was **already cached**, so no password was requested — and they were refused anyway. Authorisation and validation are independent layers, and the second one held on its own.

### Build-time (10.41–10.42) — **pass**

Headless mount smoke test and the new helper refusal checks both pass in `check()`.

---

## Findings

### F1 — `__init__.py` version stale *(fixed, `3930c41`)*

`grubforge/__init__.py` was still `1.0.3` after every other version string had been bumped. Caught by the release checklist's version-sync gate.

Notable because v1.0.3 itself shipped after fixing this same class of bug in `app.py`. **Twice now.** The checklist gained a note calling `__init__.py` out by name so the third occurrence is caught.

### F2 — confirmation dialogs silently swallowed backup labels *(fixed, `2658b58`)*

`ConfirmDialog` renders its message through a Textual `Static`, which parses Rich markup. The message carries real data — backup labels like `[pre-edit]`, entry titles, config values. Rich read those square brackets as a markup tag and **dropped them with no error**.

Concretely: the Restore dialog showed a bare timestamp, with the label identifying *which* backup you were about to overwrite `/etc/default/grub` with simply missing.

Pre-existing, not a v1.1.0 regression. Surfaced only because Javier asked for the password heads-up to be yellow, which meant making it a real dialog element rather than markup appended to the message — and that raised the question of what else in that string was being parsed.

Fixed by escaping the message and adding a separate `note=` element in the title's `#f9e2af`.

### F3 — a documented promise the code did not keep *(fixed, `d4a3eac`)*

The rewritten README claimed grubForge "tells you so instead of failing mysteriously" when there is no authentication agent. It did not. It relayed pkexec's stderr, which in that situation reads:

```
Error executing command as another user: Not authorized
This incident has been reported.
```

That sounds like a security event. It means there was no window to show a dialog in.

Found by writing the test for the claim and realising the claim could not be true, because `detect()` cannot know whether an *agent* is running — only that polkit, the helper and the policy exist, which they do on a text console.

Fixed by replacing the 127 message with one naming both possible causes (rejected password, or no agent) and pointing at `sudo`. pkexec does not distinguish the two cases, so grubForge does not guess. Matrix §10.29 was corrected too — it had asserted a READ-ONLY badge that the code does not and cannot show.

### F4 — unmanaged generators duplicate entries → **[#20](https://github.com/jetomev/grubforge/issues/20)** *(deferred)*

Saving a custom order copies entries from generator scripts outside `MANAGED_SCRIPTS` into `40_custom` without disabling them, so they render twice.

On this machine, `41_snapshots-btrfs` is executable and produces a "KognogOS snapshots" submenu. Saving the order would have written that entry into `40_custom` while the generator continued to emit it — a duplicate in the live boot menu.

**Pre-existing; unchanged from v1.0.3.** Only visible now because `render_custom_order()` was split out as a pure function during the privilege work, so the proposed content could be diffed against the live file **without writing it**. Closely related to #19 — same underlying gap.

### F5 — unreadable on a text console → **[forgekit#1](https://github.com/jetomev/forgekit/issues/1)** *(deferred)*

On `TERM=linux` the interface loses most of its structure: the console offers **8 colours and 64 pairs** against grubForge's **27 distinct hex values**, and the default console font has no glyphs for the nav emoji.

This matters more for grubForge than its siblings: a text console is where you end up when the desktop is broken, which is when you want a bootloader manager — and v1.1.0's own README documents that path. Filed on forgekit because semantic colour tokens and glyph fallbacks belong in the shared layer, with trackers on all four apps (grubForge #21, alacrittyForge #7, bitlaForge #2, nogForge #1).

---

## Not run, and why

Recorded rather than quietly omitted.

| Matrix item | Reason |
|---|---|
| **10.25–10.27** Boot Entries save / restore / partial completion | Deliberate. This machine has been in frozen-entries mode since 2026-05-21, with its real boot menu — including Windows 11 — living in `40_custom`. Running these would have written a duplicate entry (F4) into the live boot menu of the machine under test. Javier's call: skip and file the issue. The **rendered output was diffed against the live file** instead, which is what found F4. |
| **10.2, 10.30, 10.32** ROOT-badge paths | Not exercised. `sudo` paths are unchanged from v1.0.3 behaviour and the badge is cosmetic. |
| **10.9** rotation at MAX_BACKUPS | Not observed directly. Rotation code runs in the helper and is exercised on every `backup-create`; the directory held exactly 10 at the close of testing. |
| **10.13–10.15** theme apply, restore, delete | Not run. Same code path as 10.10 (backup + `write-config`), which passed. |
| **10.33–10.35** os-prober | Not run — os-prober is installed on this host, so the "not installed" guidance path could not be reached without removing it. |
| **10.28** UI responsiveness during the dialog | Not measured rigorously. No freeze was observed during the runs that did happen. |
| **10.31** source-checkout read-only | Verified programmatically before the helper was installed: `detect()` returned `NONE` with the "helper is not installed" reason. Not seen in the running UI. |

**Highest-value gap:** 10.25–10.27. The partial-completion message — *"Order saved, but grub.cfg was not regenerated — press Ctrl+R when ready"* — has never been read by a human on screen. It should be exercised on a VM, or on this host once #20 is resolved.

---

## Next-session handoff (read this first)

- **v1.1.0 is ready to tag.** Testing complete, three fixes landed during the run, two findings filed as issues.
- **Do not run Boot Entries save/restore on the desktop** until **#20** is fixed. It will duplicate the snapshots entry in the live boot menu. The safe way to inspect is `render_custom_order(parse_boot_entries())` and diff — it writes nothing.
- **The desktop remains in frozen-entries mode** (since 2026-05-21). `/etc/default/grub` is largely inert there — that is **#19**, and it is still open.
- **Open after this release:** #17, #19, #20, #21.
- **Next cycle is v2.0.0 — forgekit migration** (Javier, 2026-08-23). **forgekit#1 (console rendering) should land in forgekit before that migration**, so grubForge inherits it rather than being retrofitted afterwards.
- The helper and policy on this machine were installed **by hand** from the checkout during testing. Installing the real package will overwrite both; if the helper is edited again, reinstall it or the tested copy and the running copy will drift.
