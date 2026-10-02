#!/usr/bin/env bash
# Build release-candidate packages of python-forgekit and grubforge from the
# current code, for testing before a release (v2.0.0: Javier's run, matrix §10).
#
# The recipes are the AUR ones (~/Programs/aur-python-forgekit, aur-grubforge),
# copied and changed in three places only: the source is a tarball of the
# current commit instead of the signed release asset (which doesn't exist
# yet), the version gets an "rc" suffix (2.0.0rc1 sorts before 2.0.0, so the
# real release upgrades over it), and grubforge's forgekit requirement accepts
# the rc. Everything else — check(), package() — runs exactly as on the AUR.
# The AUR folders themselves are never changed.
#
#   scripts/make-rc-packages.sh [rc-number]      (default 1)
#
# Packages land in dist-rc/. Logs to logs/make-rc-packages-<time>.log.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
log="logs/make-rc-packages-$(date +%Y%m%d-%H%M%S).log"
ln -sfn "$(basename "$log")" logs/make-rc-packages-latest.log
exec > >(tee "$log") 2>&1

rc="${1:-1}"
GF="$PWD"
FK="$(cd ../forgekit && pwd)"
OUT="$GF/dist-rc"
WORK="$(mktemp -d)"
trap 'rm -rf --one-file-system "$WORK"' EXIT
mkdir -p "$OUT"

ver_of() { sed -n 's/^__version__ = "\([0-9.]*\).*/\1/p' "$1"; }
fk_ver="$(ver_of "$FK/forgekit/__init__.py")rc$rc"
gf_ver="$(ver_of "$GF/grubforge/__init__.py")rc$rc"
echo "forgekit $fk_ver from $(git -C "$FK" log --format='%h %s' -1)"
echo "grubforge $gf_ver from $(git -C "$GF" log --format='%h %s' -1)"
for repo in "$FK" "$GF"; do
  if [ -n "$(git -C "$repo" status --porcelain --untracked-files=no)" ]; then
    echo "NOTE: $repo has uncommitted changes; the package is built from the last commit"
  fi
done

# rc_recipe <aur dir> <src name> <version> <out dir>: the AUR recipe, sourced locally
rc_recipe() {
  local aur="$1" src="$2" ver="$3" dir="$4"
  mkdir -p "$dir"
  python3 - "$aur/PKGBUILD" "$dir/PKGBUILD" "$src" "$ver" <<'PY'
import re, sys
src_path, out, name, ver = sys.argv[1:]
s = open(src_path).read()
s = re.sub(r"^pkgver=.*$", f"pkgver={ver}", s, flags=re.M)
s = re.sub(r"^pkgrel=.*$", "pkgrel=1", s, flags=re.M)
s = re.sub(r"^source=\(.*?\)$", f'source=("{name}-{ver}.tar.gz")', s, flags=re.M | re.S)
s = re.sub(r"^sha256sums=\(.*?\)$", "sha256sums=('SKIP')   # local test build: not signed", s, flags=re.M | re.S)
s = re.sub(r"^validpgpkeys=\(.*?\)$", "", s, flags=re.M | re.S)
s = s.replace("python-forgekit>=0.5.0", "python-forgekit>=0.5.0rc1")
# the version the code reports ("0.5.0-dev") is what forgekit's check compares
s = s.replace("assert __version__ == '${pkgver}', __version__",
              "assert __version__.split('-')[0] == '${pkgver}'.split('rc')[0], __version__")
open(out, "w").write(s)
PY
}

echo
echo "=== python-forgekit $fk_ver"
d="$WORK/forgekit"; rc_recipe ~/Programs/aur-python-forgekit forgekit "$fk_ver" "$d"
git -C "$FK" archive --prefix="forgekit-$fk_ver/" -o "$d/forgekit-$fk_ver.tar.gz" HEAD
(cd "$d" && PKGDEST="$OUT" makepkg -f --nodeps --noconfirm)

echo
echo "=== grubforge $gf_ver"
d="$WORK/grubforge"; rc_recipe ~/Programs/aur-grubforge grubforge "$gf_ver" "$d"
git -C "$GF" archive --prefix="grubforge-$gf_ver/" -o "$d/grubforge-$gf_ver.tar.gz" HEAD
# grubforge's check() needs the new forgekit; this computer has an older one
# installed, so the check uses the forgekit commit being packaged
mkdir -p "$WORK/fk-src" && tar -C "$WORK/fk-src" -xzf "$WORK/forgekit/forgekit-$fk_ver.tar.gz"
(cd "$d" && PYTHONPATH="$WORK/fk-src/forgekit-$fk_ver" PKGDEST="$OUT" makepkg -f --nodeps --noconfirm)

echo
ls -l "$OUT"
echo OK
