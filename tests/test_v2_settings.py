"""grubForge v2.0.0 — distributions, settings, the session, the screens.

Run: python -m unittest tests.test_v2_settings -v   (needs forgekit: PYTHONPATH=~/Programs/forgekit)
No root, no real /etc/default/grub: everything is built here.
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.expanduser("~/Programs/forgekit"))

from grubforge import config_manager, grubenv, privilege  # noqa: E402
from grubforge.settings_spec import (  # noqa: E402
    BY_KEY, SETTINGS, display, join_kernel, kernel_other_problem, split_kernel, switch_is_on, switch_value,
)


def make_root(tmp: str, os_release: str, files: dict[str, str]) -> Path:
    root = Path(tmp)
    (root / "etc").mkdir(parents=True, exist_ok=True)
    (root / "etc/os-release").write_text(os_release)
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


class Distributions(unittest.TestCase):
    """#24: every major family finds its own GRUB."""

    def test_arch(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, 'NAME="KognogOS"\nID=kognogos\nID_LIKE=arch\n', {"boot/grub/grub.cfg": "menuentry 'x' {}"})
            env = grubenv.detect(root, which=lambda n: "/usr/bin/" + n if n == "grub-mkconfig" else None)
            self.assertEqual((env.family, env.mkconfig, env.grub_cfg), ("Arch", "grub-mkconfig", root / "boot/grub/grub.cfg"))
            self.assertTrue(env.uses_grub)
            self.assertFalse(env.bls)

    def test_ubuntu_is_debian_family(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, 'NAME="Ubuntu"\nID=ubuntu\nID_LIKE=debian\n', {"boot/grub/grub.cfg": ""})
            env = grubenv.detect(root, which=lambda n: "/usr/sbin/" + n if n == "grub-mkconfig" else None)
            self.assertEqual(env.family, "Debian")

    def test_fedora_uses_grub2_and_bls(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, 'NAME="Fedora Linux"\nID=fedora\n', {
                "boot/grub2/grub.cfg": "insmod blscfg\nblscfg\n",
                "etc/default/grub": 'GRUB_ENABLE_BLSCFG=true\n',
                "boot/loader/entries/abc-6.10.conf": "title Fedora Linux (6.10)\n",
            })
            env = grubenv.detect(root, which=lambda n: "/usr/sbin/" + n if n == "grub2-mkconfig" else None)
            self.assertEqual((env.family, env.mkconfig), ("Fedora", "grub2-mkconfig"))
            self.assertEqual(env.grub_cfg, root / "boot/grub2/grub.cfg")
            self.assertTrue(env.bls)

    def test_opensuse_grub2_without_bls(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, 'NAME="openSUSE Tumbleweed"\nID="opensuse-tumbleweed"\nID_LIKE="opensuse suse"\n',
                             {"boot/grub2/grub.cfg": "menuentry 'openSUSE' {}"})
            env = grubenv.detect(root, which=lambda n: "/usr/sbin/" + n if n == "grub2-mkconfig" else None)
            self.assertEqual((env.family, env.mkconfig, env.bls), ("openSUSE", "grub2-mkconfig", False))

    def test_systemd_boot_is_read_only_and_says_why(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, 'NAME="Pop!_OS"\nID=pop\nID_LIKE="ubuntu debian"\n', {"boot/loader/loader.conf": "timeout 3"})
            env = grubenv.detect(root, which=lambda n: None)
            self.assertFalse(env.uses_grub)
            self.assertIn("systemd-boot", env.note)

    def test_saved_but_not_rebuilt_reads_file_times(self):
        with tempfile.TemporaryDirectory() as t:
            root = make_root(t, "ID=arch\n", {"boot/grub/grub.cfg": "", "etc/default/grub": "GRUB_TIMEOUT=5\n"})
            env = grubenv.detect(root, which=lambda n: None)
            os.utime(root / "boot/grub/grub.cfg", (1000, 1000))
            os.utime(root / "etc/default/grub", (5000, 5000))
            self.assertTrue(grubenv.saved_but_not_rebuilt(env, (root / "etc/default/grub",)))
            os.utime(root / "boot/grub/grub.cfg", (9000, 9000))
            self.assertFalse(grubenv.saved_but_not_rebuilt(env, (root / "etc/default/grub",)))


