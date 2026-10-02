"""grubForge v2.0.0 — the boot order draft (#20) and Add an entry.

Run: python -m unittest tests.test_v2_bootmenu -v   (PYTHONPATH=~/Programs/forgekit)
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, os.path.expanduser("~/Programs/forgekit"))

from grubforge import probe  # noqa: E402
from grubforge.boot_entries_manager import parse_entries_text  # noqa: E402
from grubforge.bootorder import BootDraft  # noqa: E402

GRUB_CFG = """\
### BEGIN /etc/grub.d/10_linux ###
menuentry 'KognogOS' --class arch {
	linux /vmlinuz-linux-zen root=UUID=abc rw
}
submenu 'Advanced options for KognogOS' {
	menuentry 'KognogOS, linux-lts' {
		linux /vmlinuz-linux-lts root=UUID=abc rw
	}
}
### END /etc/grub.d/10_linux ###
### BEGIN /etc/grub.d/20_memtest86+ ###
menuentry 'Memory test (memtest86+)' {
	linux /memtest86+/memtest.efi
}
### END /etc/grub.d/20_memtest86+ ###
### BEGIN /etc/grub.d/30_os-prober ###
menuentry 'Windows 11 (on /dev/sdb2)' --class windows {
	chainloader /EFI/Microsoft/Boot/bootmgfw.efi
}
### END /etc/grub.d/30_os-prober ###
### BEGIN /etc/grub.d/30_uefi-firmware ###
menuentry 'UEFI Firmware Settings' {
	fwsetup
}
### END /etc/grub.d/30_uefi-firmware ###
### BEGIN /etc/grub.d/41_snapshots-btrfs ###
submenu 'KognogOS snapshots' {
	menuentry 'snapshot 1' {
		linux /vmlinuz-linux-zen
	}
}
### END /etc/grub.d/41_snapshots-btrfs ###
"""


def titles(d: BootDraft) -> list[str]:
    return [it.entry.title for it in d.visible()]


def reread_custom(text: str) -> list:
    """Run a 40_custom through sh as grub-mkconfig does, and parse what it prints."""
    with tempfile.NamedTemporaryFile("w", suffix="_40_custom", delete=False) as f:
        f.write(text)
        name = f.name
    try:
        out = subprocess.run(["sh", name], capture_output=True, text=True).stdout
    finally:
        os.unlink(name)
    return parse_entries_text("### BEGIN /etc/grub.d/40_custom ###\n" + out + "### END /etc/grub.d/40_custom ###\n")


class FixedEntries(unittest.TestCase):
    """#20, Javier's ruling: entries made by other tools stay where their tool puts them."""

    def setUp(self):
        self.d = BootDraft.from_entries(parse_entries_text(GRUB_CFG))

    def test_fixed_entries_sit_where_grub_puts_them(self):
        # 20_memtest86+ runs before 40_custom, 41_snapshots after it
        self.assertEqual(titles(self.d)[0], "Memory test (memtest86+)")
        self.assertEqual(titles(self.d)[-1], "KognogOS snapshots")
        self.assertFalse(self.d.items[0].movable)

    def test_fixed_entries_never_move_and_movable_ones_stop_at_them(self):
        memtest = self.d.items[0]
        self.assertFalse(self.d.move(memtest, 1))
        first_mine = self.d.items[1]
        self.assertFalse(self.d.move(first_mine, -1))     # can't jump above a fixed entry
        self.assertTrue(self.d.move(first_mine, 1))

    def test_saved_order_holds_only_movable_entries(self):
        win = next(it for it in self.d.items if it.entry.title.startswith("Windows"))
        self.d.move(win, -2)
        text = self.d.custom_40()
        self.assertNotIn("snapshot", text)
        self.assertNotIn("memtest", text)
        back = reread_custom(text)
        self.assertEqual([e.title for e in back],
                         ["Windows 11 (on /dev/sdb2)", "KognogOS", "Advanced options for KognogOS",
                          "UEFI Firmware Settings"])
        # origins survive the round trip
        self.assertEqual(back[0].source, "30_os-prober")

    def test_scripts_turned_off_are_only_grubforges_own(self):
        self.d.move(self.d.items[2], 1)
        self.assertEqual(self.d.scripts_to_turn_off(), ["10_linux", "30_os-prober", "30_uefi-firmware"])

    def test_an_old_copy_inside_the_saved_order_is_dropped(self):
        # the v1.x bug, as it sits on a real desktop: a snapshot submenu copied
        # into grubForge's 40_custom, and the live one from its own tool
        cfg = """\
### BEGIN /etc/grub.d/40_custom ###
# This file is managed by grubForge.
# grubforge-source: 10_linux
menuentry 'KognogOS' {
	linux /vmlinuz-linux-zen
}
# grubforge-source: 41_snapshots-btrfs (guessed)
submenu 'KognogOS snapshots' {
	menuentry 'snapshot 1' {
		linux /x
	}
}
### END /etc/grub.d/40_custom ###
### BEGIN /etc/grub.d/41_snapshots-btrfs ###
submenu 'KognogOS snapshots' {
	menuentry 'snapshot 1' {
		linux /x
	}
}
### END /etc/grub.d/41_snapshots-btrfs ###
"""
        d = BootDraft.from_entries(parse_entries_text(cfg))
        self.assertEqual(len(d.stale_copies), 1)
        # found, not changed: nothing is pending until it is dropped
        self.assertFalse(d.changed)
        self.assertEqual(d.changes(), [])
        d.drop_stale = True
        self.assertTrue(d.changed)
        self.assertIn(("KognogOS snapshots (old copy)", "in your saved order", "dropped"), d.changes())
        self.assertNotIn("snapshots", d.custom_40())
        self.assertIn("KognogOS", d.custom_40())

