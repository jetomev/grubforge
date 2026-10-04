# If the computer won't start

Stay calm: your files are fine. These steps work from the boot menu itself.

## The menu shows, but the system doesn't start

1. In the menu, pick **Advanced options**, then an older kernel or the **fallback** entry.
2. Once started, open grubForge, **Backups**, restore the backup from before the change, and press **F9**.

## The screen goes black after the menu

1. In the menu, highlight your system's entry and press **e**.
2. Find the line starting with `linux`. Move to its end and type a space and `nomodeset`.
3. Press **Ctrl+X** (or **F10**) to start. This change is for this start only.
4. Once started, fix the cause (often the graphics driver), or add **nomodeset** in **Settings ▸ Kernel options** until it's fixed.

## The menu doesn't show at all (it starts straight away)

Hold **Shift** (older computers) or tap **Esc** (UEFI computers) right after switching on.

## Only a text console, no desktop

Press **Ctrl+Alt+F3**, log in, and run `grubforge`. It works on the text console and asks for your password in its own box; see [On a text console](#console).

## Nothing helps

Start from a KognogOS (or any Linux) USB stick and ask for help. Your settings backups are in `/var/lib/grubforge/backups` on the installed system.
