#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-2.0-or-later
# Dual boot, write W2 (docs/DUAL-BOOT.md): Fedora's own (inner) partition table for its new size, on the INSTALLED Fedora.
# Run as root from the folder that holds this script and plan/ (head-new.bin, tail-new.bin, head-old.bin, tail-old.bin,
# SHA256SUMS = gpt-plan.py shrink --trust-primary of a copy of the inner disk's first 6 / last 5 blocks). F, NI and
# P3START below are the reference layout (fedora 32,730,388 blocks, the inner disk 57,900,303, p3 from 644,352).
#   sudo bash dualboot-w2.sh --dry-run               every check, writes nothing; prints the confirm codes
#   sudo bash dualboot-w2.sh --write --confirm CODE  tail-new at block F-5, then head-new at block 0 (CODE = first 12 hex
#                                                    of sha256(head-new.bin))
#   sudo bash dualboot-w2.sh --restore --confirm CODE   head-old back at block 0 (CODE = first 12 hex of sha256(head-old.bin));
#                                                    the old backup table at the disk's old end was never touched
# Refuses (nothing written) unless: root; the installed system on the Pad 4 (not a rehearsal); the plan matches SHA256SUMS;
# Fedora's disk = a loop device of exactly 57,900,303 blocks of 4096 B over the partition labelled userdata; its current
# first 6 blocks equal head-old (write) or head-new (restore); systemd-repart is masked; and - for --write - the btrfs on
# p3 is at most the new p3 size minus 1 GiB (W1 done) and ends before block F-5.
set -u
F=32730388; NI=57900303; P3START=644352
HERE=$(cd "$(dirname "$0")" && pwd); PL=$HERE/plan
say() { echo "dualboot-w2: $*"; }
refuse() { say "REFUSED: $*"; exit 1; }
[ "$(id -u)" = 0 ] || refuse "run with sudo"
tr '\0' '\n' < /sys/firmware/devicetree/base/compatible 2>/dev/null | grep -qx 'oneplus,iceland' || refuse "not the OnePlus Pad 4"
grep -q 'iceland.rehearsal=' /proc/cmdline && refuse "a rehearsal boot: run it on the installed system"
MODE=""; CODE=""
while [ $# -gt 0 ]; do case "$1" in --dry-run) MODE=dry ;; --write) MODE=write ;; --restore) MODE=restore ;;
	--confirm) CODE=${2:-}; shift ;; *) refuse "usage: $0 --dry-run | --write --confirm CODE | --restore --confirm CODE" ;; esac; shift; done
