#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# w3-gpt.sh - write W3 of the dual boot (docs/DUAL-BOOT.md): the new
# LUN 0 partition table, from Linux in RAM (fastboot boot; nothing on LUN 0 mounted). Only the
# user types the write; this script never runs a write by itself.
#
#   w3-gpt.sh --dry-run                    every check and the read-back of LUN 0; writes nothing; prints what --write
#                                          / --restore would write and the confirm code each needs
#   w3-gpt.sh --write   --confirm CODE     tail-new (the backup table, last 5 blocks) then head-new (blocks 0-5)
#   w3-gpt.sh --restore --confirm CODE     tail-old then head-old (the undo: the table before W3)
# options: --dev DEV (default /dev/sda), --plan DIR (default: plan/ next to this script), --blocks N (default
#          61853696, LUN 0 of the Pad 4 in 4096-byte blocks), --log DIR (default /tmp/w3-gpt-<time>),
#          --pc-test (PC proof only: allows a device that is not the tablet's UFS LUN 0; refused on a UFS device)
# CODE = the first 12 hex digits of the sha256 of head-new.bin (--write) or head-old.bin (--restore); --dry-run
# prints both. The plan dir holds head-old.bin (6 blocks) / tail-old.bin (5 blocks) = the table before W3, cut by
# gpt-plan.py split from the copy read that day (R0.2), head-new.bin / tail-new.bin = the planned table, SHA256SUMS.
#
# Refuses (exit 1, nothing written) unless: root; the plan files match SHA256SUMS, have GPT headers whose LBAs fit
# --blocks, old != new; DEV is a whole disk with 4096-byte logical blocks and exactly --blocks blocks, the tablet's
# UFS LUN 0 (0:0:0:0 under 1d84000.ufs) unless --pc-test; nothing on it is mounted, used as swap or held (a loop
# device / dm over a partition); the battery is at 15 % or more (when the kit sees one; the floor is low because the
# write is two dd's of 6 + 5 blocks and a re-read, and the RAM boot does not charge); LUN 0's first 6 and last 5
# blocks, read with O_DIRECT, equal the table the mode starts from:
#   --write   from head-old + tail-old (or head-old + tail-new: a write stopped after its first dd), to head-new +
#             tail-new; already head-new + tail-new = nothing to write (exit 0)
#   --restore from head-new + tail-new (or a mix of old and new: a stopped write or restore) to head-old + tail-old;
#             already head-old + tail-old = nothing to write (exit 0)
#   anything else (a table that is neither the saved one nor the planned one) = REFUSED.
# Writes: dd bs=4096 oflag=direct,sync conv=notrunc,fsync, the backup blocks first, each read back (O_DIRECT) and
# compared before the next one; a mismatch stops at once (the primary table is still the one it started from).
# Then blockdev --flushbufs, BLKRRPART (blockdev --rereadpt; partx -u when the disk is busy), the final read-back of
# both ranges and the kernel's partition view (/sys/class/block start / size of every entry of the written table;
# no partition for an unused entry). A read-only whole disk (the storage seat belt) is made writable for the writes
# only and read-only again right after (also on any exit), both logged.
# Exit: 0 PASS / dry run OK / nothing to write, 1 REFUSED or FAIL, 3 written and verified on disk but the kernel's
# partition view is stale (a partition was busy: reboot before using the partitions).
set -u
MODE=""; DEV=/dev/sda; PLAN=$(dirname "$(readlink -f "$0")")/plan; N=61853696; LOGD=""; CONFIRM=""; PCTEST=0
while [ $# -gt 0 ]; do
	case "$1" in
	--dry-run|--write|--restore) [ -z "$MODE" ] || { echo "w3-gpt: one mode only"; exit 2; }; MODE=${1#--} ;;
	--dev) DEV=$2; shift ;;
	--plan) PLAN=$2; shift ;;
	--blocks) N=$2; shift ;;
	--log) LOGD=$2; shift ;;
	--confirm) CONFIRM=$2; shift ;;
	--pc-test) PCTEST=1 ;;
	*) echo "usage: w3-gpt.sh --dry-run|--write|--restore [--confirm CODE] [--dev DEV] [--plan DIR] [--blocks N] [--log DIR] [--pc-test]"; exit 2 ;;
	esac
	shift
