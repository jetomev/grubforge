"""grubForge — GRUB TUI Manager entry point."""

from grubforge.app import GrubForgeApp

if __name__ == "__main__":
    app = GrubForgeApp()
    app.run()