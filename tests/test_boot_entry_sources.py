"""
Where boot entries come from (issue #28) — run with: python tests/test_boot_entry_sources.py

No root, no real grub.cfg: every case is built here. The save-and-reread case
runs the generated 40_custom through sh exactly as grub-mkconfig does, so the
origin lines are proven to survive the real mechanism, not a model of it.
"""

import importlib.machinery
import importlib.util
import io
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True

from grubforge import boot_entries_manager as bem  # noqa: E402
from grubforge import system                        # noqa: E402

system.system_name = lambda refresh=False: "Debian GNU/Linux"
bem.system_name = system.system_name

FAILS = []


def check(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n        got:  {got!r}\n        want: {want!r}"))
    if not ok:
        FAILS.append(name)


def section(script, body):
    return f"### BEGIN /etc/grub.d/{script} ###\n{body}\n### END /etc/grub.d/{script} ###\n"


def entry(title, body="    linux /vmlinuz"):
    return f"menuentry '{title}' --class os {{\n{body}\n}}"


# A Debian host with Windows, a second Linux, firmware settings and snapshots,
# and a password hash above the menu, as some distributions carry.
STOCK = (
    "set superusers=\"root\"\n"
    "password_pbkdf2 root grub.pbkdf2.sha512.10000.SECRETHASH\n"
    + section("10_linux", entry("Debian GNU/Linux") + "\n"
              + "submenu 'Advanced options for Debian GNU/Linux' {\n" + entry("Debian, recovery") + "\n}")
    + section("30_os-prober", entry("Windows Boot Manager (on /dev/vda1)") + "\n"
              + entry("Ubuntu 24.04.1 LTS (24.04) (on /dev/vda3)"))
    + section("30_uefi-firmware", "if [ \"$grub_platform\" = \"efi\" ]; then\n"
              + entry("UEFI Firmware Settings", "    fwsetup") + "\nfi")
    + section("40_custom", "")
    + section("41_snapshots-btrfs", entry("Debian snapshots"))
)


def sources(entries):
    return [(e.title, e.source, e.source_guessed, e.in_custom_order) for e in entries]


print("1 · reading grub.cfg's own markers")
got = {e.title: e for e in bem.parse_entries_text(STOCK)}
check("Ubuntu found by os-prober is OS Prober, not this system",
      got["Ubuntu 24.04.1 LTS (24.04) (on /dev/vda3)"].source_label, "OS Prober")
check("this system's kernel", got["Debian GNU/Linux"].source_label, "Debian GNU/Linux")
check("submenu inherits its section",
      got["Advanced options for Debian GNU/Linux"].source, "10_linux")
check("entry inside an if block", got["UEFI Firmware Settings"].source_label, "UEFI")
check("snapshots", got["Debian snapshots"].source_label, "BTRFS Snapshots")
check("nothing is marked guessed",
      [t for t, e in got.items() if e.source_guessed], [])


print("2 · save a custom order, let the shell run it, read it back")
order = bem.parse_entries_text(STOCK)
order.reverse()
custom_40 = bem.render_custom_order(order)
with tempfile.TemporaryDirectory() as d:
    script = Path(d) / "40_custom"
    script.write_text(custom_40)
    # Exactly how grub-mkconfig runs it: as a program, capturing its output.
    emitted = subprocess.run(["sh", str(script)], capture_output=True, text=True, check=True).stdout
# grubForge disables the scripts it took entries from, so only 40_custom and
# the unmanaged snapshots script still emit anything (#20 is the duplicate).
regenerated = section("40_custom", emitted.rstrip("\n")) + section("41_snapshots-btrfs", entry("Debian snapshots"))
back = bem.parse_entries_text(regenerated)
check("same entries, same order",
      [e.title for e in back[:len(order)]], [e.title for e in order])
check("every entry keeps its original source",
      [e.source for e in back[:len(order)]], [e.source for e in order])
check("all are marked as held in the custom order",
      all(e.in_custom_order for e in back[:len(order)]), True)
byt = {e.title: e for e in back[:len(order)]}
check("label after a reorder",
      byt["Ubuntu 24.04.1 LTS (24.04) (on /dev/vda3)"].source_label, "OS Prober · custom order")
check("this system after a reorder",
      byt["Debian GNU/Linux"].source_label, "Debian GNU/Linux · custom order")
check("the block reaches grub.cfg unchanged",
      byt["UEFI Firmware Settings"].raw_block, entry("UEFI Firmware Settings", "    fwsetup"))
check("save again, nothing drifts",
      bem.render_custom_order(back[:len(order)]), custom_40)


print("3 · entries grubForge did not take from elsewhere")
mine = bem.create_custom_entry("My Memtest", "Memtest")
check("an entry you created still reads Custom", mine.source_label, "Custom")
handwritten = section("40_custom", entry("Rescue USB"))
e = bem.parse_entries_text(handwritten)[0]
check("someone's own 40_custom entry is Custom, not guessed",
      (e.source_label, e.source_guessed, e.in_custom_order), ("Custom", False, False))
check("a created entry round-trips as Custom",
      bem.parse_entries_text(section("40_custom", subprocess.run(
          ["sh", "-c", "tail -n +3"], input=bem.render_custom_order([mine]),
          capture_output=True, text=True).stdout))[0].source_label, "Custom")


print("4 · an order saved by v1.1.2 or earlier (no origin lines)")
legacy_40 = bem.CUSTOM_40_HEADER + entry("Ubuntu 24.04.1 LTS (24.04) (on /dev/vda3)") + "\n" + entry("Debian GNU/Linux") + "\n"
legacy = bem.parse_entries_text(section("40_custom", "\n".join(legacy_40.splitlines()[2:])))
check("origin is guessed, and says so",
      [e.source_label for e in legacy],
      ["OS Prober (guessed) · custom order", "Debian GNU/Linux (guessed) · custom order"])
check("the guess survives the next save, still marked guessed",
      bem.render_custom_order(legacy).count("(guessed)"), 2)


print("5 · no markers at all")
bare = bem.parse_entries_text(entry("Ubuntu (on /dev/sdb2)") + "\n" + entry("Arch Linux"))
check("os-prober titles are recognised", bare[0].source, "30_os-prober")
check("and marked guessed", [e.source_guessed for e in bare], [True, True])


print("6 · a rename keeps the origin")
r = bem.rename_entry(byt["Ubuntu 24.04.1 LTS (24.04) (on /dev/vda3)"], "Ubuntu")
check("renamed entry", (r.source, r.in_custom_order), ("30_os-prober", True))


print("7 · nothing unsafe is written")
evil = bem.BootEntry(title="x", entry_type="menuentry", source="10_linux\nrm -rf /", raw_block=entry("x"))
check("a malformed source is never written", bem._origin_line(evil), "# grubforge-source: 40_custom")


print("8 · the privileged helper")
loader = importlib.machinery.SourceFileLoader("helper", str(ROOT / "helper" / "grubforge-helper"))
spec = importlib.util.spec_from_loader("helper", loader)
helper = importlib.util.module_from_spec(spec)
loader.exec_module(helper)
with tempfile.TemporaryDirectory() as d:
    cfg = Path(d) / "grub.cfg"
    cfg.write_text(STOCK + regenerated)
    helper.GRUB_CFG_PATH = cfg
    buf = io.StringIO()
    with redirect_stdout(buf):
        helper.do_read_entries()
    out = buf.getvalue()
check("the password hash never leaves", "SECRETHASH" in out or "password" in out, False)
check("the helper's view parses to the same sources as the file",
      sources(bem.parse_entries_text(out)), sources(bem.parse_entries_text(STOCK + regenerated)))
check("helper pass-through matches the parser's patterns", [
    bool(any(r.match(l) for r in helper._PASSTHROUGH_RES)) for l in (
        "### BEGIN /etc/grub.d/30_os-prober ###", "# grubforge-source: 10_linux (guessed)",
        bem.MANAGED_MARK, "### BEGIN /etc/grub.d/x ### extra", "# grubforge-source: a b",
        "password_pbkdf2 root x")],
    [True, True, True, False, False, False])


print()
if FAILS:
    print(f"*** {len(FAILS)} FAILED ***")
    sys.exit(1)
print("*** all checks passed ***")
