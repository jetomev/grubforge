"""grubForge 2.2.0 — the menu keys come from forgekit 0.10.0, "Boot Menu", --hypeforge,
and button labels in Javier's format.

Run: PYTHONPATH=~/Programs/forgekit python -m unittest tests.test_v220 -v
No root, no real /etc/default/grub: every session is built in a temporary folder.

Found by Javier on 2026-10-08, running grubForge inside hypeForge Settings:
  F-6 (#38)  Help had no number, and "1-5 screens" in the bottom bar was confusing
  F-7 (#39)  "Boot menu" should read "Boot Menu"
  #40        a --hypeforge start option; button labels as "Words In Title Case (k)"
"""
from __future__ import annotations

import io
import os
import re
import signal
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.expanduser("~/Programs/forgekit"))
sys.path.insert(0, str(Path(__file__).parent))

from textual.widgets import Button  # noqa: E402

from forgekit import HYPEFORGE_FLAG, HintBar, MenuDropdown, menu_key_clashes  # noqa: E402
from forgekit.menu import assign_accels  # noqa: E402

from grubforge import cli, privilege  # noqa: E402
from grubforge.app import GrubForgeApp, QuitDialog  # noqa: E402
from test_v2_settings import SAMPLE, fake_session  # noqa: E402

SECTIONS = ["overview", "settings", "boot", "themes", "backups"]
# Javier's letter rule (forgekit, 2026-10-08): the title's first letter unless taken, else its
# next free letter; Help H, Quit Q; the app's own Ctrl keys (Ctrl+R rebuild) count as taken
LETTERS = {"overview": "o", "settings": "s", "boot": "b", "themes": "t", "backups": "a",
           "help": "h", "quit": "q"}


def own_ctrl_letters() -> set[str]:
    return {b.key[5:] for b in GrubForgeApp.__dict__["BINDINGS"] if b.key.startswith("ctrl+") and len(b.key) == 6}


def writable_session():
    """Allowed to write, so every editing button shows; nothing in these tests saves."""
    s = fake_session(SAMPLE)
    s.capability = privilege.Capability(privilege.Privilege.POLKIT, "test: shown, never used")
    s.load_boot()
    return s


def watch_exit(app) -> list:
    calls: list = []
    app.exit = lambda *a, **k: calls.append(1)
    return calls


def active(app) -> list[str]:
    return [w.id for w in app.query(".menu-title.active")]


