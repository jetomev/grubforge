# Add or reorder entries

The **Boot menu** screen (press **3**) is the menu as it shows at start-up, top to bottom.

## Move an entry

1. Pick it with **↑ ↓**.
2. **Shift+↑** or **Shift+↓** slides it up or down.
3. **F10**, then **Save and rebuild**.

## Rename an entry

Pick it, press **F2**, type the new name, **Enter**.

## Add an entry

Press **+**. Choose what kind:

- **Another Linux kernel on this computer**: pick the kernel, its start-up image and options from lists. Good for a "safe graphics" entry with `nomodeset`.
- **Another operating system (EFI)**: pick its loader from the EFI partition.
- **Memory test**, **Firmware (UEFI) settings**, or **An empty entry** you write yourself.

The box at the bottom shows exactly what GRUB will read. **Edit by hand** lets you change it. Before it's added, GRUB's own checker reads it; a mistake is shown with its line.

## Your own order, and new kernels

Saving your own order writes the entries to `/etc/grub.d/40_custom` and turns off the scripts that made them, so your order stays. The cost: **those scripts no longer add new kernels by themselves.** After a kernel update, go **Back to the original order**, rebuild, and arrange again if you want.

## Entries marked "fixed"

Some entries are made by other tools (btrfs snapshots, for example). Their tool keeps placing them, so grubForge never copies them into your order and they can't be moved; that's what stops them appearing twice. If an older grubForge left such a copy in your order, the screen says so and offers **Drop the old copy**.
