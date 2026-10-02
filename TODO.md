# grubForge — the list

**Current release: v1.1.3** (29 Sep 2026). **Working on: v2.0.0 — the move onto forgekit, and a full redesign of every screen** (Javier, 2 Oct 2026).

**Updated after every step.** The full story behind each item is in its GitHub issue.

## Now — v2.0.0
Javier's brief (2 Oct): *"screens done with high quality UI and easy to use structure … caring for formatting, use of colors, contrasts, and following flow of use from selecting, tabbing, buttons … leave as little to the user to write where options are known to select from … besides the help shortcuts, a manual on how to use it."*

- [x] Research (2 Oct): inventory of every screen/setting today; forgekit's API and gaps; how well-regarded TUIs do settings, pickers, apply/preview, manuals
- [ ] Design: screen-by-screen proposal published 2 Oct — https://claude.ai/artifact/EM3avQE6fn4EXYHnz9674R — **waiting on Javier's six decisions** (form vs table, one Apply, plain names, #20 fixed entries, #24 grub2 paths, closing note)
- [ ] Build on forgekit; promote shared pieces (pickers, notices) into forgekit where every app benefits
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
