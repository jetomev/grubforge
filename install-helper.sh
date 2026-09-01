#!/bin/sh
# grubForge — install the privileged helper on a distribution without a package.
#
# On Arch the AUR package does this. Everywhere else grubForge runs from a clone,
# and polkit will only run a helper installed system-wide at the exact path named
# in the policy file. Without both files in place grubForge stays read-only — and
# cannot read a grub.cfg that is readable only by root.
#
# Run from the top of the checkout:
#     sudo sh install-helper.sh
#
# It copies two files. It does not install grubForge itself, touch your
# bootloader, or add a package.
set -eu

HELPER_DIR=/usr/lib/grubforge
HELPER_DST="$HELPER_DIR/grubforge-helper"
POLICY_DST=/usr/share/polkit-1/actions/org.kognogos.grubforge.policy

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
HELPER_SRC="$SRC_DIR/helper/grubforge-helper"
POLICY_SRC="$SRC_DIR/polkit/org.kognogos.grubforge.policy"

if [ "$(id -u)" != 0 ]; then
    echo "This installs into /usr, so it needs root:  sudo sh install-helper.sh" >&2
    exit 1
fi

for f in "$HELPER_SRC" "$POLICY_SRC"; do
    [ -f "$f" ] || { echo "Not found: $f" >&2
                     echo "Run this from the top of the grubForge checkout." >&2; exit 1; }
done

if ! command -v pkexec >/dev/null 2>&1; then
    echo "Warning: pkexec was not found. Install your distribution's polkit package,"
    echo "         or grubForge will stay read-only even with the helper in place."
fi

# root-owned and not writable by you — a root helper an unprivileged user can
# edit is a way to run anything as root, which is the problem it exists to avoid.
install -d -m 755 -o root -g root "$HELPER_DIR"
install    -m 755 -o root -g root "$HELPER_SRC" "$HELPER_DST"
install    -m 644 -o root -g root "$POLICY_SRC" "$POLICY_DST"

echo "Installed:"
ls -l "$HELPER_DST" "$POLICY_DST"
echo
echo "Both must be owned by root and not writable by you. That is the whole point."
echo "Now run grubForge as your normal user; it asks for permission when it needs it."
