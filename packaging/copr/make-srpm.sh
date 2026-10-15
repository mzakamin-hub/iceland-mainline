#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# packaging/copr/make-srpm.sh - the spec + sources (or the source rpm) of one of the project's packages, from this
# repository's packaging and the public upstream sources. Used by COPR's "custom" source method
# (copr-custom-script.sh) and on the PC (a local SRPM check, or an SRPM to upload with `copr-cli build`).
#   make-srpm.sh PKG --sources DIR   spec + every source file, flat in DIR (what COPR's custom method wants)
#   make-srpm.sh PKG --srpm DIR      rpmbuild -bs into DIR (needs rpmbuild)
#   PKG: kernel-iceland | iceland-device | hexagonrpc | libssc | iio-sensor-proxy | iceland-firmware
# Environment:
#   COPR_OWNER=NAME     iceland-device: the owner's Fedora account name written into its COPR repository file
#                       (the spec's %{copr_owner}); unset keeps the placeholder (the channels cannot be switched on)
#   LINUX_TARBALL=F     kernel-iceland: use this linux-<base>.tar.gz instead of downloading it from kernel.org
#   QUEUE_TARBALL=F     kernel-iceland: use this iceland-linux-<commit>.tar.gz instead of GitHub's archive
#   ART_DIR=D           iceland-device: a clone of github.com/linux-msm/audioreach-topology (else cloned)
#   FIRMWARE_DIR=D      iceland-firmware: a clone of github.com/mzakamin-hub/iceland-firmware (else cloned)
#   RPMBUILD="cmd ..."  the rpmbuild to run for --srpm (default: rpmbuild)
# Downloads use curl over https only. Nothing here needs the tablet, a token or an account.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd); top=$(cd "$here/../.." && pwd)
pkg=${1:?usage: make-srpm.sh PKG --sources DIR | --srpm DIR}; mode=${2:?--sources DIR | --srpm DIR}; out=${3:?output directory}
case "$mode" in --sources|--srpm) ;; *) echo "make-srpm: unknown mode $mode" >&2; exit 2 ;; esac
out=$(mkdir -p "$out" && cd "$out" && pwd)
work=$(mktemp -d "${TMPDIR:-/tmp}/iceland-srpm.XXXXXX"); trap 'rm -rf "$work"' EXIT
S=$work/SOURCES; mkdir -p "$S" "$work/SPECS"
fetch() { # fetch URL FILE: https only, fails on HTTP errors
	case "$1" in https://*) ;; *) echo "make-srpm: refusing non-https source $1" >&2; exit 1 ;; esac
	curl -fsSL --retry 3 --proto '=https' --proto-redir '=https' -o "$2" "$1"
}
remote_sources() { # every Source/Patch URL of SPEC that is not in SOURCES yet is downloaded (name: after '#/' or the last path part)
	local spec=$1 url name lines
	lines=$(sed -n 's/^\(Source\|Patch\)[0-9]*:[[:space:]]*//p' "$spec")
	while read -r url; do
		url=$(expand "$spec" "$url")
		case "$url" in *://*) ;; *) continue ;; esac
		case "$url" in *'#/'*) name=${url##*#/}; url=${url%%#/*} ;; *) name=${url##*/} ;; esac
		[ -e "$S/$name" ] || { echo "make-srpm: download $url"; fetch "$url" "$S/$name"; }
	done <<< "$lines"
}
expand() { # expand SPEC STRING: the spec's %global / Name / Version macros (enough for our specs' Source URLs)
	python3 - "$1" "$2" <<'PY'
import re, sys
spec, s = open(sys.argv[1], encoding="utf-8").read(), sys.argv[2]
m = {}
for k, v in re.findall(r"^%global\s+(\S+)\s+(.+?)\s*$", spec, re.M): m[k] = v
for k in ("Name", "Version"):
    r = re.search(r"^%s:\s*(\S+)" % k, spec, re.M)
    if r: m[k.lower()] = r.group(1)
r = re.search(r"^URL:\s*(\S+)", spec, re.M)
if r: m["url"] = r.group(1)
def one(v):
    v = re.sub(r"%\{(\w+)\}", lambda x: m.get(x.group(1), x.group(0)), v)
    # the specs' short-commit idiom: %(c=<hash>; echo ${c:0:N})
    return re.sub(r"%\(c=([0-9a-f]+); echo \$\{c:0:(\d+)\}\)", lambda x: x.group(1)[:int(x.group(2))], v)
for _ in range(8):
    for k in list(m): m[k] = one(m[k])
for _ in range(8): s = one(s)
if "%{" in s or "%(" in s:
    sys.exit("make-srpm: cannot expand " + s)
print(s)
PY
}
case "$pkg" in
kernel-iceland)
	d=$here/kernel-iceland; spec=$d/kernel-iceland.spec
	cp "$spec" "$work/SPECS/"; cp "$d/config-iceland" "$d/90-iceland-dtb.install" "$S/"
	base=$(sed -n 's/^%global base_tag[[:space:]]*//p' "$spec"); qc=$(sed -n 's/^%global queue_commit[[:space:]]*//p' "$spec")
	[ "$(sed -n 's/^%global queue_short[[:space:]]*//p' "$spec")" = "${qc:0:12}" ] || { echo "make-srpm: queue_short is not queue_commit's first 12" >&2; exit 1; }
	if [ -n "${LINUX_TARBALL:-}" ]; then cp "$LINUX_TARBALL" "$S/linux-$base.tar.gz"; fi
	if [ -n "${QUEUE_TARBALL:-}" ]; then cp "$QUEUE_TARBALL" "$S/iceland-linux-$qc.tar.gz"; fi
	remote_sources "$spec"
	;;