# ── F-6 (#38): every menu entry has a number and a Ctrl key, Help included ─────────────────────
class MenuKeys(unittest.IsolatedAsyncioTestCase):
    def test_every_entry_gets_a_letter(self):
        self.assertEqual(menu_key_clashes(GrubForgeApp.MENU, own_ctrl_letters()), [])

    def test_javiers_rule_gives_these_letters(self):
        self.assertEqual(assign_accels(GrubForgeApp.MENU, own_ctrl_letters()), LETTERS)
        self.assertFalse(any("acc" in m for m in GrubForgeApp.MENU), "the rule decides, not the app")

    async def test_the_running_app_underlines_those_letters(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            for entry, letter in LETTERS.items():
                markup = str(app.query_one(f"#menu-{entry}").content)
                self.assertEqual([u.lower() for u in re.findall(r"\[u\](.)\[/u\]", markup)], [letter], entry)

    def test_no_ctrl_key_of_the_app_takes_an_underlined_letter(self):
        letters = set(assign_accels(GrubForgeApp.MENU, own_ctrl_letters()).values())
        self.assertEqual(own_ctrl_letters() & letters, set(),
                         "an app Ctrl key on an underlined letter would hide that entry")

    def test_the_app_binds_no_menu_keys_of_its_own(self):
        # forgekit makes them from MENU; a second, hand-written set drifts (Help had no number)
        own = [b.key for b in GrubForgeApp.__dict__["BINDINGS"]]
        self.assertEqual([k for k in own if k.isdigit()], [], "numbers come from forgekit")
        self.assertEqual(own_ctrl_letters(), {"r"}, "only Ctrl+R (rebuild) is grubForge's own")

    async def test_numbers_reach_every_entry_help_included(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            for n, section in enumerate(SECTIONS, 1):
                app.set_focus(None)              # nothing focused: no field to type the digit into
                await pilot.press(str(n))
                await pilot.pause(0.2)
                self.assertEqual(active(app), [f"menu-{section}"], f"key {n}")
            app.set_focus(None)
            await pilot.press("6")
            await pilot.pause(0.2)
            self.assertIsInstance(app.screen, MenuDropdown, "6 opens Help")
            self.assertEqual(app.screen.menu_id, "help")
            await pilot.press("escape")
            await pilot.pause(0.2)
            app.set_focus(None)
            await pilot.press("7")
            await pilot.pause(0.2)
            self.assertEqual(len(app.screen_stack), 1, "Quit has no number")

    async def test_ctrl_letters_reach_every_entry_help_included(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            for key, section in (("ctrl+s", "settings"), ("ctrl+b", "boot"), ("ctrl+t", "themes"),
                                 ("ctrl+a", "backups"), ("ctrl+o", "overview")):
                await pilot.press(key)
                await pilot.pause(0.2)
                self.assertEqual(active(app), [f"menu-{section}"], key)
            await pilot.press("ctrl+h")
            await pilot.pause(0.2)
            self.assertEqual(getattr(app.screen, "menu_id", None), "help", "Ctrl+H opens Help")

    async def test_help_6_twice_closes_it_and_help_is_lit_while_open(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            app.set_focus(None)
            await pilot.press("6")
            await pilot.pause(0.2)
            self.assertEqual(getattr(app.screen, "menu_id", None), "help")
            self.assertTrue(app.query_one("#menu-help").has_class("open"), "Help lit while open")
            await pilot.press("6")
            await pilot.pause(0.2)
            self.assertEqual(len(app.screen_stack), 1, "6 again closes Help")
            self.assertFalse(app.query_one("#menu-help").has_class("open"))

    async def test_the_bottom_bar_says_1_6_menu(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            for key in ("1", "4"):               # Overview's own hints, then the app's
                app.set_focus(None)
                await pilot.press(key)
                await pilot.pause(0.3)
                app.set_focus(None)
                app.refresh_hints()
                text = str(app.query_one(HintBar).render())
                self.assertIn("1-6", text, key)
                self.assertIn("menu", text, key)
                self.assertNotIn("screens", text, key)
                self.assertNotIn("1-5", text, key)

    def test_no_hint_list_still_says_1_5(self):
        from grubforge.ui.bootmenu import BootMenuScreen
        from grubforge.ui.overview import OverviewScreen
        for name, hints in (("app", GrubForgeApp.HINTS), ("overview", OverviewScreen.FORGE_HINTS),
                            ("boot view", BootMenuScreen.VIEW_HINTS)):
            self.assertNotIn("1-5", [k for k, _d in hints], name)

    def test_the_keys_list(self):
        keys = dict(GrubForgeApp.SHORTCUTS)
        self.assertIn("1-6, Ctrl+letter", keys)
        self.assertIn("Help is 6", keys["1-6, Ctrl+letter"])
        self.assertFalse(any("1-5" in k for k in keys))
        self.assertTrue(any("hypeForge Settings" in d for _k, d in GrubForgeApp.SHORTCUTS),
                        "the Quit line says it isn't there inside hypeForge Settings")


# ── About and License are pages in the content area, not windows (forgekit, Javier 10-08) ──────
class AboutAndLicensePages(unittest.IsolatedAsyncioTestCase):
    async def test_pages_not_windows_and_esc_goes_back(self):
        from textual.widgets import ContentSwitcher
        for action, page in (("about", "forge-about"), ("license", "forge-license")):
            app = GrubForgeApp(session=fake_session(SAMPLE))
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.3)
                await pilot.press("ctrl+t")                      # come from Themes
                await pilot.pause(0.3)
                app.action_act(action)
                await pilot.pause(0.3)
                work = app.query_one("#forge-work", ContentSwitcher)
                self.assertEqual(len(app.screen_stack), 1, f"{action}: no window over the app")
                self.assertEqual(work.current, f"sec-{page}", action)
                self.assertEqual(active(app), ["menu-help"], f"{action}: Help lit while it shows")
                if action == "about":
                    self.assertIn("grubForge", app.export_screenshot())
                await pilot.press("escape")
                await pilot.pause(0.3)
                self.assertEqual(work.current, "sec-themes", f"{action}: Esc goes back to Themes")
                self.assertEqual(active(app), ["menu-themes"])

    async def test_from_the_help_menu(self):
        from textual.widgets import ContentSwitcher
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            app.set_focus(None)
            await pilot.press("6")
            await pilot.pause(0.2)
            await pilot.press("a")                               # About, in the Help menu
            await pilot.pause(0.3)
            self.assertEqual(app.query_one("#forge-work", ContentSwitcher).current, "sec-forge-about")
            self.assertEqual(len(app.screen_stack), 1)


# ── F-7 (#39): Boot Menu ───────────────────────────────────────────────────────────────────────
class BootMenuName(unittest.IsolatedAsyncioTestCase):
    async def test_the_tab_and_the_heading_read_boot_menu(self):
        app = GrubForgeApp(session=fake_session(SAMPLE))
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.3)
            self.assertIn("Boot Menu", str(app.query_one("#menu-boot").render()))
            await pilot.press("ctrl+b")
            await pilot.pause(0.3)
            self.assertIn("Boot Menu", app.export_screenshot().replace("&#160;", " "))
            self.assertNotIn("Boot menu", app.export_screenshot().replace("&#160;", " "))


# ── #40: inside hypeForge Settings ─────────────────────────────────────────────────────────────
class InsideHypeforge(unittest.IsolatedAsyncioTestCase):
    async def test_no_quit_and_q_does_nothing(self):
        app = GrubForgeApp(session=fake_session(SAMPLE), hypeforge=True)
        async with app.run_test(size=(120, 40)) as pilot:
            calls = watch_exit(app)
            await pilot.pause(0.3)
            self.assertEqual(len(app.query("#menu-quit")), 0, "no Quit in the bar")
            for key in ("q", "ctrl+q"):
                app.set_focus(None)
                await pilot.press(key)
                await pilot.pause(0.2)
            app.action_act("quit")
            await pilot.pause(0.2)
            self.assertEqual(calls, [], "Q, Ctrl+Q and the quit action do nothing")
            self.assertEqual(len(app.screen_stack), 1, "and ask nothing")
            self.assertEqual(app._menu_count, 6, "Help keeps its number: 1-6 inside Settings too")

    async def test_control_without_the_flag_q_quits(self):
        # the guard above is only worth something if this exit-watching sees a real quit
        app = GrubForgeApp(session=fake_session(SAMPLE), hypeforge=False)
        async with app.run_test(size=(120, 40)) as pilot:
            calls = watch_exit(app)
            await pilot.pause(0.3)
            self.assertEqual(len(app.query("#menu-quit")), 1)
            app.set_focus(None)
            await pilot.press("q")
            await pilot.pause(0.2)
            self.assertEqual(calls, [1])

    async def test_settings_closing_with_unsaved_changes_asks_grubforges_question(self):
        app = GrubForgeApp(session=fake_session(SAMPLE), hypeforge=True)
        async with app.run_test(size=(120, 40)) as pilot:
            calls = watch_exit(app)
            await pilot.pause(0.3)
            app.session.set("GRUB_TIMEOUT", "3")
            # without a listener SIGUSR1 would end the whole test run, so check that first
            self.assertNotIn(signal.getsignal(signal.SIGUSR1), (signal.SIG_DFL, None))
            os.kill(os.getpid(), signal.SIGUSR1)              # what Settings sends
            await pilot.pause(0.3)
            self.assertIsInstance(app.screen, QuitDialog, "grubForge's own question")
            self.assertEqual(calls, [], "nothing closes before the answer")
            await pilot.press("escape")                        # Stay
            await pilot.pause(0.2)
            self.assertEqual(calls, [], "Stay keeps it open")
            self.assertNotIsInstance(app.screen, QuitDialog)
            os.kill(os.getpid(), signal.SIGUSR1)               # asked again
            await pilot.pause(0.3)
            self.assertIsInstance(app.screen, QuitDialog)
            await pilot.click("#quit")                         # Quit Without Saving
            await pilot.pause(0.3)
            self.assertEqual(calls, [1], "the answer closes it")

    async def test_settings_closing_with_nothing_unfinished_closes_at_once(self):
        app = GrubForgeApp(session=fake_session(SAMPLE), hypeforge=True)
        async with app.run_test(size=(120, 40)) as pilot:
            calls = watch_exit(app)
            await pilot.pause(0.3)
            app.host_quit()
            await pilot.pause(0.2)
            self.assertEqual(calls, [1])


class CommandLine(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, list[dict], str]:
        made: list[dict] = []

        class FakeApp:
            def __init__(self, **kw):
                made.append(kw)
                self.session = fake_session(SAMPLE)

            def run(self):
                pass

        out = io.StringIO()
        with tempfile.TemporaryDirectory() as logs, \
                mock.patch("grubforge.app.GrubForgeApp", FakeApp), mock.patch.object(cli, "LOG_DIR", logs), \
                redirect_stdout(out):
            code = cli.main(argv)
        return code, made, out.getvalue()

    def test_both_spellings_start_it_inside_settings(self):
        for flag in ("--hypeforge", "--hypeForge", "--HYPEFORGE"):
            code, made, _out = self.run_main([flag])
            self.assertEqual(code, 0, flag)
            self.assertEqual(made, [{"hypeforge": True}], flag)

    def test_without_the_flag_it_is_a_normal_start(self):
        code, made, _out = self.run_main([])
        self.assertEqual((code, made), (0, [{"hypeforge": False}]))

    def test_help_and_the_man_page_do_not_mention_it(self):
        _code, made, out = self.run_main(["--help"])
        self.assertEqual(made, [], "--help doesn't open the app")
        self.assertIn("Usage", out)
        self.assertNotIn("hypeforge", out.lower())
        self.assertNotIn("hypeforge", (ROOT / "grubforge.1").read_text().lower())

    def test_other_options_still_work_beside_it(self):
        code, made, out = self.run_main(["--hypeforge", "--version"])
        self.assertEqual((code, made), (0, []))
        self.assertIn("grubForge", out)
        err = io.StringIO()
        with mock.patch("sys.stderr", err):
            self.assertEqual(cli.main(["--hypeforgex"]), 2, "only the exact word")

    def test_the_flag_is_forgekits(self):
        self.assertEqual(cli.HYPEFORGE_FLAG, HYPEFORGE_FLAG)


# ── #40: button labels in Javier's format ──────────────────────────────────────────────────────
SMALL_WORDS = {"a", "an", "the", "and", "or", "to", "of", "by", "in", "on", "for"}
KEY = r"(?:[a-z+]|F\d{1,2}|Esc|Shift\+[↑↓])"


def label_problem(label: str) -> str | None:
    """None when the label is "Words In Title Case (k)" or "Words In Title Case"."""
    m = re.fullmatch(rf"(.+?)(?: \(({KEY})\))?", label)
    words = m.group(1)
    if "  " in words or "…" in words or "(" in words:
        return "a key must be in brackets at the end, nothing else"
    for i, w in enumerate(words.split()):
        if i and w in SMALL_WORDS:
            continue
        if not w[0].isupper():
            return f"{w!r} is not in Title Case"
    return None


class ButtonLabels(unittest.IsolatedAsyncioTestCase):
    def test_the_checker_itself(self):
        for good in ("Save Changes (s)", "Rebuild Boot Menu (F9)", "Back to the Original Order",
                     "Move Up (Shift+↑)", "Cancel (Esc)", "Add an Entry (+)", "Why?"):
            self.assertIsNone(label_problem(good), good)
        for bad in ("Save…  F10", "Rebuild boot menu  F9", "Restore…  R", "Back up now",
                    "Read the boot menu (asks for your password)", "Search now"):
            self.assertIsNotNone(label_problem(bad), bad)

    def test_every_label_in_the_code(self):
        # every Button, confirm, review, quit and changes-bar label written in grubForge
        found = []
        for path in sorted((ROOT / "grubforge").rglob("*.py")):
            text = path.read_text()
            self.assertNotIn('Button(f"', text, f"{path.name}: a built label can't be checked")
            found += [(path.name, m) for m in re.findall(r'Button\("([^"]+)"', text)]
            found += [(path.name, m) for m in re.findall(r'ConfirmDialog\(\s*[^,]+,\s*"([^"]+)"', text)]
            found += [(path.name, m) for m in re.findall(r'\("([^"]+)", "[a-z-]+", (?:True|False)\)', text)]
        self.assertGreater(len(found), 40, "the search finds the labels")
        problems = [(f, lab, label_problem(lab)) for f, lab in found if label_problem(lab)]
        self.assertEqual(problems, [])

    async def test_every_button_drawn_on_every_screen(self):
        # the wait-time presets (0, 3 … forever) are values to pick, like a list's items, not actions
        from forgekit import ChangesBar, NumberPresets
        app = GrubForgeApp(session=writable_session())
        async with app.run_test(size=(120, 40)) as pilot:
            seen = {}
            for key in "12345":
                app.set_focus(None)
                await pilot.press(key)
                await pilot.pause(0.3)
                seen.update({b.id: str(b.label) for b in app.screen.query(Button)
                             if not any(isinstance(a, NumberPresets) for a in b.ancestors)})
            app.session.set("GRUB_TIMEOUT", "3")
            app.refresh_state()
            await pilot.pause(0.3)
            seen.update({b.id: str(b.label) for b in app.query_one(ChangesBar).query(Button)})
            app.session.discard()
            with mock.patch.object(type(app.session), "not_rebuilt", new_callable=mock.PropertyMock,
                                   return_value=True):
                app.refresh_state()
                await pilot.pause(0.3)
                seen.update({b.id: str(b.label) for b in app.query_one(ChangesBar).query(Button)})
            problems = {i: (lab, label_problem(lab)) for i, lab in seen.items() if label_problem(lab)}
            self.assertEqual(problems, {})
            for bid, label in KEYED.items():
                self.assertEqual(seen.get(bid), label, bid)

    def test_each_key_in_a_label_is_really_bound(self):
        from grubforge.ui.backups import BackupsScreen
        from grubforge.ui.bootmenu import BootMenuScreen
        from grubforge.ui.themes import ThemesScreen
        owners = {"gf-save": GrubForgeApp, "gf-rebuild": GrubForgeApp, "ov-rebuild": GrubForgeApp,
                  "bk-restore": BackupsScreen, "bk-new": BackupsScreen, "bk-delete": BackupsScreen,
                  "th-install": ThemesScreen, "bm-others": BootMenuScreen, "bm-add": BootMenuScreen,
                  "bm-rename": BootMenuScreen, "bm-up": BootMenuScreen, "bm-down": BootMenuScreen}
        names = {"+": "plus", "Shift+↑": "shift+up", "Shift+↓": "shift+down"}
        for bid, label in KEYED.items():
            key = label.rsplit("(", 1)[1].rstrip(")")
            key = names.get(key, key.lower())
            self.assertIn(key, [b.key for b in owners[bid].BINDINGS], f"{label!r}: {key} isn't bound")


KEYED = {
    "gf-save": "Save Changes (s)", "gf-rebuild": "Rebuild Boot Menu (F9)", "ov-rebuild": "Rebuild It Now (F9)",
    "bk-restore": "Restore (r)", "bk-new": "Back Up Now (n)", "bk-delete": "Delete (d)",
    "th-install": "Install a Theme (i)", "bm-others": "Find Other Systems (f)", "bm-add": "Add an Entry (+)",
    "bm-rename": "Rename (F2)", "bm-up": "Move Up (Shift+↑)", "bm-down": "Move Down (Shift+↓)",
}


if __name__ == "__main__":
    unittest.main()