done
[ -n "$MODE" ] || { echo "usage: w3-gpt.sh --dry-run|--write|--restore [--confirm CODE] ..."; exit 2; }
LOGD=${LOGD:-/tmp/w3-gpt-$(date +%Y%m%d-%H%M%S)-$MODE}
mkdir -p "$LOGD" || exit 1
LOG=$LOGD/w3-gpt.log
say() { echo "w3-gpt: $*" | tee -a "$LOG"; }
RESTORE_RO=""
end() { # end RESULT EXIT-CODE TEXT
	restore_ro
	say "RESULT $1 $3"
	exit "$2"
}
refuse() { end REFUSED 1 "$* - nothing written"; }
restore_ro() {
	[ -n "$RESTORE_RO" ] || return 0
	RESTORE_RO=""
	if blockdev --setro "$DEV" && [ "$(blockdev --getro "$DEV")" = 1 ]; then say "$DEV read-only again"; else say "FAIL $DEV could not be made read-only again"; fi
}
trap 'restore_ro' EXIT
trap 'say "interrupted"; restore_ro; exit 1' INT TERM HUP
say "mode $MODE, device $DEV, plan $PLAN, $N blocks of 4096 B, log $LOGD, $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
[ "$(id -u)" = 0 ] || refuse "not root"
for c in dd cmp sha256sum od blockdev readlink; do command -v "$c" > /dev/null || refuse "the kit has no $c"; done
case "$N" in ''|*[!0-9]*) refuse "--blocks $N is not a number" ;; esac
TB=$((N - 5))   # first block of the tail range: the backup entries (N-5 .. N-2) and the backup header (N-1)

# ---- 1. the plan files
for f in head-old.bin tail-old.bin head-new.bin tail-new.bin SHA256SUMS; do [ -f "$PLAN/$f" ] || refuse "$PLAN/$f is missing"; done
(cd "$PLAN" && sha256sum -c --quiet SHA256SUMS > "$LOGD/plan-sha256.txt" 2>&1) || refuse "the plan files do not match $PLAN/SHA256SUMS: $(head -n 3 "$LOGD/plan-sha256.txt" | tr '\n' ' ')"
for f in head-old.bin tail-old.bin head-new.bin tail-new.bin; do
	grep -q " $f\$" "$PLAN/SHA256SUMS" || refuse "SHA256SUMS does not list $f"
done
size() { stat -c %s "$1"; }
u64() { od -An -tu8 -j "$2" -N8 "$1" | tr -d ' '; }
u32() { od -An -tu4 -j "$2" -N4 "$1" | tr -d ' '; }
sig() { dd if="$1" bs=1 skip="$2" count=8 status=none; }
for v in old new; do
	h=$PLAN/head-$v.bin; t=$PLAN/tail-$v.bin
	[ "$(size "$h")" = 24576 ] && [ "$(size "$t")" = 20480 ] || refuse "head-$v.bin must be 24576 B and tail-$v.bin 20480 B"
	[ "$(sig "$h" 4096)" = "EFI PART" ] && [ "$(sig "$t" 16384)" = "EFI PART" ] || refuse "$v: no GPT header in block 1 of head-$v.bin or in the last block of tail-$v.bin"
	# header: my LBA at 24, alternate LBA at 32, partition entries LBA at 72
	[ "$(u64 "$h" 4120)" = 1 ] && [ "$(u64 "$h" 4128)" = $((N - 1)) ] && [ "$(u64 "$h" 4168)" = 2 ] \
		|| refuse "$v: the primary header does not describe a disk of $N blocks (my LBA $(u64 "$h" 4120), backup LBA $(u64 "$h" 4128))"
	[ "$(u64 "$t" 16408)" = $((N - 1)) ] && [ "$(u64 "$t" 16416)" = 1 ] && [ "$(u64 "$t" 16456)" = "$TB" ] \
		|| refuse "$v: the backup header does not sit at block $((N - 1)) of a disk of $N blocks"
