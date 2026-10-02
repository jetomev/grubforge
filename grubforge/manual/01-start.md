# Getting started

grubForge changes the **boot menu**: the list you see when the computer starts, before Linux or Windows. That menu is made by a program called **GRUB**.

## The three steps for any change

1. **Change** something: a setting, the order of the menu, a theme. Nothing is written yet; the bar at the bottom counts your changes.
2. **Save** with **F10**. You see a review of every change (old → new), a backup is made, and the change is written. You're asked for your password once.
3. **Rebuild** with **F9**. GRUB makes the boot menu again from what you saved. The computer shows the new menu at the next start.

Saving and rebuilding are separate on purpose: what you save stays saved, and the bar says **"Saved · not in the boot menu yet"** until you rebuild. In the review you can also choose **Save and rebuild** to do both at once.

## Moving around

- **Tab** goes to the next field or button, **Shift+Tab** back.
- **Enter** opens a list or presses a button. **Space** flips a switch.
- **1 – 5** go to the screens: Overview, Settings, Boot menu, Themes, Backups.
- **F1** explains whatever is selected. **?** lists every key. **M** opens this manual.
- **Q** quits. If something isn't saved, or saved but not rebuilt, grubForge asks first.

## Good to know

- Every save makes a backup first. See [Backups and undo](#backups).
- If the computer ever doesn't start, see [If the computer won't start](#wont-start).