iceland-device)
	d=$top/packaging/iceland-device; spec=$d/iceland-device.spec
	for f in "$d"/files/*; do [ -f "$f" ] && cp "$f" "$S/"; done
	ART=${ART_DIR:-$work/art}
	[ -d "$ART/.git" ] || git clone -q https://github.com/linux-msm/audioreach-topology.git "$ART"
	git -C "$ART" cat-file -e 993a17d^{commit} 2>/dev/null || git -C "$ART" fetch -q origin
	git -C "$ART" archive --prefix=audioreach-topology/ --format=tar 993a17d | gzip -n > "$S/audioreach-topology-993a17d.tar.gz"
	tar -C "$top" --sort=name --owner=0 --group=0 --numeric-owner -cf - audio | gzip -n > "$S/iceland-audio.tar.gz"
	tar -C "$d/files" --sort=name --owner=0 --group=0 --numeric-owner -cf - tuned | gzip -n > "$S/iceland-tuned.tar.gz"
	if [ -n "${COPR_OWNER:-}" ] && ! grep -qx '%{!?copr_owner:%global copr_owner @COPR_OWNER@}' "$spec"; then
		echo "make-srpm: this iceland-device spec has no copr_owner line (older than 0.28-17): built as it is" >&2
		cp "$spec" "$work/SPECS/"
	elif [ -n "${COPR_OWNER:-}" ]; then
		case "$COPR_OWNER" in *[!A-Za-z0-9_.@-]*) echo "make-srpm: COPR_OWNER '$COPR_OWNER' is not an account name" >&2; exit 1 ;; esac
		sed "s|^%{!?copr_owner:%global copr_owner @COPR_OWNER@}\$|%global copr_owner $COPR_OWNER|" "$spec" > "$work/SPECS/iceland-device.spec"
	else
		cp "$spec" "$work/SPECS/"
	fi
	;;
hexagonrpc|libssc|iio-sensor-proxy)
	d=$top/packaging/sensors; spec=$d/$pkg.spec
	cp "$spec" "$work/SPECS/"
	case "$pkg" in hexagonrpc) cp "$d/hexagonrpc.sysusers" "$d/60-hexagonrpc.rules" "$S/" ;; esac
	[ -d "$top/docs/sensors/patches/$pkg" ] && cp "$top/docs/sensors/patches/$pkg"/*.patch "$S/"
	remote_sources "$spec"
	;;
iceland-firmware)
	FW=${FIRMWARE_DIR:-$work/fw}
	[ -d "$FW/.git" ] || git clone -q https://github.com/mzakamin-hub/iceland-firmware.git "$FW"
	spec=$FW/iceland-firmware.spec; cp "$spec" "$work/SPECS/"
	v=$(sed -n 's/^Version:[[:space:]]*//p' "$spec")
	git -C "$FW" archive --prefix="iceland-firmware-$v/" --format=tar HEAD | gzip -n > "$S/iceland-firmware-$v.tar.gz"
	;;
*) echo "make-srpm: unknown package $pkg" >&2; exit 2 ;;
esac
# every Source / Patch the spec names must be present now
sp=$work/SPECS/$(basename "$spec")
missing=0
while read -r url; do
	[ -n "$url" ] || continue
	url=$(expand "$sp" "$url"); case "$url" in *'#/'*) name=${url##*#/} ;; *) name=${url##*/} ;; esac
	[ -e "$S/$name" ] || { echo "make-srpm: missing source $name" >&2; missing=1; }
done < <(sed -n 's/^\(Source\|Patch\)[0-9]*:[[:space:]]*//p' "$sp")
[ "$missing" = 0 ] || exit 1
if [ "$mode" = --sources ]; then
	cp "$sp" "$S"/* "$out/"
	echo "make-srpm: $pkg spec + $(ls "$S" | wc -l) sources -> $out"
else
	${RPMBUILD:-rpmbuild} --define "_topdir $work" --define "_sourcedir $S" --define "dist .fc44" --nodeps -bs "$sp" > "$work/bs.log" 2>&1 || { tail -n 20 "$work/bs.log"; exit 1; }
	cp "$work"/SRPMS/*.src.rpm "$out/"
	echo "make-srpm: $(cd "$work/SRPMS" && ls *.src.rpm) -> $out"
fi
