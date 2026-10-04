# grubForge v2.1.0 — Test Results (4 Oct 2026)

Part of the "nog inside the app" work; the full matrix is nogForge's
(`nogforge/testing/20261004 - Test Matrix for nogForge v1-1-0.md`, rows 1.5, 1.6, 1.12, 2.7, 2.8).

| ID | What | Result |
|---|---|---|
| 1 | Polkit spike, KognogOS VM tty3: the app answers polkit, pkexec runs as root | PASS (the PyGObject Listener route crashed; the D-Bus agent is used) |
| 2 | VM tty3, from source: Back up now → grubForge's box → wrong password → "That password didn't work" → right one | PASS — backup made as root |
| 3 | VM tty3, installed 2.1.0rc1 package: Back up now | PASS |
| 4 | Javier, desktop: a settings save (theme → catppuccin-frappe) and Back up now | PASS — grubForge's own box both times, not KDE's window (*"perfect!"*) |
| 5 | Javier, tty3 of the desktop | PASS (*"works wonders"*) |
| 6 | Tests | 53 PASS (on forgekit 0.6.0) |
| 7 | Audits | `run_worker(self.action_` 0 hits; version 2.1.0 in `__init__`, man page, README badge |

Not covered: SSH (the policy still refuses there, by design; Javier's call to keep or change).
