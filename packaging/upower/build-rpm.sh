#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
#   packaging/upower/build-rpm.sh OUT_DIR   -> upower / upower-libs / -devel ... 1.91.5-1.fc44.iceland1 RPMs + .src.rpm
# Fedora 44 aarch64 with the build dependencies of the spec (dnf builddep packaging/upower/upower.spec).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); dest=$(realpath -m "$1")
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/SOURCES"
cp "$here/upower-iceland-ttf-threshold.patch" "$work/SOURCES/"
curl -fsSL -o "$work/SOURCES/upower-v1.91.5.tar.bz2" 	https://gitlab.freedesktop.org/upower/upower/-/archive/v1.91.5/upower-v1.91.5.tar.bz2
echo "$(cat "$here/upower-v1.91.5.tar.bz2.sha256")  $work/SOURCES/upower-v1.91.5.tar.bz2" | sha256sum -c -
rpmbuild --define "_topdir $work" --define "dist .fc44" -ba "$here/upower.spec"
mkdir -p "$dest"; cp "$work"/RPMS/*/*.rpm "$work"/SRPMS/*.rpm "$dest/"; ls -la "$dest"