done
cmp -s "$PLAN/head-old.bin" "$PLAN/head-new.bin" && refuse "head-old.bin = head-new.bin"
cmp -s "$PLAN/tail-old.bin" "$PLAN/tail-new.bin" && refuse "tail-old.bin = tail-new.bin"
cmp -s -n 512 "$PLAN/head-old.bin" "$PLAN/head-new.bin" || refuse "the protective MBR differs between head-old and head-new"
SH_HN=$(sha256sum < "$PLAN/head-new.bin" | cut -c1-64); SH_TN=$(sha256sum < "$PLAN/tail-new.bin" | cut -c1-64)
SH_HO=$(sha256sum < "$PLAN/head-old.bin" | cut -c1-64); SH_TO=$(sha256sum < "$PLAN/tail-old.bin" | cut -c1-64)
say "plan: head-new $SH_HN, tail-new $SH_TN, head-old $SH_HO, tail-old $SH_TO (24576 + 20480 B each pair)"

# ---- 2. the device
[ -b "$DEV" ] || refuse "$DEV is not a block device"
D=$(readlink -f "$DEV"); B=${D##*/}; S=/sys/class/block/$B
[ -e "$S" ] && [ ! -e "$S/partition" ] || refuse "$DEV ($B) is not a whole disk"
SP=$(readlink -f "$S")
if [ "$PCTEST" = 1 ]; then
	case "$SP" in */1d84000.ufs/*) refuse "--pc-test on the tablet's UFS storage" ;; esac
	say "PC TEST device $B ($SP)"
else
	case "$SP" in */1d84000.ufs/*/0:0:0:0/block/"$B") say "device $B = UFS LUN 0 ($SP)" ;; *) refuse "$DEV is not the tablet's UFS LUN 0 ($SP)" ;; esac
fi
ss=$(blockdev --getss "$DEV"); sz=$(blockdev --getsize64 "$DEV")
[ "$ss" = 4096 ] || refuse "$DEV has $ss-byte logical blocks, not 4096"
[ "$sz" = $((N * 4096)) ] || refuse "$DEV has $sz B = $((sz / 4096)) blocks, not $N"
case "$B" in *[0-9]) PP=${B}p ;; *) PP=$B ;; esac   # partition names: sda15, loop3p15
busy=""
for p in "$S" "$S"/"$B"*; do
	[ -e "$p/dev" ] || continue
	n=${p##*/}
	grep -q "^/dev/$n " /proc/mounts && busy="$busy $n:mounted"
	grep -q "^/dev/$n " /proc/swaps 2>/dev/null && busy="$busy $n:swap"
	for h in "$p"/holders/*; do [ -e "$h" ] && busy="$busy $n:held-by-${h##*/}"; done
done
for l in /sys/block/loop*/loop/backing_file; do
	[ -e "$l" ] || continue
	case "$(cat "$l")" in /dev/"$B"|/dev/"$PP"[0-9]*) x=${l%/loop/backing_file}; busy="$busy backing-${x##*/}:$(cat "$l")" ;; esac
