"""grubForge v2.0.0 — themes (install safety, names, preview) and backups (what a restore changes).

Run: python -m unittest tests.test_v2_themes_backups -v   (PYTHONPATH=~/Programs/forgekit)
"""
from __future__ import annotations

import importlib.machinery
import importlib.util
import io
import os
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.expanduser("~/Programs/forgekit"))

from grubforge.ui.backups import differences, why_made  # noqa: E402
from grubforge.ui.themes import find_theme_root, pack_theme, preview_markup, short_name  # noqa: E402


def load_helper():
    loader = importlib.machinery.SourceFileLoader("grubforge_helper", str(ROOT / "helper" / "grubforge-helper"))
    spec = importlib.util.spec_from_loader("grubforge_helper", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def member(name: str, kind=tarfile.REGTYPE) -> tarfile.TarInfo:
    m = tarfile.TarInfo(name)
    m.type = kind
    return m


class ThemeInstallSafety(unittest.TestCase):
    """The helper runs as root: only plain files and folders, inside the theme."""

    @classmethod
    def setUpClass(cls):
        cls.h = load_helper()

    def test_plain_files_and_folders_pass(self):
        for name, kind in (("theme.txt", tarfile.REGTYPE), ("icons", tarfile.DIRTYPE), ("icons/linux.png", tarfile.REGTYPE)):
            self.assertEqual(self.h.theme_member_problem(member(name, kind)), "", name)

    def test_escapes_links_and_devices_are_refused(self):
        for name, kind in (("../../etc/passwd", tarfile.REGTYPE), ("/etc/shadow", tarfile.REGTYPE),
                           ("icons/../../x", tarfile.REGTYPE), ("link", tarfile.SYMTYPE),
                           ("hard", tarfile.LNKTYPE), ("dev", tarfile.CHRTYPE), ("fifo", tarfile.FIFOTYPE)):
            self.assertNotEqual(self.h.theme_member_problem(member(name, kind)), "", name)

    def test_theme_names(self):
        ok, bad = ("catppuccin-mocha", "Vimix_2.0", "tela"), ("../x", "a/b", "", ".hidden", "x" * 65, "a b")
        for n in ok:
            self.assertTrue(self.h.THEME_NAME_RE.match(n), n)
        for n in bad:
            self.assertFalse(self.h.THEME_NAME_RE.match(n), n)

    def test_a_link_inside_a_downloaded_theme_is_left_out_when_packing(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t) / "mytheme"
            (root / "icons").mkdir(parents=True)
            (root / "theme.txt").write_text("desktop-color: \"#000000\"\n")
            (root / "icons" / "a.png").write_bytes(b"png")
            os.symlink("/etc/passwd", root / "evil")
            data = pack_theme(root)
            names = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz").getnames()
            self.assertIn("theme.txt", names)
            self.assertIn("icons/a.png", names)
            self.assertNotIn("evil", names)

    def test_theme_root_is_found_inside_a_download(self):
        with tempfile.TemporaryDirectory() as t:
            inner = Path(t) / "grub2-themes-main" / "Vimix"
            inner.mkdir(parents=True)
            (inner / "theme.txt").write_text("")
            self.assertEqual(find_theme_root(Path(t)), inner)
            empty = Path(t) / "not-a-theme"
            empty.mkdir()
            self.assertIsNone(find_theme_root(empty))


class ThemeLooks(unittest.TestCase):
    def test_short_names(self):
        self.assertEqual(short_name("catppuccin-frappe-grub-theme"), "catppuccin-frappe")
        self.assertEqual(short_name("kognogos"), "kognogos")
        self.assertEqual(short_name("Vimix-grub"), "Vimix")

    def test_preview_uses_the_themes_colours_and_real_entries(self):
        class T:
            colors = {"desktop-color": "#101010", "item_color": "#aaaaaa", "selected_item_color": "#ffcc00"}
        m = preview_markup(T(), ["KognogOS", "Windows 11"], "5 seconds")
        self.assertIn("#101010", m)
        self.assertIn("on #ffcc00", m)
        self.assertIn("Windows 11", m)
        self.assertIn("Starting in 5 seconds", m)


class Backups(unittest.TestCase):
    def test_what_a_restore_would_change_in_plain_words(self):
        now = 'GRUB_DEFAULT=0\nGRUB_TIMEOUT=3\nGRUB_DISABLE_OS_PROBER=false\nGRUB_FOO=1\n'
        old = 'GRUB_DEFAULT=0\nGRUB_TIMEOUT=5\n#GRUB_DISABLE_OS_PROBER=false\nGRUB_FOO=2\n'
        d = differences(old, now)
        self.assertIn(("Wait before starting", "3 seconds", "5 seconds"), d)
        self.assertIn(("Find other systems", "On", "not set (off)"), d)
        self.assertIn(("GRUB_FOO", "1", "2"), d)
        self.assertEqual(len(d), 3)

    def test_identical_files_change_nothing(self):
        self.assertEqual(differences("GRUB_TIMEOUT=5\n", "GRUB_TIMEOUT=5\n"), [])

    def test_why_in_plain_words(self):
        self.assertEqual(why_made("pre-edit"), "Before a save")
        self.assertEqual(why_made("pre-theme-kognogos"), "Before using a theme (kognogos)")
        self.assertEqual(why_made("manual"), "Made by you")
        self.assertEqual(why_made("auto (pre-restore)"), "Before restoring a backup")

    def test_boot_order_copy_sits_beside_the_backup_and_goes_with_it(self):
        h = load_helper()
        p = Path("/var/lib/grubforge/backups/grub_20261002_120000_000000.bak")
        self.assertEqual(h.custom_path(p).name, "grub_20261002_120000_000000.bak.40_custom")


if __name__ == "__main__":
    unittest.main()
