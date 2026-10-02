# Kernel options

Extra instructions passed to Linux when it starts. In **Settings ▸ Kernel options**.

## Turn an option on or off

1. Open **Settings ▸ Kernel options**.
2. Move to the option with **↑ ↓** and press **Space** to tick or untick it.
3. **F10**, then **Save and rebuild**.

## The known options

- **quiet**: fewer messages while starting.
- **splash**: a picture instead of text while starting.
- **loglevel=3**: only serious errors are shown.
- **nomodeset**: a basic display driver. Try it if the screen goes black after the menu; take it off again once the proper driver works.
- **nowatchdog**: turns off the hang detector; saves a little power.
- **nvidia_drm.modeset=1**: needed for NVIDIA graphics on Wayland desktops.

Anything else goes in **Other options**, separated by spaces. Quotes, `;`, `$`, backticks and backslashes aren't allowed there; grubForge says so if one slips in.

**For normal starts** is what you usually want. **For every start** also reaches recovery entries; it's usually set by the installer (disks, encryption), so change it with care.

GRUB names: `GRUB_CMDLINE_LINUX_DEFAULT`, `GRUB_CMDLINE_LINUX`.
