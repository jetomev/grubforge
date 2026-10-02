# Changes made elsewhere

GRUB's files can also be changed by hand, by an installer, or by a package update. grubForge copes:

- **On every screen switch** it reads the files again; **R** does it on demand. Your unsaved changes are kept.
- **"Saved · not in the boot menu yet"** is worked out from the files' dates, so it's right even when the change was made outside grubForge.
- A kernel update normally rebuilds the menu by itself, **unless** your own boot order is in use; then go **Back to the original order** (Boot menu screen) and rebuild.
- Settings grubForge doesn't show are kept exactly as they are in the file.
