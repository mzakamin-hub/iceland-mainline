#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
#   packaging/iceland-device/build-rpm.sh OUT_DIR   -> iceland-device-*.noarch.rpm + .src.rpm
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); dest=$(realpath -m "$1")
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
mkdir -p "$work/SOURCES"
for f in "$here"/files/*; do [ -f "$f" ] && cp "$f" "$work/SOURCES/"; done
# sound sources: upstream audioreach-topology (pinned) + our audio/ overlay
top=$(cd "$here/../.." && pwd)
ART=${ART_DIR:-$work/art}
[ -d "$ART/.git" ] || git clone -q https://github.com/linux-msm/audioreach-topology.git "$ART"
git -C "$ART" fetch -q --depth 50 origin 993a17d 2>/dev/null || true
git -C "$ART" archive --prefix=audioreach-topology/ -o "$work/SOURCES/audioreach-topology-993a17d.tar.gz" 993a17d
tar -C "$top" -czf "$work/SOURCES/iceland-audio.tar.gz" audio
rpmbuild --define "_topdir $work" --define "dist .fc44" --nodeps -ba "$here/iceland-device.spec"
mkdir -p "$dest"; cp "$work"/RPMS/*/*.rpm "$work"/SRPMS/*.rpm "$dest/"; ls -la "$dest"
