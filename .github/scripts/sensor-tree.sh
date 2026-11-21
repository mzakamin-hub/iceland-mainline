#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Lay out an rpmbuild tree for the sensor packages (used by .github/workflows/rpm.yml):
#   .github/scripts/sensor-tree.sh TOP   -> TOP/SPECS/{hexagonrpc,libssc,iio-sensor-proxy}.spec, TOP/SOURCES/*
# Sources: the upstream tarballs (spectool, pinned by the specs), our patches (docs/sensors/patches/<pkg>/),
# the extra files and patches next to the specs.
set -euo pipefail
top=$(realpath -m "$1"); repo=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$top/SPECS" "$top/SOURCES"
for p in hexagonrpc libssc iio-sensor-proxy; do
	cp "$repo/packaging/sensors/$p.spec" "$top/SPECS/"
	[ -d "$repo/docs/sensors/patches/$p" ] && cp "$repo/docs/sensors/patches/$p/"*.patch "$top/SOURCES/"
	spectool -g -C "$top/SOURCES" "$top/SPECS/$p.spec"
done
cp "$repo/packaging/sensors/hexagonrpc.sysusers" "$repo/packaging/sensors/60-hexagonrpc.rules" "$top/SOURCES/"
# patches kept next to the specs (libssc-iceland-hall.patch since libssc 2.iceland1)
for f in "$repo"/packaging/sensors/*.patch; do if [ -e "$f" ]; then cp "$f" "$top/SOURCES/"; fi; done
ls -la "$top/SOURCES"
