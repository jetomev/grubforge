# grubForge — the list

**Current release: v1.1.3** (29 Sep 2026). **Working on: v2.0.0 — the move onto forgekit, and a full redesign of every screen** (Javier, 2 Oct 2026).

**Updated after every step.** The full story behind each item is in its GitHub issue.

## Now — v2.0.0
Javier's brief (2 Oct): *"screens done with high quality UI and easy to use structure … caring for formatting, use of colors, contrasts, and following flow of use from selecting, tabbing, buttons … leave as little to the user to write where options are known to select from … besides the help shortcuts, a manual on how to use it."*

- [x] Research (2 Oct): inventory of every screen/setting today; forgekit's API and gaps; how well-regarded TUIs do settings, pickers, apply/preview, manuals
- [x] Design approved (2 Oct): https://claude.ai/artifact/EM3avQE6fn4EXYHnz9674R · copy in `docs/design/v2.0.0-screens.html`. Javier's rulings:
  1. Settings as a **form** with visible controls
  2. **Save** and **Rebuild** are two buttons; saved stays saved; the bar shows "saved, not rebuilt"
  3. **Plain names**, GRUB name in the help line
  4. Entries from other tools (snapshots) **stay fixed** (#20)
  5. **All major distributions** (#24): Arch, Debian/Ubuntu, Fedora/RHEL (BLS entries!), openSUSE, Gentoo/Void; non-GRUB systems open read-only
  6. **Closing note** in the terminal; **quit warns** when something is saved but not rebuilt (or not saved)
  *"So far, it is looking very good! This pages where you do work and show me are very good to visualize before we go bananas."*
- [ ] Design still to show: the Boot menu on Fedora-style (BLS) systems
- [ ] Phase 1 · forgekit v0.5.0: hint bar, changes bar + review window, filter list, notices, progress window, manual viewer, roles (changed, info), glyphs, styles for lists/switches/checklists/radio
- [ ] Phase 2 · frame + Overview + Settings (form), Save, Rebuild, quit warning, closing note
- [ ] Phase 3 · Boot menu (+ Add an entry, Find other systems, #20 fixed entries)
- [ ] Phase 4 · Themes + Backups (40_custom backed up too)
- [ ] Phase 5 · manual, console, `--version`/`--help` (#22), distro detection (#24)
- [ ] Phase 6 · tests per screen flow; VMs per distro family (need Ubuntu, Fedora, openSUSE VMs); Javier's run; release
- [ ] In-app manual (besides the help shortcuts)
- [ ] Console mode readable (#21)
- [ ] Test matrix in VMs (KognogOS, Debian), then Javier's own run

## Open issues to fold in or decide
- [ ] #22 `grubforge --version` launches the TUI
- [ ] #19 frozen boot entries make /etc/default/grub edits inert, with no warning
- [ ] #20 saving a custom order duplicates entries from other generators (41_snapshots-btrfs)
- [ ] #24 Fedora/openSUSE/RHEL use /boot/grub2 and grub2-mkconfig
- [ ] #25 test matrix 11.A/11.B can't run on UEFI Arch
- [ ] #17 regeneration / stale-state edge cases

## Done
- v1.1.3 (29 Sep) — #28 entry sources read from grub.cfg markers; tests/ (25 checks)
- v1.1.2 (29 Sep) — #27 the distro name read from os-release
- Earlier: docs/CHANGELOG.md
