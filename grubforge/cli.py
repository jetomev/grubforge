"""Starting grubForge from the terminal (v2.0.0).

``--version`` and ``--help`` answer and exit without opening the app (#22).
Otherwise the app runs full-screen, and when it closes the terminal gets the
record of the session: the start banner, then a closing note saying what was
saved, whether the boot menu has it, where the run was logged, and a thank-you
(Javier's start-and-end rule, carried over from nog).
"""

from __future__ import annotations

import datetime as dt
import os
import sys

from . import __version__

USAGE = f"""grubForge {__version__} — the GRUB boot menu, without editing files by hand

Usage:
  grubforge             open grubForge
  grubforge --version   print the version
  grubforge --help      print this

Inside: Tab moves, Enter opens, F10 saves, F9 rebuilds the boot menu, F1 explains,
M opens the manual, ? lists every key.
Manual: https://github.com/jetomev/grubforge/tree/main/grubforge/manual
"""

LOG_DIR = "~/.local/share/grubforge/logs"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("--version", "-V", "version"):
        print(f"grubForge {__version__}")
        return 0
    if args and args[0] in ("--help", "-h", "help"):
        print(USAGE)
        return 0
    if args:
        print(f"grubforge: unknown option {args[0]!r}\n\n{USAGE}", file=sys.stderr)
        return 2

    from forgekit import closing_notice, runs_log_row, session_banner
    from .app import GrubForgeApp

    app = GrubForgeApp()
    app.run()
    s = app.session
    ended = dt.datetime.now()
    heading, lines, level = s.summary()
    user = os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"
    logs = []
    try:
        logs.append(runs_log_row(LOG_DIR, "grubforge",
                                 [f"{s.started:%m/%d/%Y}", f"{s.started:%I:%M %p}", user, "grubforge",
                                  heading.split("·", 1)[-1].strip(), " ".join(lines)]))
    except OSError as e:
        lines = lines + [f"(This run could not be logged: {e})"]
    print(session_banner("grubForge", __version__, "grubforge", s.started, ended, user))
    print(closing_notice(heading, lines, level=level, logs=logs, thanks="Thank you for using grubForge!"))
    return 0
