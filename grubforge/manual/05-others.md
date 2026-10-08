# Find other systems

## Add Windows (or another Linux) to the menu

1. Make sure **os-prober** is installed. On KognogOS: `nog install os-prober`.
2. In **Settings ▸ Other systems**, turn **Find other systems** on. (Or: **Boot Menu ▸ Find Other Systems (f) ▸ Turn the Search On**.)
3. **F10**, then **Save and Rebuild**. The rebuild searches the disks and adds what it finds.

**Boot Menu ▸ Find Other Systems (f) ▸ Search Now** shows what a rebuild would find, without changing anything.

## Why it's off at first

GRUB turns this search off by default, because a system it finds on another disk is started without any further check. Turn it on when you have another system you want in the menu.

GRUB name: `GRUB_DISABLE_OS_PROBER` (stored backwards: "disable = false" means the search is on; grubForge shows it the right way round).
