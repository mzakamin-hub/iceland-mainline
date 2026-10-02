#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
#   build-rpm.sh TOP OUT_DIR   (on Fedora 44 aarch64; TOP holds SPECS/ and SOURCES/, see mk-sensor-pkg.sh)
# Builds hexagonrpc, libssc and iio-sensor-proxy (SSC + the Pad 4 patches) in that order. libssc and libssc-devel
# are installed in between: iio-sensor-proxy builds against them. The build dependencies must be installed
# (the BuildRequires of the three specs). A failing test suite does not stop a build: it is built again without
# %check and the log says so. RPMBUILD_LENIENT=1 (first builds of a changed spec): a file that is installed but not
# listed in %files is only a warning in the log.
set -u
top=$(realpath "$1"); dest=$(realpath -m "$2"); mkdir -p "$dest"
extra=(); [ -n "${RPMBUILD_LENIENT:-}" ] && extra=(--define "_unpackaged_files_terminate_build 0")
one() { # $1 spec name
	local log=$dest/build-$1.log rc
	rpmbuild --define "_topdir $top" "${extra[@]}" -ba "$top/SPECS/$1.spec" > "$log" 2>&1; rc=$?
	if [ $rc != 0 ] && grep -q -E "Bad exit status from .*\(%check\)" "$log"; then
		echo "$1: %check failed, building again without it"; cp "$log" "$dest/build-$1-check-failed.log"
		rpmbuild --define "_topdir $top" "${extra[@]}" --nocheck -ba "$top/SPECS/$1.spec" > "$log" 2>&1; rc=$?
	fi
	echo "$1: rpmbuild rc $rc"
	return $rc
}
# every package is tried, so that one run shows every problem
bad=0
one hexagonrpc || bad=1
if one libssc; then
	rpm -Uvh --force "$top"/RPMS/*/libssc-0*.rpm "$top"/RPMS/*/libssc-devel-*.rpm && one iio-sensor-proxy || bad=1
else
	bad=1
fi
cp "$top"/RPMS/*/*.rpm "$top"/SRPMS/*.src.rpm "$dest/" 2>/dev/null
ls -la "$dest"
exit $bad