done
[ -z "$busy" ] || refuse "$DEV is in use:$busy (unmount / losetup -d / swapoff first)"
say "$DEV: 4096-byte blocks, $N blocks, nothing mounted, no swap, no holder"
bat=""
for c in /sys/class/power_supply/*/capacity; do
	[ -e "$c" ] || continue
	case "$(cat "${c%/capacity}/type" 2>/dev/null)" in Battery) bat=$(cat "$c"); break ;; esac
done
if [ -n "$bat" ]; then
	[ "$bat" -ge 15 ] || { [ "$MODE" = dry-run ] && say "WARN battery $bat % (a write needs 15 % or more)" || refuse "battery $bat %, a write needs 15 % or more"; }
	say "battery $bat %"
else
	say "battery: none seen (PC test or no power_supply)"
fi
RO=$(blockdev --getro "$DEV")
say "$DEV read-only flag now: $RO"

# ---- 3. what LUN 0 holds now
readback() { # readback TAG: LUN 0's first 6 / last 5 blocks with O_DIRECT -> $LOGD/TAG-head.bin / TAG-tail.bin
	dd if="$DEV" of="$LOGD/$1-head.bin" bs=4096 count=6 iflag=direct status=none \
		&& dd if="$DEV" of="$LOGD/$1-tail.bin" bs=4096 skip="$TB" count=5 iflag=direct status=none
}
which_is() { # which_is FILE head|tail -> old / new / other
	if cmp -s "$1" "$PLAN/$2-old.bin"; then echo old; elif cmp -s "$1" "$PLAN/$2-new.bin"; then echo new; else echo other; fi
}
readback before || refuse "LUN 0 could not be read"
HS=$(which_is "$LOGD/before-head.bin" head); TS=$(which_is "$LOGD/before-tail.bin" tail)
say "LUN 0 now: blocks 0-5 = head-$HS ($(sha256sum < "$LOGD/before-head.bin" | cut -c1-12)), blocks $TB-$((N - 1)) = tail-$TS ($(sha256sum < "$LOGD/before-tail.bin" | cut -c1-12))"
[ "$HS" = other ] || [ "$TS" = other ] && refuse "LUN 0's table is neither the saved one (head-old / tail-old) nor the planned one: compute the plan again from today's copy"

# ---- 4. the kernel's partition view of a table file (used after the writes)
view() { # view HEADFILE -> "ok" or the mismatches; every used entry i is partition PP(i+1) with the entry's start / size
	local h=$1 ne off i t first last pn st sz bad=""
	ne=$(u32 "$h" 4176); off=$((2 * 4096))
	for i in $(seq 0 $((ne - 1))); do
		t=$(od -An -tx1 -j $((off + i * 128)) -N16 "$h" | tr -d ' \n'); pn=$PP$((i + 1))
		if [ "$t" = 00000000000000000000000000000000 ]; then
			[ -e "/sys/class/block/$pn" ] && bad="$bad $pn:exists-but-entry-$((i + 1))-unused"
			continue
		fi
		first=$(u64 "$h" $((off + i * 128 + 32))); last=$(u64 "$h" $((off + i * 128 + 40)))
		st=$(cat "/sys/class/block/$pn/start" 2>/dev/null); sz=$(cat "/sys/class/block/$pn/size" 2>/dev/null)
		[ "$st" = $((first * 8)) ] && [ "$sz" = $(((last - first + 1) * 8)) ] || bad="$bad $pn:kernel-${st:-none}+${sz:-none}-table-$((first * 8))+$(((last - first + 1) * 8))"
	done
	echo "${bad:-ok}"
}
names() { # the partitions named userdata / fedora as the kernel sees them
	local u n
	for u in /sys/class/block/"$PP"*/uevent; do
		[ -e "$u" ] || continue
		n=$(sed -n 's/^PARTNAME=//p' "$u")
		case "$n" in userdata|fedora) d=${u%/uevent}; echo -n "${d##*/}=$n start $(cat "$d/start") size $(cat "$d/size") (512 B units); " ;; esac
	done
}

# ---- 5. the mode
CW=$(echo "$SH_HN" | cut -c1-12); CR=$(echo "$SH_HO" | cut -c1-12)
if [ "$MODE" = dry-run ]; then
	case "$HS/$TS" in
	old/old) say "LUN 0 equals the saved table (head-old + tail-old). --write would write tail-new (20480 B at block $TB, byte $((TB * 4096))) then head-new (24576 B at block 0), BLKRRPART, read back; confirm code for --write: $CW" ;;
	new/new) say "LUN 0 already holds the planned table (head-new + tail-new). --restore would write tail-old then head-old; confirm code for --restore: $CR" ;;
	old/new) say "LUN 0 holds head-old + tail-new (a write stopped after its first dd). --write would write head-new only (confirm $CW); --restore would write tail-old only (confirm $CR)" ;;
	new/old) say "LUN 0 holds head-new + tail-old (a restore stopped after its first dd). --restore would write head-old only (confirm $CR); --write refuses until the restore is finished" ;;
	esac
	say "kernel view now: $(names)"
	end DRY-RUN-OK 0 "nothing written (LUN 0 = head-$HS + tail-$TS)"
fi
if [ "$MODE" = write ]; then TO=new; CODE=$CW; else TO=old; CODE=$CR; fi
[ "$CONFIRM" = "$CODE" ] || refuse "--$MODE needs --confirm $CODE (the first 12 hex digits of the sha256 of head-$TO.bin); given '${CONFIRM:-none}'"
if [ "$HS" = "$TO" ] && [ "$TS" = "$TO" ]; then
	say "kernel view: $(names)"
	end PASS 0 "LUN 0 already holds head-$TO + tail-$TO: nothing to write"
fi
if [ "$MODE" = write ] && [ "$HS" = new ]; then
	refuse "head-new with tail-old is a stopped restore: finish it with --restore first"