class SettingsInPlainWords(unittest.TestCase):
    def test_every_setting_has_a_group_a_label_and_help(self):
        self.assertEqual(len(SETTINGS), 17)
        for s in SETTINGS:
            self.assertTrue(s.label and s.help and s.group, s.key)
            self.assertLessEqual(len(s.label), 24, s.label)   # fits the label column

    def test_backwards_switches_read_the_right_way_round(self):
        prober = BY_KEY["GRUB_DISABLE_OS_PROBER"]
        self.assertTrue(switch_is_on(prober, "false"))     # DISABLE=false → looking
        self.assertFalse(switch_is_on(prober, "true"))
        self.assertFalse(switch_is_on(prober, None))       # GRUB's default: off
        self.assertEqual(switch_value(prober, True), "false")
        submenu = BY_KEY["GRUB_DISABLE_SUBMENU"]
        self.assertTrue(switch_is_on(submenu, None))       # GRUB's default: grouped
        self.assertFalse(switch_is_on(submenu, "y"))       # "y" counts as true

    def test_kernel_options_split_and_join(self):
        on, other = split_kernel("loglevel=3 quiet splash nvidia_drm.modeset=1 nvidia_drm.fbdev=1")
        self.assertEqual(set(on), {"loglevel=3", "quiet", "splash", "nvidia_drm.modeset=1"})
        self.assertEqual(other, "nvidia_drm.fbdev=1")
        self.assertEqual(sorted(join_kernel(on, other).split()),
                         sorted("loglevel=3 quiet splash nvidia_drm.modeset=1 nvidia_drm.fbdev=1".split()))
        self.assertEqual(kernel_other_problem('a"b'), "can't contain quotes")
        self.assertEqual(kernel_other_problem("rootfstype=btrfs"), "")

    def test_display_in_plain_words(self):
        self.assertEqual(display(BY_KEY["GRUB_TIMEOUT"], "-1"), "wait forever")
        self.assertEqual(display(BY_KEY["GRUB_TIMEOUT"], "1"), "1 second")
        self.assertEqual(display(BY_KEY["GRUB_DEFAULT"], "saved"), "Last chosen")
        self.assertEqual(display(BY_KEY["GRUB_TIMEOUT_STYLE"], "countdown"), "With a countdown")
        self.assertEqual(display(BY_KEY["GRUB_THEME"], None), "not set (none)")
        self.assertEqual(display(BY_KEY["GRUB_THEME"], "/boot/grub/themes/kognogos/theme.txt"), "kognogos")


class Writer(unittest.TestCase):
    def _config(self, text: str) -> config_manager.GrubConfig:
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "grub"
            p.write_text(text)
            return config_manager.parse_grub_config(p)

    def test_not_set_comments_the_line_out_and_appends_nothing(self):
        cfg = self._config('GRUB_TIMEOUT=5\nGRUB_THEME="/boot/grub/themes/x/theme.txt"\n')
        out = "".join(config_manager.write_grub_config(cfg, {"GRUB_THEME": None, "GRUB_GFXMODE": None}))
        self.assertIn('#GRUB_THEME="/boot/grub/themes/x/theme.txt"', out)
        self.assertNotIn("GRUB_GFXMODE", out)
        self.assertIn("GRUB_TIMEOUT=5", out)

    def test_validation_accepts_what_grub_accepts(self):
        ok = config_manager.validate_changes({"GRUB_DEFAULT": "Advanced options for Arch>Arch, linux-lts",
                                              "GRUB_GFXMODE": "1920x1080,auto", "GRUB_SAVEDEFAULT": "y"})
        self.assertTrue(ok.valid, ok.errors)
        self.assertEqual(ok.warnings, [])
        bad = config_manager.validate_changes({"GRUB_TIMEOUT": None, "GRUB_DISTRIBUTOR": 'a"b'})
        self.assertFalse(bad.valid)
        self.assertEqual(len(bad.errors), 2)


