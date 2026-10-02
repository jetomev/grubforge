# Look

What the menu looks like. In **Settings ▸ Look**, and on the **Themes** screen.

## Make the menu look nicer

1. Open **Themes** (press **4**). Pick one and look at the preview.
2. Choose **Use this theme**. grubForge also turns on what a theme needs: the menu drawn as **Graphics**, and a resolution.
3. **F10**, then **Save and rebuild**.

## The settings

- **Theme**: a theme sets the background, fonts and colours. See [Themes](#themes).
- **Screen resolution**: **Automatic** lets GRUB choose. Pick your screen's size (marked "this screen") for sharp text. **Other…** takes any size, or several: `1920x1080,auto`.
- **Menu drawn as**: **Graphics** allows themes and pictures; **Plain text console** is the most reliable on unusual hardware.
- **Text colours** and **Highlight colours**: used when no theme or picture is set. The sample shows how they read.
- **Background picture**: a PNG, JPG or TGA behind the menu when no theme is used.
- **Resolution after menu**: what screen mode Linux starts in. **Keep the menu's** avoids a flicker.

GRUB names: `GRUB_THEME`, `GRUB_GFXMODE`, `GRUB_TERMINAL_OUTPUT`, `GRUB_COLOR_NORMAL`, `GRUB_COLOR_HIGHLIGHT`, `GRUB_BACKGROUND`, `GRUB_GFXPAYLOAD_LINUX`.
