#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# image/kiwi/tools/build-local-repo.sh - our packages for the kiwi build, as an rpm-md repository. Runs INSIDE a Fedora 44 aarch64
# environment (the CI's fedora:44 container on the arm64 runner; on x86 a fedora:44 aarch64 container under qemu-user).
#   build-local-repo.sh INPUT_DIR REPO_DIR
# INPUT_DIR holds what the release pages publish (names as GitHub stores them: ~ and ^ become .) plus SHA256SUMS.pins:
#   kernel-iceland-*.aarch64.rpm       binary (iceland-linux release; the kernel build is not repeated here)
#   iceland-firmware-*.noarch.rpm      binary (iceland-firmware release)
#   hexagonrpc-*.aarch64.rpm or hexagonrpc-*.src.rpm   (NOT published yet: see the report's gap list)
#   libssc-*.src.rpm, iio-sensor-proxy-*.src.rpm       (iceland-mainline release) - rebuilt here, as the B run's sensrpm step
#   iceland-device-*.src.rpm  or  iceland-pkg-*.tgz     (the release srpm, or the candidate tarball: build-rpm.sh)
# Every input file must be listed in SHA256SUMS.pins and match it (sha256sum -c --strict), else nothing is built.
# Writes only REPO_DIR (+ a scratch rpmbuild tree under /tmp). Prints one "local-repo:" line per package and the repo's list.
set -euo pipefail
IN=$(realpath "${1:?INPUT_DIR}"); REPO=$(realpath -m "${2:?REPO_DIR}")
say() { echo "local-repo: $*"; }
die() { say "FAIL $*"; exit 1; }
[ "$(uname -m)" = aarch64 ] || die "not aarch64 ($(uname -m)): run in the arm64 runner's container or under qemu-user"
[ -s "$IN/SHA256SUMS.pins" ] || die "no $IN/SHA256SUMS.pins"
( cd "$IN" && sha256sum -c --strict --quiet SHA256SUMS.pins ) || die "input checksums"
for f in "$IN"/*; do
	case "${f##*/}" in SHA256SUMS.pins) continue ;; esac
	grep -q "[ *]${f##*/}\$" "$IN/SHA256SUMS.pins" || die "${f##*/} is not pinned in SHA256SUMS.pins"
done
say "inputs: $(ls "$IN" | wc -l) files, all pinned"
dnf5 -y -q --setopt=install_weak_deps=False install rpm-build dnf5-plugins createrepo_c git-core m4 alsa-utils alsa-topology-utils \
	checkpolicy policycoreutils > /dev/null || die "build tools"
W=/tmp/iceland-localrepo; rm -rf "$W"; mkdir -p "$W" "$REPO"
one() { ls "$IN"/$1 2>/dev/null | head -n 1; }
# binaries as published
for g in 'kernel-iceland-*.aarch64.rpm' 'iceland-firmware-*.noarch.rpm'; do
	f=$(one "$g"); [ -n "$f" ] || die "missing $g"; cp "$f" "$REPO/"; say "binary ${f##*/}"
done
# hexagonrpc: binary if given, else its srpm
if f=$(one 'hexagonrpc-*.aarch64.rpm') && [ -n "$f" ]; then cp "$f" "$REPO/"; say "binary ${f##*/}"
elif f=$(one 'hexagonrpc-*.src.rpm') && [ -n "$f" ]; then
	dnf5 -y -q builddep "$f" > /dev/null || die "builddep hexagonrpc"
	rpmbuild --rebuild --define "_topdir $W/hex" --define "dist .fc44" "$f" > "$W/hex.log" 2>&1 || die "hexagonrpc build (tail: $(tail -n 3 "$W/hex.log" | tr '\n' ' '))"
	cp "$W"/hex/RPMS/aarch64/hexagonrpc-[0-9]*.aarch64.rpm "$REPO/"; say "built hexagonrpc"
else die "no hexagonrpc rpm or srpm in the inputs"; fi
# libssc (also for libssc-devel, which only the iio-sensor-proxy build needs) - the B run's sensrpm step
l=$(one 'libssc-*.src.rpm'); [ -n "$l" ] || die "missing libssc srpm"
dnf5 -y -q builddep "$l" > /dev/null || die "builddep libssc"
rpmbuild --rebuild --nocheck --define "_topdir $W/ssc" --define "dist .fc44" "$l" > "$W/ssc.log" 2>&1 || die "libssc build"
dnf5 -y -q install "$W"/ssc/RPMS/aarch64/libssc-[0-9]*.aarch64.rpm "$W"/ssc/RPMS/aarch64/libssc-devel-*.aarch64.rpm > /dev/null || die "libssc-devel install"
cp "$W"/ssc/RPMS/aarch64/libssc-[0-9]*.aarch64.rpm "$REPO/"; say "built libssc"
i=$(one 'iio-sensor-proxy-*.src.rpm'); [ -n "$i" ] || die "missing iio-sensor-proxy srpm"
dnf5 -y -q builddep "$i" > /dev/null || die "builddep iio-sensor-proxy"
rpmbuild --rebuild --define "_topdir $W/iio" --define "dist .fc44" "$i" > "$W/iio.log" 2>&1 || die "iio-sensor-proxy build"
grep -q -e 'ssc-light-filter' -e '0003-ssc-light' "$W/iio.log" || die "iio-sensor-proxy built without patch 0003 (the light filter)"
for r in "$W"/iio/RPMS/aarch64/iio-sensor-proxy-*.aarch64.rpm; do case "$r" in *debuginfo*|*debugsource*) ;; *) cp "$r" "$REPO/" ;; esac; done; say "built iio-sensor-proxy (patch 0003 applied)"
# iceland-device: the release srpm, or the candidate tarball through its own build-rpm.sh (the B run's devrpm step)
if d=$(one 'iceland-device-*.src.rpm') && [ -n "$d" ]; then
	rpmbuild --rebuild --nodeps --define "_topdir $W/dev" --define "dist .fc44" "$d" > "$W/dev.log" 2>&1 || die "iceland-device build"
	cp "$W"/dev/RPMS/noarch/iceland-device-*.noarch.rpm "$REPO/"
elif t=$(one 'iceland-pkg-*.tgz') && [ -n "$t" ]; then
	mkdir -p "$W/pkg"; tar -C "$W/pkg" -xzf "$t"
	( cd "$W/pkg" && bash packaging/iceland-device/build-rpm.sh "$W/devout" ) > "$W/dev.log" 2>&1 || die "iceland-device build-rpm.sh"
	cp "$W"/devout/iceland-device-*.noarch.rpm "$REPO/"
else die "no iceland-device srpm or iceland-pkg tarball"; fi
for r in "$REPO"/iceland-device-*.noarch.rpm; do say "built ${r##*/}"; done
createrepo_c -q "$REPO" || die "createrepo_c"
( cd "$REPO" && sha256sum *.rpm ) > "$REPO/../localrepo.sha256"
say "repository $REPO: $(ls "$REPO"/*.rpm | wc -l) packages"; sed 's/^/local-repo:   /' "$REPO/../localrepo.sha256"
