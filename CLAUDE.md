# grubForge — how this project works (L2)

GRUB bootloader manager for the terminal (Python 3.10+, Textual). Part of the Forge Suite; ships on the AUR as `grubforge`. Names: **grubForge** (lowercase g). People: Javier and Claude — never the Rullynastre persona names here.

## Run and test
- Run from the tree: `python main.py` (or `python -m grubforge`). Without `/etc/default/grub` it mounts in mock mode.
- Tests: `python tests/test_boot_entry_sources.py` (25 checks, no root) and `PYTHONPATH=~/Programs/forge-suite/forgekit python -W always -m unittest discover -s tests` (75 tests at 2.2.0, no root, never writes /etc). The AUR `check()` also runs a headless mount (`app.run_test()`) and the helper refusal checks — run the same three before any tag.
- `cargo`-style counts: report the number of test checks in every changelog entry; a drop means something was deleted.
- A real save touches the bootloader. Test saves in a VM (`kognog-hypeforge` for Arch/KognogOS, `debian13-grubforge` for Debian — fragile boot, see memory) before this desktop.

## Privilege model (v1.1.0)
- The TUI runs as the user. Only `helper/grubforge-helper` runs as root, through `pkexec`, matched by path in `polkit/org.kognogos.grubforge.policy` → installed at `/usr/lib/grubforge/grubforge-helper`, root-owned. Never widen what the helper accepts without a test that it still refuses the rest.
- Since 2.1 grubForge is polkit's password asker for its own process (forgekit's `InAppPolkitAgent`), on a desktop and a text console alike. `sudo grubforge` is only for SSH, where the policy refuses (`allow_any=no`).

## Keys and hypeForge Settings (2.2.0)
- The menu keys come from forgekit (≥ 0.10.0), made from `MENU`: **1–6 in bar order, Help included, Quit not**, and **Ctrl + the underlined letter**. Never bind numbers or Ctrl+<underlined letter> in the app; `menu_key_clashes(MENU)` must stay `[]` and no app Ctrl key may take an underlined letter (tests in `tests/test_v220.py`). The hint bar uses `MENU_HINT` ("1-6 menu").
- `--hypeforge` (any case): how hypeForge Settings starts grubForge as one of its pages. The CLI strips it and passes `hypeforge=True`; forgekit then hides Quit and makes Q/Ctrl+Q do nothing; Settings closes the app with SIGUSR1 → `host_quit()` → grubForge's own `before_quit()` (the QuitDialog when something is unsaved or not rebuilt; its answer exits). **Not in `--help` or the man page** (it's for Settings); documented in the README ("Inside hypeForge Settings"), the manual's first page and the changelog.
- Button labels (Javier, 2026-10-03): "Words In Title Case (k)": the key in round brackets after the name; the letter key when the button has one, else the F-key (or Esc / Shift+↑ / + where that is the key); no key → just the name. Brackets always mean a key. A test checks every label in the code.

## Ship
- Release discipline: `~/.claude/rules/release.md` and `testing/RELEASE-CHECKLIST.md` (version surfaces, the worker double-wrap grep, the AUR badge cache-buster AFTER the AUR push).
- Packaging lives in `~/Programs/aur-grubforge/` (the AUR clone) — no PKGBUILD in this repo.
- Test matrices/results in `testing/`, named `YYYYMMDD - Test Matrix for grubForge vX-Y-Z.md`.
- Every push → a Vault entry in `~/Google Drive/Rullynastre/GrubForge/`.

## Design rules (binding)
- Javier's message and flow rules: memory `feedback_designed_messages` — designed notices, the same start/end framing, small actions show only what changes, nothing destructive without asking.
- v2.0.0 moves onto **forgekit** (shared shell, semantic colour roles, glyph table with ASCII fallbacks, console mode for `TERM=linux`). App-specific colours/glyphs go through forgekit's roles, never raw hex in screens.
- Known values are picked, not typed (themes, entries, kernels, resolutions, styles, booleans).
