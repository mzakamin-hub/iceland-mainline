#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Fetch the official Fedora aarch64 images for the OnePlus Pad 4 and verify them against Fedora's CHECKSUM files
# (sha256; the CHECKSUM file's GPG signature is checked when the Fedora key is available: gpgv + fedora.gpg).
#   phase4/fetch-fedora.sh [base|workstation|all] [OUT_DIR]     default: base, ~/mainline/build/fedora
# base        = Fedora-Container-Base-Generic (has systemd; the RAM-boot rootfs)
# workstation = Fedora-Workstation-Disk raw image (GNOME; the Phase 4 install image, needs the user's OK to write)
set -euo pipefail
what=${1:-base}; OUT=${2:-$HOME/mainline/build/fedora}; mkdir -p "$OUT"
REL=43; VER=43-1.6; M=https://dl.fedoraproject.org/pub/fedora/linux/releases/$REL
fetch() { # fetch SUBDIR FILE CHECKSUMFILE
	local sub=$1 f=$2 c=$3
	cd "$OUT"
	[ -s "$c" ] || curl -sSf -o "$c" "$M/$sub/$c"
	if [ ! -s "$f" ] || ! sha256sum -c --quiet --ignore-missing "$c" 2>/dev/null; then
		echo "downloading $f ($(curl -sI "$M/$sub/$f" | grep -i content-length | tr -dc 0-9) bytes)"
		curl -sSf -o "$f.part" -C - "$M/$sub/$f" || curl -sSf -o "$f.part" "$M/$sub/$f"
		mv "$f.part" "$f"
	fi
	grep -E "SHA256 \($f\)|^[0-9a-f]{64} +\*?$f$" "$c" > "$f.sha256" || { echo "$f not in $c"; exit 1; }
	sha256sum -c --quiet --ignore-missing "$c" && echo "verified $f: $(cut -c1-16 "$f.sha256" | tail -1)..."
	if [ -s "$OUT/fedora.gpg" ] && command -v gpgv >/dev/null; then
		gpgv --keyring "$OUT/fedora.gpg" "$c" 2>&1 | tail -1 || echo "WARNING: CHECKSUM signature not verified"
	else echo "note: CHECKSUM signature not checked (put Fedora's key at $OUT/fedora.gpg to enable it)"; fi
}
case $what in
	base|all) fetch Container/aarch64/images Fedora-Container-Base-Generic-$VER.aarch64.oci.tar.xz Fedora-Container-$VER-aarch64-CHECKSUM ;;&
	workstation|all) fetch Workstation/aarch64/images Fedora-Workstation-Disk-$VER.aarch64.raw.xz Fedora-Workstation-$VER-aarch64-CHECKSUM ;;
	base) ;;
	*) echo "usage: $0 [base|workstation|all] [OUT_DIR]"; exit 1 ;;
esac
ls -la "$OUT"
