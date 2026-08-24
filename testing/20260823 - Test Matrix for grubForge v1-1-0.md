# grubForge — v1.1.0 release test matrix

Verification matrix for the **polkit privilege model** — the change that closes [#18](https://github.com/jetomev/grubforge/issues/18), reported by [@marco-gallegos](https://github.com/marco-gallegos).

This release moves grubForge off `sudo`. The application now runs as an ordinary user and asks polkit for authorisation one action at a time. Because the change touches how *every* write happens, this matrix covers three things: that changes still work, that the security boundary actually holds, and that the app degrades honestly when it cannot escalate.

## How to run

1. Test against a **clean install of grubforge v1.1.0-1 from the AUR** (`yay -S grubforge`) on an Arch host with an active desktop session and a running polkit authentication agent.
2. Run sections 10.A–10.D **as your normal user, without sudo**. That is now the primary supported way to use grubForge.
3. Run section 10.E in the two degraded environments named there.
4. Tick each `[ ]` as verified. If anything in **10.C** fails, stop — that section is the security boundary, and a failure there is a release blocker, not a bug report.

> **Section 10.C attempts hostile input against a root helper.** Use the canary-file form given, never a real system path. If a check fails, the difference between those two choices is the difference between a failed test and a damaged system.

---

## 10. v1.1.0 privilege model

### 10.A — Capability detection and what the user is told

- [ ] **10.1** Launch `grubforge` as your normal user on a desktop session. The sidebar shows **no badge** — not DEMO, not READ-ONLY, not ROOT. Running unprivileged is now the normal, fully-capable case.
- [ ] **10.2** Launch `sudo grubforge`. The sidebar shows a yellow **ROOT** badge reading *"no prompts"*.
- [ ] **10.3** Run `pkaction --action-id org.kognogos.grubforge.manage --verbose`. It reports `implicit active: auth_admin_keep`, and an exec path of `/usr/lib/grubforge/grubforge-helper`.
- [ ] **10.4** Confirm the helper is root-owned and not writable by your user: `ls -l /usr/lib/grubforge/grubforge-helper` shows `-rwxr-xr-x root root`. *(A user-writable root helper would defeat the entire model.)*

### 10.B — The authorisation flow, end to end

- [ ] **10.5** Backup & Restore (**4**), press **N**. The confirm dialog includes **"You will be asked for your password."** before you commit to anything.
- [ ] **10.6** Confirm it. A **graphical password dialog** appears — from your desktop, not a prompt inside the terminal — saying *"grubForge needs permission to change your bootloader settings."*
- [ ] **10.7** Enter **your own** password (not root's). The backup is created and appears in the list immediately.
- [ ] **10.8** Verify on disk: the new file in `/var/lib/grubforge/backups/` is `root:root`, mode `644`, and byte-identical to `/etc/default/grub` (`diff -q`).
- [ ] **10.9** With exactly `MAX_BACKUPS` (10) present, create one more. The **oldest is rotated out**, and its `.label` sidecar goes with it — no orphaned label files remain.
- [ ] **10.10** Config Editor (**2**): change `GRUB_TIMEOUT`, press **S**, confirm. A backup is taken *and* the config written — and you are asked for your password **once**, not twice. *(This is `auth_admin_keep`.)*
- [ ] **10.11** Immediately after 10.10, press **Ctrl+R** to regenerate. It proceeds **without a second prompt**. Run `pkcheck --list-temp` right after authenticating to see the live temporary authorisation that explains this.
- [ ] **10.12** Wait several minutes, then trigger another change. The prompt **returns** — the authorisation expires rather than lasting the session. Confirm `pkcheck --list-temp` is empty by then.
- [ ] **10.13** Themes (**3**): apply a theme. Backup plus config write, one prompt, theme reflected on the Dashboard.
- [ ] **10.14** Backup & Restore: restore a backup (**X**). A pre-restore snapshot labelled `auto (pre-restore)` is created automatically, so the restore is itself undoable.
- [ ] **10.15** Delete a backup (**D**). Both the `.bak` and its `.label` disappear.

### 10.C — The security boundary *(failures here block the release)*

- [ ] **10.16** **Cancel the password dialog.** Press Escape or Cancel. grubForge reports **"Cancelled — nothing was changed."** as a *warning, not an error* — and nothing was written. Verify with `diff` against the pre-action state.
- [ ] **10.17** **The helper refuses to run unprivileged.** `python /usr/lib/grubforge/grubforge-helper regenerate` → exits non-zero with *"must run as root"*. It does not act.
- [ ] **10.18** **The helper refuses unknown verbs.** `pkexec /usr/lib/grubforge/grubforge-helper definitely-not-a-verb` → exits non-zero, *"unknown verb … refusing"*. **There must be no verb that takes a command to run.**
- [ ] **10.19** **Path traversal is refused.** Create a canary: `echo canary > /tmp/gf-canary`. Then
  `pkexec /usr/lib/grubforge/grubforge-helper backup-delete ../../../tmp/gf-canary`
  → refused with *"is not a grubForge backup name"*, **and `/tmp/gf-canary` still exists.**
- [ ] **10.20** Repeat 10.19 with `backup-restore`. Same refusal, canary intact.
- [ ] **10.21** **Only managed scripts can be touched.** `pkexec … script-enable ../../../bin/sh` and `… script-disable 00_header` are both refused by name. Only `10_linux`, `20_linux_xen`, `30_os-prober`, `30_uefi-firmware` are accepted.
- [ ] **10.22** **Shell injection into the config is refused.** Feed the helper a config body containing a bare command line (e.g. `id > /tmp/gf-pwned`) on stdin via `write-config`. It is refused at the line that is not `KEY=value`, and `/tmp/gf-pwned` is never created. *(`grub-mkconfig` sources this file as shell — accepting arbitrary text here would mean running arbitrary code as root.)*
- [ ] **10.23** **40_custom keeps its shape.** `write-custom-40` with content not starting `#!/bin/sh` is refused.
- [ ] **10.24** **Writes are atomic.** After any successful save, `/etc/default/grub` is complete and well-formed, owned `root:root`, mode `644`, with no `.grubforge-*` temporary files left behind in `/etc/default/`.

### 10.D — Behaviour under partial completion

- [ ] **10.25** Boot Entries (**5**): reorder entries, **Save & Apply**, and cancel the password dialog at the *regenerate* step (after the order was written). grubForge reports **"Order saved, but grub.cfg was not regenerated — press Ctrl+R when ready."** It does **not** claim success, and does **not** silently roll back a boot-config change.
- [ ] **10.26** Press **Ctrl+R** afterwards and authenticate. The boot menu rebuilds and reflects the saved order.
- [ ] **10.27** Boot Entries → **Restore Original** (**X**). Managed scripts are re-enabled and `40_custom` returns to Arch's stock template. Confirm `ls -l /etc/grub.d/` shows the execute bits restored and **no `.grubforge_perms` sidecars left over**.
- [ ] **10.28** The UI stays responsive while a password dialog is open — the sidebar and screen do not freeze. *(Privileged work runs off the event loop; a frozen TUI behind the dialog reads as a crash.)*

### 10.E — Degrading honestly

- [ ] **10.29** **No desktop session.** Connect over SSH (or switch to a text console) and run `grubforge`.

  The sidebar shows **no badge** — grubForge cannot tell at startup whether an authentication *agent* is running, only that polkit, the helper and the policy all exist, which they do here. Detecting agent presence is not something polkit exposes cheaply, so grubForge does not pretend to know.

  The check is that the failure is **honest when it happens**: attempt a change, and grubForge reports *"Permission was not granted, so nothing was changed… this session has no authentication agent to ask — which is normal over SSH or on a text console. There, run grubForge with sudo instead."*

  It must **not** show pkexec's raw *"Not authorized. This incident has been reported."*, which sounds like a security incident and explains nothing. And it must not print a password prompt into the terminal, which would corrupt the Textual display.
- [ ] **10.30** In that same session, `sudo grubforge` works fully, with a ROOT badge and no prompts.
- [ ] **10.31** **Running from a source checkout** (helper not installed): grubForge launches read-only and explains that the privileged helper is not installed, suggesting installing the package or using sudo.
- [ ] **10.32** `sudo python main.py` from the checkout works fully, and uses the checkout's helper rather than the installed one — so development tests the code being edited.

### 10.F — os-prober, now that grubForge no longer installs it

- [ ] **10.33** On a host **without** os-prober, Boot Entries shows a button reading **"How to install os-prober"** — not "Install os-prober".
- [ ] **10.34** Pressing it displays the install commands (`sudo pacman -S os-prober`, and `nog install os-prober` on KognogOS). **Nothing is installed.** Confirm `pacman -Q os-prober` still reports it missing.
- [ ] **10.35** On a host **with** os-prober: enable it (config write, one prompt), then Scan. Detected systems are listed. Scanning changes nothing on disk.

### 10.G — Regressions from earlier releases

- [ ] **10.36** All five screens open and render (`1`–`5`), no exceptions.
- [ ] **10.37** Backups created by **v1.0.x** still list correctly, with their original labels and timestamps, and can be restored.
- [ ] **10.38** `?` opens the help modal; `Esc` and `?` close it; `q` inside it closes without quitting the app.
- [ ] **10.39** The Dashboard sync indicator still distinguishes *in sync* / *grub.cfg older* / *pending changes*.
- [ ] **10.40** `man grubforge` renders, and its DESCRIPTION and USAGE describe the polkit model rather than `sudo grubforge`.

---

## Build-time checks

These run inside the PKGBUILD's `check()` and must pass before a package is produced:

- [ ] **10.41** Headless mount smoke test passes (`grubforge headless mount OK`).
- [ ] **10.42** Helper refusal checks pass (`grubforge helper refusal checks OK`) — the helper declines a verb while unprivileged, declines an unknown verb, and declines being run with no verb at all.