fi
if [ "$RO" = 1 ]; then
	blockdev --setrw "$DEV" && [ "$(blockdev --getro "$DEV")" = 0 ] || refuse "$DEV is read-only and could not be made writable"
	RESTORE_RO=1; say "$DEV writable for the write (it was read-only)"
fi
put() { # put FILE BLOCK COUNT TAG: dd with O_DIRECT + O_SYNC + fsync, then read back with O_DIRECT and compare
	say "writing $(basename "$1") ($(stat -c %s "$1") B, sha256 $(sha256sum < "$1" | cut -c1-12)) at block $2"
	dd if="$1" of="$DEV" bs=4096 seek="$2" count="$3" oflag=direct,sync conv=notrunc,fsync status=none 2> "$LOGD/dd-$4.err" \
		|| { say "FAIL dd: $(tr '\n' ' ' < "$LOGD/dd-$4.err")"; return 1; }
	dd if="$DEV" of="$LOGD/check-$4.bin" bs=4096 skip="$2" count="$3" iflag=direct status=none && cmp -s "$1" "$LOGD/check-$4.bin" \
		|| { say "FAIL the blocks read back at $2 differ from $(basename "$1")"; return 1; }
	say "read back at block $2: equal"
}
if [ "$TS" != "$TO" ]; then
	put "$PLAN/tail-$TO.bin" "$TB" 5 tail || end FAIL 1 "the backup table (tail) write failed; blocks 0-5 untouched (head-$HS): run --dry-run, then --restore"
fi
if [ "$HS" != "$TO" ]; then
	put "$PLAN/head-$TO.bin" 0 6 head || end FAIL 1 "the primary table (head) write failed after tail-$TO: run --dry-run, then --restore from the kit"
fi
sync; blockdev --flushbufs "$DEV" 2>> "$LOG"
# BLKRRPART fails (EBUSY) while any partition is open - also while udev's blkid probes them after a "change" event
# (setting the read-only flag sends one: PC proof, 16 Oct). So: settle udev, re-read (up to 5 tries, settling in
# between), and only then make the disk read-only again.
settle() { command -v udevadm > /dev/null && udevadm settle --timeout=20 2>/dev/null; return 0; }
STALE=0; rr=1; i=0
while [ $i -lt 5 ]; do
	i=$((i + 1)); settle
	blockdev --rereadpt "$DEV" 2> "$LOGD/rereadpt.err" && { rr=0; break; }
	sleep 1
done
restore_ro
if [ "$rr" = 0 ]; then
	say "BLKRRPART: the kernel re-read the table (try $i)"
else
	say "BLKRRPART failed 5 times: $(tr '\n' ' ' < "$LOGD/rereadpt.err")"
	STALE=1   # partx -u (BLKPG) can move partitions but gives them no PARTNAME: by-partlabel stays wrong until a reboot
	if command -v partx > /dev/null && partx -u "$DEV" 2> "$LOGD/partx.err"; then say "partx -u: partition view updated"; else say "partx -u failed: $(tr '\n' ' ' < "$LOGD/partx.err" 2>/dev/null)"; fi
fi
settle
readback after || end FAIL 1 "LUN 0 could not be read back"
HA=$(which_is "$LOGD/after-head.bin" head); TA=$(which_is "$LOGD/after-tail.bin" tail)
say "read back: blocks 0-5 = head-$HA, blocks $TB-$((N - 1)) = tail-$TA"
[ "$HA" = "$TO" ] && [ "$TA" = "$TO" ] || end FAIL 1 "LUN 0 does not hold head-$TO + tail-$TO after the write: run --dry-run"
v=$(view "$PLAN/head-$TO.bin")
say "kernel view: $(names)"
if [ "$v" = ok ]; then
	say "kernel partition view = the table written (every entry's start / size, no partition for an unused entry)"
else
	say "WARN the kernel's partition view is stale:$v"; STALE=1
fi
[ "$STALE" = 0 ] || end PASS-STALE 3 "LUN 0 = head-$TO + tail-$TO, verified on disk; the kernel's partition view is not fully re-read (BLKRRPART busy or a mismatch above): reboot before using the partitions"
end PASS 0 "LUN 0 = head-$TO + tail-$TO, verified on disk and in the kernel's partition view"
