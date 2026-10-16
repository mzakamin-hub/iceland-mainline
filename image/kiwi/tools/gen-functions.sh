
# ---- B150g GENERIC (wf/generic, owner's decision of 15 Oct 2026): an image for every OnePlus Pad 4, no unit data in it.
# What differs from B149 (mk-b150g.py inserts these pieces; everything else is tablet-b149.sh unchanged):
#   build1a  no /etc/iceland/bdaddr; an $IN/bdaddr in the inputs is refused (the record then stops every later step)
#   sensrpm  NEW: iio-sensor-proxy 3.9-11.iceland1 built in the RAM root from its srpm (no aarch64 binary on the PC)
#   build2a  installs the sensrpm rpm with the tablet-in rpms (refused without it)
#   build2b  gen_clean (unit data out) + gen_check (one "generic:" line in check.txt; a FAIL keeps the build record, so
#            check-b150g.sh fails and the golden is not committed)
# The sensor registry stays (owner: generic, the same on every unit). In the PC / CI build iceland-firmware 11.A.38-4
# owns every firmware / sensor-tree file including sensors/registry (gen_check proves it); on a tablet B run the
# extractor's registry is counted, never a FAIL.
GEN_DEVREL=${GEN_DEVREL:-0.28-19}; GEN_IIO=${GEN_IIO:-3.9-11.iceland1}; GEN_FW=${GEN_FW:-11.A.38-5}
GEN_KREL=${GEN_KREL:-7.3.0~rc7.iceland.00453}
gen_clean() { # unit data and build residues out of the image ($MNT); prints what it removed (counts only)
	local n=0 p m
	for p in usr/lib/firmware/updates/.iceland-extracted etc/iceland/bdaddr etc/iceland/wifimac var/lib/systemd/random-seed \
		root/.bash_history root/.lesshst root/.python_history var/lib/iceland/refresh-before.tsv var/lib/iceland/refresh-fw-before.txt; do
		[ -e "$MNT/$p" ] && { rm -f "$MNT/$p"; n=$((n + 1)); }
	done
	for p in var/lib/iceland/unheld-rpms root/.ssh; do [ -e "$MNT/$p" ] && { rm -rf "${MNT:?}/$p"; n=$((n + 1)); }; done
	for p in "$MNT"/etc/NetworkManager/system-connections/* "$MNT"/var/lib/NetworkManager/*.lease "$MNT"/var/lib/NetworkManager/seen-bssids \
		"$MNT"/var/lib/NetworkManager/timestamps "$MNT"/var/log/journal/*/* "$MNT"/var/log/dnf5.log*; do
		[ -e "$p" ] && { rm -rf "$p"; n=$((n + 1)); }
	done
	# the generic-image marker (iceland-device 0.28-17's iceland-grow acts only when it exists and removes it after the
	# grow): the build id only, no unit data
	mkdir -p "$MNT/etc/iceland" && printf 'B150g generic image (Fedora Remix for OnePlus Pad 4), built %s\n' "$(date -u +%Y-%m-%d)" > "$MNT/etc/iceland/generic-image" \
		&& chmod 644 "$MNT/etc/iceland/generic-image" && n=$((n + 1))
	m=$(tr -d ' \n' < "$MNT/etc/machine-id" 2>/dev/null)
	case "$m" in ""|uninitialized) ;; *) printf 'uninitialized\n' > "$MNT/etc/machine-id"; n=$((n + 1)) ;; esac
	echo "generic clean: $n removed / reset"
}
gen_check() { # the generic image's invariants -> "PASS n" or "FAIL <what>"; never prints a unit value
	local bad="" n=0 v own unown reg oreg f
	chk() { n=$((n + 1)); [ "$1" = 0 ] || bad="$bad $2"; }
	chk "$([ -e "$MNT/etc/iceland/bdaddr" ] && echo 1 || echo 0)" bdaddr-file
	chk "$([ -e "$MNT/usr/lib/firmware/updates/.iceland-extracted" ] && echo 1 || echo 0)" extraction-record
	v=$(tr -d ' \n' < "$MNT/etc/machine-id" 2>/dev/null); case "$v" in ""|uninitialized) chk 0 x ;; *) chk 1 machine-id ;; esac
	chk "$(awk -F: '$3 >= 1000 && $3 < 60000' "$MNT/etc/passwd" 2>/dev/null | grep -c .)" users
	chk "$(ls -A "$MNT/home" 2>/dev/null | grep -c .)" homes
	chk "$(ls "$MNT"/etc/ssh/ssh_host_* 2>/dev/null | grep -c .)" ssh-host-keys
	chk "$(find "$MNT/root" "$MNT/home" -name authorized_keys 2>/dev/null | grep -c .)" authorized-keys
	chk "$(ls -A "$MNT/etc/NetworkManager/system-connections" 2>/dev/null | grep -c .)" nm-connections
	chk "$(find "$MNT/var/log/journal" -name '*.journal*' 2>/dev/null | grep -c .)" journal
	chk "$(ls -A "$MNT/var/lib/bluetooth" 2>/dev/null | grep -c -E '^([0-9A-F]{2}:){5}[0-9A-F]{2}$')" bt-pairings
	chk "$(grep -c -i -E '^[[:space:]]*(AutomaticLoginEnable|TimedLoginEnable)[[:space:]]*=[[:space:]]*(true|1)' "$MNT/etc/gdm/custom.conf" 2>/dev/null)" autologin
	chk "$(grep -c -i -E '^[[:space:]]*InitialSetupEnable[[:space:]]*=[[:space:]]*(false|0)' "$MNT/etc/gdm/custom.conf" 2>/dev/null)" wizard-off
	chk "$(rpm --root "$MNT" -q gnome-initial-setup > /dev/null 2>&1 && echo 0 || echo 1)" no-wizard-package
	chk "$(find "$MNT/var/lib/gdm" -name gnome-initial-setup-done 2>/dev/null | grep -c .)" wizard-done-stamp
	chk "$([ -e "$MNT/var/lib/systemd/random-seed" ] && echo 1 || echo 0)" random-seed
	chk "$([ -e "$MNT/var/lib/iceland/provisioned" ] && echo 1 || echo 0)" provision-stamp
	chk "$([ -x "$MNT/usr/libexec/iceland/iceland-provision" ] && [ -L "$MNT/usr/lib/systemd/system/multi-user.target.wants/iceland-provision.service" ] && echo 0 || echo 1)" provision-unit
	# the small image grows at the first boot: Fedora's repart rule + growfs in fstab + iceland-grow, nothing masked or stamped
	chk "$([ -x "$MNT/usr/libexec/iceland/iceland-grow" ] && [ -L "$MNT/usr/lib/systemd/system/multi-user.target.wants/iceland-grow.service" ] && echo 0 || echo 1)" grow-unit
	chk "$(grep -q '^Type=root' "$MNT/etc/repart.d/50-root.conf" 2>/dev/null && echo 0 || echo 1)" repart-root-rule
	chk "$(grep -c 'x-systemd.growfs' "$MNT/etc/fstab" 2>/dev/null | grep -q '^[1-9]' && echo 0 || echo 1)" fstab-growfs
	chk "$([ "$(readlink "$MNT/etc/systemd/system/systemd-repart.service" 2>/dev/null)" = /dev/null ] && echo 1 || echo 0)" repart-masked
	chk "$([ -e "$MNT/var/lib/iceland/grown" ] && echo 1 || echo 0)" grow-stamp
	chk "$(grep -q '^B150g generic image' "$MNT/etc/iceland/generic-image" 2>/dev/null && [ "$(wc -l < "$MNT/etc/iceland/generic-image")" = 1 ] && echo 0 || echo 1)" generic-image-marker
	v=$(rpm --root "$MNT" -q --qf '%{VERSION}-%{RELEASE}' iceland-device 2>/dev/null); chk "$([ "$v" = "$GEN_DEVREL.fc44" ] && echo 0 || echo 1)" "iceland-device=${v:-absent}"
	v=$(rpm --root "$MNT" -q --qf '%{VERSION}-%{RELEASE}' iio-sensor-proxy 2>/dev/null); chk "$([ "$v" = "$GEN_IIO.fc44" ] && echo 0 || echo 1)" "iio-sensor-proxy=${v:-absent}"
	v=$(rpm --root "$MNT" -q --qf '%{VERSION}-%{RELEASE}' iceland-firmware 2>/dev/null); chk "$([ "$v" = "$GEN_FW.fc44" ] && echo 0 || echo 1)" "iceland-firmware=${v:-absent}"
	v=$(rpm --root "$MNT" -q --qf '%{VERSION}\n' kernel-iceland 2>/dev/null | head -n 1); case "$v" in "$GEN_KREL".*) chk 0 x ;; *) chk 1 "kernel-iceland=${v:-absent}" ;; esac
	chk "$(rpm --root "$MNT" -V iceland-firmware 2>/dev/null | grep -c .)" iceland-firmware-modified
	# generic blobs only: every file under the firmware updates tree and the sensor hub tree belongs to a package, except
	# the sensor registry (owner: generic; counted, never a FAIL)
	own=$(mktemp); unown=$(mktemp)
	rpm --root "$MNT" -qa --qf '[%{FILENAMES}\n]' 2>/dev/null | LC_ALL=C sort -u > "$own"
	( cd "$MNT" && find usr/lib/firmware/updates usr/share/qcom/kaanapali/OnePlus/iceland -type f 2>/dev/null | sed 's|^|/|' | LC_ALL=C sort ) \
		| LC_ALL=C comm -23 - "$own" > "$unown"
	reg=$(grep -c '^/usr/share/qcom/kaanapali/OnePlus/iceland/sensors/registry/' "$unown")
	f=$(grep -v -c '^/usr/share/qcom/kaanapali/OnePlus/iceland/sensors/registry/' "$unown")
	chk "$f" "unowned-firmware-files=$f"
	rm -f "$own" "$unown"
	oreg=$(rpm --root "$MNT" -ql iceland-firmware 2>/dev/null | grep -c '^/usr/share/qcom/kaanapali/OnePlus/iceland/sensors/registry/')
	[ -z "$bad" ] && echo "PASS $n checks; sensor registry $oreg files owned by iceland-firmware, $reg unowned (generic per the owner)" || echo "FAIL$bad"
}