[ -n "$MODE" ] || refuse "no mode"
(cd "$PL" && sha256sum --quiet -c SHA256SUMS) || refuse "plan/ does not match its SHA256SUMS"
c_new=$(sha256sum "$PL/head-new.bin" | cut -c1-12); c_old=$(sha256sum "$PL/head-old.bin" | cut -c1-12)
[ "$(stat -c %s "$PL/head-new.bin")" = 24576 ] && [ "$(stat -c %s "$PL/tail-new.bin")" = 20480 ] || refuse "plan file sizes"
UD=$(readlink -f /dev/disk/by-partlabel/userdata) || refuse "no userdata partition"
# the carrier attaches the loop in the initramfs, so its backing_file reads "/sda15", not "/dev/sda15" (and losetup's
# BACK-MAJ:MIN is the device node's file system, not the partition): match the backing file's base name with userdata's
# kernel name (as iceland-slot-mark does), and require offset 0 and a size equal to userdata's; exactly one loop
UDN=${UD##*/}; UDSZ=$(blockdev --getsize64 "$UD") || refuse "cannot read the size of $UD"
LOOP=""; n=0
for l in /sys/block/loop*/loop/backing_file; do
	bf=$(cat "$l" 2>/dev/null) || continue
	[ "${bf##*/}" = "$UDN" ] || continue
	x=${l%/loop/backing_file}; x=${x##*/}
	[ "$(cat "/sys/block/$x/loop/offset" 2>/dev/null)" = 0 ] || continue
	[ "$(blockdev --getsize64 "/dev/$x")" = "$UDSZ" ] || continue
	LOOP=/dev/$x; n=$((n + 1))
done
[ "$n" = 1 ] || refuse "found $n loop devices over $UD (name $UDN, offset 0, $UDSZ B); exactly one expected (is this the installed Fedora?)"
RS=$(findmnt -n -o SOURCE /); [ "${RS%%\[*}" = "${LOOP}p3" ] || refuse "/ is on $RS, not on ${LOOP}p3"
[ "$(blockdev --getss "$LOOP")" = 4096 ] || refuse "$LOOP does not have 4096-byte blocks"
[ $(( $(blockdev --getsize64 "$LOOP") / 4096 )) = $NI ] || refuse "$LOOP is not $NI blocks"
cur=$(dd if="$LOOP" bs=4096 count=6 iflag=direct status=none | sha256sum | cut -c1-64)
[ "$(systemctl is-enabled systemd-repart.service 2>/dev/null)" = masked ] || refuse "systemd-repart.service is not masked (W0b first)"
FS=$(btrfs filesystem show --raw / 2>/dev/null | awk '/devid/ {for (i=1;i<=NF;i++) if ($i=="size") print $(i+1); exit}')
LIM=$(( (F - 6 - P3START + 1) * 4096 - 1073741824 ))
say "Fedora's disk: $LOOP over $UD, $NI blocks; btrfs device size ${FS:-?} B (limit for W2: $LIM B); repart masked"
say "confirm codes: --write $c_new   --restore $c_old"
case "$MODE" in
dry)
	if [ "$cur" = "$(sha256sum < "$PL/head-old.bin" | cut -c1-64)" ]; then say "today's first 6 blocks = head-old: --write would write";
	elif [ "$cur" = "$(sha256sum < "$PL/head-new.bin" | cut -c1-64)" ]; then say "today's first 6 blocks = head-new: W2 is already done";
	else say "today's first 6 blocks match neither plan file: --write would be REFUSED"; fi
	[ -n "$FS" ] && [ "$FS" -le "$LIM" ] && say "btrfs is small enough (W1 done)" || say "btrfs is still larger than $LIM B: W1 first"
	say "DRY RUN: nothing written"; exit 0 ;;
write)
	[ "$CODE" = "$c_new" ] || refuse "wrong confirm code"
	[ "$cur" = "$(sha256sum < "$PL/head-old.bin" | cut -c1-64)" ] || refuse "today's first 6 blocks are not head-old"
	[ -n "$FS" ] && [ "$FS" -le "$LIM" ] || refuse "btrfs device size ${FS:-?} B > $LIM B: run W1 (and its scrub) first"
	sync
	dd if="$PL/tail-new.bin" of="$LOOP" bs=4096 seek=$((F - 5)) oflag=direct,sync conv=notrunc,fsync status=none || refuse "tail write failed (head untouched)"
	cmp -s "$PL/tail-new.bin" <(dd if="$LOOP" bs=4096 skip=$((F - 5)) count=5 iflag=direct status=none) || refuse "tail read-back differs (head untouched)"
	dd if="$PL/head-new.bin" of="$LOOP" bs=4096 oflag=direct,sync conv=notrunc,fsync status=none || refuse "head write failed: run --restore"
	cmp -s "$PL/head-new.bin" <(dd if="$LOOP" bs=4096 count=6 iflag=direct status=none) || refuse "head read-back differs: run --restore"
	say "W2 written and read back: tail at block $((F - 5)), head at block 0"
	sfdisk -d "$LOOP" 2>&1 | grep -E 'last-lba|p3 :' | sed 's/^/dualboot-w2:   /'
	say "PASS - reboot twice; Fedora must start normally" ;;
restore)
	[ "$CODE" = "$c_old" ] || refuse "wrong confirm code"
	[ "$cur" = "$(sha256sum < "$PL/head-new.bin" | cut -c1-64)" ] || [ "$cur" = "$(sha256sum < "$PL/head-old.bin" | cut -c1-64)" ] || refuse "today's first 6 blocks are neither plan file"
	dd if="$PL/head-old.bin" of="$LOOP" bs=4096 oflag=direct,sync conv=notrunc,fsync status=none || refuse "restore write failed"
	cmp -s "$PL/head-old.bin" <(dd if="$LOOP" bs=4096 count=6 iflag=direct status=none) && say "RESTORED: head-old back at block 0" || refuse "restore read-back differs" ;;
esac
