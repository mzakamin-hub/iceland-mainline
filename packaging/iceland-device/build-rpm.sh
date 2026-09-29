#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
#   packaging/iceland-device/build-rpm.sh OUT_DIR   -> iceland-device-*.noarch.rpm + .src.rpm
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); dest=$(realpath -m "$1")
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/SOURCES"
cp "$here"/files/* "$work/SOURCES/"
rpmbuild --define "_topdir $work" --define "dist .fc44" --nodeps -ba "$here/iceland-device.spec"
mkdir -p "$dest"; cp "$work"/RPMS/*/*.rpm "$work"/SRPMS/*.rpm "$dest/"; ls -la "$dest"
