# grubForge release checklist

Pre-flight gates that any cut (alpha or stable) must pass before tag + GitHub release + AUR push. Captures process gaps surfaced by past test runs.

## Pre-test snapshot — preserve outside the backups dir

The §11 cleanup verification needs a survival baseline that is **immune to §8.7's destructive cleanup**. Before launching the test app:

```bash
mkdir -p /tmp/grubforge-pretest
sudo cp -p /etc/default/grub /tmp/grubforge-pretest/
sudo cp -p /etc/grub.d/40_custom /tmp/grubforge-pretest/ 2>/dev/null || true
sudo sha256sum /etc/default/grub > /tmp/grubforge-pretest/grub.sha256
```

§11 then diffs against `/tmp/grubforge-pretest/grub` rather than against a backup that the run might have wiped. (Background: M6 in the v1.0.1 test results — without this, drift on individual GRUB keys cannot be conclusively attributed.)

## Async-worker pattern audit — `@work` and `run_worker` must not double-wrap

```bash
grep -rn "@work" grubforge/
grep -rn "run_worker" grubforge/
grep -rn "run_worker(self\.action_" grubforge/   # MUST be empty
```

The third grep must return zero hits. Any `run_worker(self.action_X())` where `action_X` is `@work`-decorated will throw `WorkerError: Unsupported attempt to run an async worker` on newer Textual versions. (Background: F14 in the v1.0.1 test results — v1.0.0 shipped this bug across themes.py and backup.py; v1.0.1 only fixed themes.py until §8 caught it.)

## Version sync

Before tagging, all of these must agree on the version string:

- `grubforge/__init__.py` `__version__`
- `grubforge/app.py` `VERSION`
- `grubforge.1` `.TH` header
- `README.md` Version badge
- `~/Programs/aur-grubforge/PKGBUILD` `pkgver` + `pkgrel`
- AUR `.SRCINFO` (regenerate with `makepkg --printsrcinfo > .SRCINFO`)

> `__init__.py` is the one that gets forgotten. It was stale at 1.0.3 during
> the v1.1.0 cut and this gate is what caught it. v1.0.3 shipped after fixing
> the same class of bug in `app.py`, so it has now happened twice.

## Privilege model — the three-way path agreement (v1.1.0+)

pkexec runs **only** the exact path named in the polkit policy. If these three
disagree, authorisation fails at runtime with an error that does not obviously
point at a packaging mistake:

```bash
grep exec.path polkit/org.kognogos.grubforge.policy
grep 'INSTALLED_HELPER' grubforge/privilege.py
grep 'grubforge-helper' ~/Programs/aur-grubforge/PKGBUILD
```

All three must read `/usr/lib/grubforge/grubforge-helper`.

Also verify after installing the package:

```bash
pkaction --action-id org.kognogos.grubforge.manage --verbose
ls -l /usr/lib/grubforge/grubforge-helper     # must be root:root, not user-writable
```

A root helper writable by an unprivileged user defeats the entire model.

## Privilege model — constants duplicated in the helper

`helper/grubforge-helper` is deliberately self-contained: root-owned code must
never import from a user-writable path. The cost is duplicated constants, and
silent drift between the two copies is a **security** bug, not a cosmetic one —
the app would offer something the helper refuses, or worse, the helper would
accept something the app never intended to allow.

```bash
grep -n 'MAX_BACKUPS' grubforge/backup_manager.py helper/grubforge-helper
grep -n 'MANAGED_SCRIPTS' grubforge/boot_entries_manager.py helper/grubforge-helper
grep -n 'BACKUP_DIR\|GRUB_CONFIG_PATH\|CUSTOM_40' grubforge/*.py helper/grubforge-helper
```

The retention cap stated in the man page must match both copies.

## Doc coverage

- README and man page must list every binding in `app.py` BINDINGS + every screen `BINDINGS` (excluding `show=False` aliases)
- Universal section of help overlay (`?`) must match the universal bindings actually defined in `app.py`
- Backup retention cap mentioned in man page must match `MAX_BACKUPS` in `backup_manager.py`

## Co-author credit

Every release artifact must carry the human + AI credit:

- `~/Programs/aur-grubforge/PKGBUILD` co-developer line
- `README.md` Authors / Credits section
- GitHub release body
- Man page AUTHORS section

## Release-day flow

1. Pre-test snapshot (above)
2. Run the Test Matrix top to bottom; log findings in Test Results
3. Land HF batch closing all in-scope findings
4. Audit greps (above)
5. Version sync (above)
6. Rebuild package locally; `sudo pacman -U` reinstall
7. Re-run the regression slice from the previous Test Results' next-session handoff
8. `git tag vX.Y.Z` + `git push --tags`
9. GitHub release with notes
10. README sweep top to bottom (Description, Topics, README sections, Authors, Changelog)
11. Bump AUR PKGBUILD; `makepkg --printsrcinfo > .SRCINFO`; local `makepkg -si` smoke
12. `git push` to `ssh://aur@aur.archlinux.org/grubforge.git`
13. Verify public install path: delete local build → `yay -S grubforge` → smoke
14. Write end-of-day session log to vault with mandatory `## Next-session handoff (read this first)` section
