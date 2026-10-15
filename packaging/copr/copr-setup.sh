#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# packaging/copr/copr-setup.sh - the copr-cli commands that create the project's two COPR projects and their packages.
# Run by the OWNER on their own PC, with their own COPR API token in ~/.config/copr (see README.md, step 3).
# Without --run it only PRINTS the commands (check them first); nothing here reads or prints the token.
#   copr-setup.sh OWNER                 print: create OWNER/iceland-testing and OWNER/iceland, add the packages
#   copr-setup.sh OWNER --run           run those commands (copr-cli must be installed and configured)
#   copr-setup.sh OWNER --build PKG     print the command that builds PKG in iceland-testing (add --run to run it)
#   copr-setup.sh OWNER --promote       print the command that copies testing's newest builds to stable (--run runs it)
# PKG order for a first build: hexagonrpc, libssc, iio-sensor-proxy (needs libssc-devel from the project),
# iceland-device, kernel-iceland (long: about 2-4 h on a normal aarch64 builder; timeout 30 h).
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
owner=${1:?usage: copr-setup.sh OWNER [--run] | --build PKG [--run] | --promote [--run]}
case "$owner" in *[!A-Za-z0-9_.@-]*) echo "copr-setup: '$owner' is not a Fedora account name" >&2; exit 2 ;; esac
shift
action=setup; pkg=""; run=0
while [ $# -gt 0 ]; do
	case "$1" in
	--run) run=1 ;;
	--build) action=build; pkg=${2:?--build PKG}; shift ;;
	--promote) action=promote ;;
	*) echo "copr-setup: unknown argument $1" >&2; exit 2 ;;
	esac
	shift
done
PKGS="hexagonrpc libssc iio-sensor-proxy iceland-device kernel-iceland"
CHROOT=fedora-44-aarch64
DESC="Packages for mainline Linux on the OnePlus Pad 4 (iceland, Snapdragon 8 Elite Gen 5) running Fedora 44: the kernel-iceland kernel, the iceland-device settings and the sensor programs. Unofficial; not affiliated with, endorsed or supported by the Fedora Project, Red Hat or OnePlus. Sources and issues: https://github.com/mzakamin-hub/iceland-mainline"
INSTR="Only for the OnePlus Pad 4 installed with the project's image (iceland-device >= 0.28-17). Do not use 'dnf copr enable': the device package ships the repository file. On the tablet: sudo iceland-channel stable (or testing), then sudo dnf upgrade. A new kernel boots once as a trial and becomes the default only after it reached the desktop. Install guide and rollback: https://github.com/mzakamin-hub/iceland-mainline/blob/main/docs/INSTALL-GUIDE.md"
q() { printf '%q ' "$@"; echo; }
do_() { q "$@"; [ "$run" = 1 ] && "$@"; return 0; }
script_for() { # the custom-method script of one package (see copr-custom-script.sh)
	local f; f=$(mktemp "${TMPDIR:-/tmp}/copr-custom-$1.XXXXXX.sh")
	sed -e "s|@PKG@|$1|g" -e "s|@OWNER@|$owner|g" "$here/copr-custom-script.sh" > "$f"; echo "$f"
}
case "$action" in
setup)
	for p in iceland-testing iceland; do
		d=$DESC; [ "$p" = iceland-testing ] && d="TESTING channel: every new build lands here first and is promoted to $owner/iceland after a RAM rehearsal on the tablet. $DESC"
		do_ copr-cli create "$p" --chroot "$CHROOT" --description "$d" --instructions "$INSTR" \
			--enable-net off --unlisted-on-hp on --isolation default
	done
	for p in $PKGS; do
		s=$(script_for "$p")
		extra=(); [ "$p" = kernel-iceland ] && extra=(--timeout 108000)
		do_ copr-cli add-package-custom iceland-testing --name "$p" --script "$s" --script-chroot fedora-44-x86_64 \
			--script-builddeps "git-core curl tar gzip python3 rpm-build" --script-resultdir result --webhook-rebuild off "${extra[@]}"
	done
	echo "# then, one by one (each waits for the previous): $0 $owner --build hexagonrpc ... --build kernel-iceland"
	;;
build)
	case " $PKGS " in *" $pkg "*) ;; *) echo "copr-setup: unknown package $pkg ($PKGS)" >&2; exit 2 ;; esac
	extra=(); [ "$pkg" = kernel-iceland ] && extra=(--timeout 108000)
	do_ copr-cli build-package iceland-testing --name "$pkg" "${extra[@]}"
	;;
promote)
	# COPR's fork copies the newest successful build of every package into the existing stable project (re-signed
	# with stable's key; the packages' contents are not rebuilt): exactly what the rehearsal tested in testing
	do_ copr-cli fork "$owner/iceland-testing" "$owner/iceland" --confirm
	;;
esac
[ "$run" = 1 ] || echo "# (printed only; add --run to run these with your own copr-cli configuration)"