def fake_session(text: str):
    """A session over a temporary /etc/default/grub, read-only for writes."""
    from grubforge.session import Session
    tmp = tempfile.TemporaryDirectory()
    root = make_root(tmp.name, 'NAME="KognogOS"\nID=kognogos\nID_LIKE=arch\n',
                     {"boot/grub/grub.cfg": "menuentry 'KognogOS (linux-zen)' {\n}\nmenuentry 'KognogOS (linux-lts)' {\n}\n",
                      "etc/default/grub": text})
    env = grubenv.detect(root, which=lambda n: None)
    cap = privilege.Capability(privilege.Privilege.NONE, "test: no writes")
    s = Session(env=env, capability=cap, config=config_manager.parse_grub_config(root / "etc/default/grub"))
    s._read_originals()
    s._tmp = tmp
    return s


SAMPLE = ('GRUB_DEFAULT=0\nGRUB_TIMEOUT=10\nGRUB_DISTRIBUTOR="KognogOS"\n'
          'GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet splash nvidia_drm.modeset=1 nvidia_drm.fbdev=1"\n'
          'GRUB_CMDLINE_LINUX="zswap.enabled=0 rootfstype=btrfs"\nGRUB_GFXMODE=1920x1080,auto\n'
          'GRUB_DISABLE_OS_PROBER=false\n')


class SessionModel(unittest.TestCase):
    def test_setting_back_to_the_file_value_is_no_change(self):
        s = fake_session(SAMPLE)
        self.assertTrue(s.set("GRUB_TIMEOUT", "3"))
        self.assertIn("GRUB_TIMEOUT", s.pending)
        self.assertFalse(s.set("GRUB_TIMEOUT", "10"))
        self.assertEqual(s.pending, {})

    def test_review_lists_old_and_new_in_plain_words(self):
        s = fake_session(SAMPLE)
        s.set("GRUB_TIMEOUT", "-1")
        self.assertEqual(s.changes(), [("Wait before starting", "10 seconds", "wait forever")])

    def test_summary_of_a_quiet_run(self):
        s = fake_session(SAMPLE)
        heading, lines, level = s.summary()
        self.assertEqual(level, "ok")
        self.assertIn("nothing", heading.lower())


class Screens(unittest.IsolatedAsyncioTestCase):
    async def _app(self):
        from grubforge.app import GrubForgeApp
        return GrubForgeApp(session=fake_session(SAMPLE))

    async def test_nothing_is_marked_changed_at_start(self):
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.5)
            self.assertEqual(app.session.pending, {})
            self.assertFalse(app.changes_bar.display)

    async def test_a_change_shows_in_the_row_and_the_bar(self):
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.3)
            app.query_one("#row-GRUB_TIMEOUT").control.set_value(3)
            await pilot.pause(0.3)
            self.assertEqual(app.session.pending, {"GRUB_TIMEOUT": "3"})
            row = app.query_one("#row-GRUB_TIMEOUT")
            self.assertIn("changed", str(row.query_one(".forge-setting-mark").render()))
            self.assertIn("was: 10 seconds", str(row.query_one(".forge-setting-note").render()))
            self.assertTrue(app.changes_bar.display)
            self.assertIn("1 change not saved yet", str(app.query_one("#forge-changes-msg").render()))

    async def test_discard_puts_everything_back(self):
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            app.query_one("#row-GRUB_TIMEOUT").control.set_value(30)
            await pilot.pause(0.3)
            app.on_button_pressed(type("E", (), {"button": type("B", (), {"id": "gf-discard"})()})())
            await pilot.pause(0.3)
            self.assertEqual(app.session.pending, {})
            self.assertEqual(app.query_one("#row-GRUB_TIMEOUT").control.value, 10)
            self.assertFalse(app.changes_bar.display)

    async def test_quit_with_unsaved_changes_asks_first(self):
        from grubforge.app import QuitDialog
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            app.session.set("GRUB_TIMEOUT", "3")
            app.action_act("quit")
            await pilot.pause(0.3)
            self.assertIsInstance(app.screen, QuitDialog)
            self.assertTrue(app.is_running)

    async def test_long_field_values_are_visible(self):
        # the kit's horizontal scrollbar once covered a field whose value was
        # as long as the field, and the text vanished
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            app.query_one("#gf-groups").highlighted = 2
            await pilot.pause(0.5)
            self.assertIn("zswap.enabled=0", app.export_screenshot())

    async def test_read_only_says_why(self):
        app = await self._app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause(0.5)
            await pilot.press("2")
            await pilot.pause(0.3)
            self.assertIn("Read-only", str(app.query_one("#gf-readonly").render()))


if __name__ == "__main__":
    unittest.main()
