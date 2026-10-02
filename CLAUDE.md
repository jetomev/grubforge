# grubForge — how this project works (L2)

GRUB bootloader manager for the terminal (Python 3.10+, Textual). Part of the Forge Suite; ships on the AUR as `grubforge`. Names: **grubForge** (lowercase g). People: Javier and Claude — never the Rullynastre persona names here.

## Run and test
- Run from the tree: `python main.py` (or `python -m grubforge`). Without `/etc/default/grub` it mounts in mock mode.
- Tests: `python tests/test_boot_entry_sources.py` (no root). The AUR `check()` also runs a headless mount (`app.run_test()`) and the helper refusal checks — run the same three before any tag.
- `cargo`-style counts: report the number of test checks in every changelog entry; a drop means something was deleted.
- A real save touches the bootloader. Test saves in a VM (`kognog-hypeforge` for Arch/KognogOS, `debian13-grubforge` for Debian — fragile boot, see memory) before this desktop.

## Privilege model (v1.1.0)
- The TUI runs as the user. Only `helper/grubforge-helper` runs as root, through `pkexec`, matched by path in `polkit/org.kognogos.grubforge.policy` → installed at `/usr/lib/grubforge/grubforge-helper`, root-owned. Never widen what the helper accepts without a test that it still refuses the rest.
- On a text console with no polkit agent: `sudo grubforge` is the documented path.

## Ship
- Release discipline: `~/.claude/rules/release.md` and `testing/RELEASE-CHECKLIST.md` (version surfaces, the worker double-wrap grep, the AUR badge cache-buster AFTER the AUR push).
- Packaging lives in `~/Programs/aur-grubforge/` (the AUR clone) — no PKGBUILD in this repo.
- Test matrices/results in `testing/`, named `YYYYMMDD - Test Matrix for grubForge vX-Y-Z.md`.
- Every push → a Vault entry in `~/Google Drive/Rullynastre/GrubForge/`.

## Design rules (binding)
- Javier's message and flow rules: memory `feedback_designed_messages` — designed notices, the same start/end framing, small actions show only what changes, nothing destructive without asking.
- v2.0.0 moves onto **forgekit** (shared shell, semantic colour roles, glyph table with ASCII fallbacks, console mode for `TERM=linux`). App-specific colours/glyphs go through forgekit's roles, never raw hex in screens.
- Known values are picked, not typed (themes, entries, kernels, resolutions, styles, booleans).