class FirmwareGuard(unittest.TestCase):
    def test_the_uefi_entry_keeps_its_guard_in_a_saved_order(self):
        d = BootDraft.from_entries(parse_entries_text(GRUB_CFG))
        text = d.custom_40()
        i = text.index("menuentry 'UEFI Firmware Settings'")
        self.assertIn('if [ "$grub_platform" = "efi" ]; then', text[:i].splitlines()[-1])
        back = reread_custom(text)
        self.assertIn("UEFI Firmware Settings", [e.title for e in back])
        # saving that order again doesn't wrap it twice
        again = BootDraft.from_entries(back).custom_40()
        self.assertEqual(again.count("grub_platform"), 1)
        self.assertEqual(probe.check_entry('menuentry \'x\' {\n echo\n}'), "")


class Draft(unittest.TestCase):
    def setUp(self):
        self.d = BootDraft.from_entries(parse_entries_text(GRUB_CFG))

    def test_untouched_is_unchanged(self):
        self.assertFalse(self.d.changed)
        self.assertEqual(self.d.changes(), [])

    def test_moves_renames_adds_and_removes_read_in_plain_words(self):
        win = next(it for it in self.d.items if it.entry.title.startswith("Windows"))
        self.d.move(win, -1)
        self.d.rename(win, "Windows")
        from grubforge.boot_entries_manager import BootEntry
        self.d.add(BootEntry("Firmware", "menuentry", "40_custom", "menuentry 'Firmware' {\n fwsetup\n}"))
        uefi = next(it for it in self.d.items if it.entry.title.startswith("UEFI"))
        self.d.remove(uefi)
        ch = self.d.changes()
        self.assertIn(("Windows 11 (on /dev/sdb2)", "name", '"Windows"'), ch)
        self.assertIn(("Windows", "3rd", "2nd"), ch)
        self.assertIn(("Firmware", "not in the menu", "added"), ch)
        self.assertIn(("UEFI Firmware Settings", "in the menu", "removed"), ch)
        self.assertNotIn("UEFI Firmware Settings", self.d.custom_40())


class AddEntry(unittest.TestCase):
    def test_built_entries_pass_grubs_own_check(self):
        for block in (probe.linux_entry("It's mine", "vmlinuz-linux", "initramfs-linux.img", "quiet"),
                      probe.chainload_entry("Windows", "ABCD-1234", "/EFI/Microsoft/Boot/bootmgfw.efi"),
                      probe.firmware_entry("UEFI Firmware Settings"),
                      probe.empty_entry("Mine")):
            self.assertEqual(probe.check_entry(block), "", block)

    def test_a_quote_in_a_title_is_kept_safe(self):
        block = probe.firmware_entry("Javier's menu")
        self.assertIn("'Javier'\\''s menu'", block)
        self.assertEqual(probe.check_entry(block), "")

    def test_broken_entries_are_refused_with_a_reason(self):
        self.assertIn("{ and }", probe.check_entry("menuentry 'x' {\n"))
        self.assertTrue(probe.check_entry("menuentry 'x' {\n if then\n}"))
        self.assertEqual(probe.check_entry("echo hi"), "an entry must start with menuentry")

    def test_install_hint_per_family(self):
        self.assertIn("nog install os-prober", probe.os_prober_install_hint("Arch"))
        self.assertIn("dnf", probe.os_prober_install_hint("Fedora"))
        self.assertIn("zypper", probe.os_prober_install_hint("openSUSE"))


if __name__ == "__main__":
    unittest.main()


class FedoraStyle(unittest.IsolatedAsyncioTestCase):
    """Found in the Fedora 44 VM: the old-copy button showed with no old copy,
    the hint line offered move/rename/add that don't work there, and GRUB's own
    entries (UEFI Firmware Settings) were missing from the list."""

    async def test_entry_files_then_fixed_entries_and_only_working_keys(self):
        from unittest import mock
        from grubforge.app import GrubForgeApp
        from grubforge.ui.bootmenu import BootMenuScreen
        from grubforge.boot_entries_manager import parse_boot_entries
        sys.path.insert(0, str(Path(__file__).parent))
        from test_v2_settings import SAMPLE, fake_session
        s = fake_session(SAMPLE)
        s.env.bls = True
        with tempfile.TemporaryDirectory() as t:
            cfg = Path(t) / "grub.cfg"
            cfg.write_text("### BEGIN /etc/grub.d/30_uefi-firmware ###\n"
                           "menuentry 'UEFI Firmware Settings' $menuentry_id_option 'uefi-firmware' {\n\tfwsetup\n}\n"
                           "### END /etc/grub.d/30_uefi-firmware ###\n")
            s.boot = BootDraft.from_entries(parse_boot_entries(cfg))
        files = [("abc-6.19", "Fedora Linux (6.19) 44", "6.19")]
        with mock.patch("grubforge.probe.bls_entries", return_value=files):
            app = GrubForgeApp(session=s)
            async with app.run_test(size=(120, 40)) as pilot:
                await pilot.pause(0.5)
                await pilot.press("3")
                await pilot.pause(0.5)
                bm = app.query_one(BootMenuScreen)
                table = bm.query_one("#bm-table")
                self.assertEqual(table.row_count, 2)
                self.assertIn("Firmware", str(table.get_row_at(1)[1]))
                self.assertFalse(bm.query_one("#bm-stale").display)
                self.assertFalse(bm.query_one("#bm-actions").display)
                self.assertIs(table.FORGE_HINTS, BootMenuScreen.VIEW_HINTS)
