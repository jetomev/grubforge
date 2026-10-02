#!/usr/bin/env python3
"""Make the README screenshots (v2.0.0): screenshots/v2_*.png.

Opens grubForge headless against this computer's real settings, visits each
screen, and saves an SVG; Chrome turns each into a PNG (rsvg collapses spaces,
so it is not used). Read-only: the Review picture comes from a change staged in
memory, and the window is closed with Cancel, so nothing is ever written.

    PYTHONPATH=../forgekit python scripts/make-screenshots.py
"""

import asyncio
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from grubforge.app import GrubForgeApp  # noqa: E402

SIZE = (120, 36)
OUT = ROOT / "screenshots"


async def capture(tmp: Path) -> list[Path]:
    app = GrubForgeApp()
    shots = []

    def save(name: str) -> None:
        app.save_screenshot(str(tmp / f"{name}.svg"))
        shots.append(tmp / f"{name}.svg")

    async with app.run_test(size=SIZE) as p:
        await p.pause(0.8)
        save("v2_overview")
        await p.press("2")
        await p.pause(0.6)
        save("v2_settings")
        await p.press("3")
        await p.pause(0.6)
        save("v2_boot_menu")
        await p.press("4")
        await p.pause(0.8)
        save("v2_themes")
        # the review, from a change held in memory only
        await p.press("2")
        await p.pause(0.4)
        app.query_one("#row-GRUB_TIMEOUT").control.set_value(3)
        await p.pause(0.4)
        await p.press("f10")
        await p.pause(0.8)
        save("v2_review")
        await p.press("escape")
        await p.pause(0.3)
        app.session.discard()
    return shots


def to_png(svg: Path, png: Path) -> None:
    chrome = shutil.which("google-chrome-stable") or shutil.which("chromium")
    if not chrome:
        sys.exit("needs google-chrome-stable or chromium to turn SVG into PNG")
    # the SVG's own size, so nothing is cropped
    head = svg.read_text()[:400]
    w, h = (float(x) for x in head.split('viewBox="0 0 ')[1].split('"')[0].split())
    subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={int(w)},{int(h)}", f"--screenshot={png}", svg.as_uri()],
                   check=True, capture_output=True)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as t:
        for svg in asyncio.run(capture(Path(t))):
            png = OUT / f"{svg.stem}.png"
            to_png(svg, png)
            print(png.relative_to(ROOT))
    print("OK")


if __name__ == "__main__":
    main()
