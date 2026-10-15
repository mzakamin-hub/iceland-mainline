#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# keep-only-current.sh (15 Oct 2026): keep only the RUNNING kernel and the current root; remove every other
# kernel-iceland, every root snapshot (snapshots/root-* and root.before-rollback-*) and their "Roll back" GRUB entries.
#
#   sudo bash keep-only-current.sh            READ ONLY: shows what would go
#   sudo bash keep-only-current.sh --delete   does it, after you type KEEP-ONLY
#
# PERMANENT: removed kernels and deleted snapshots cannot be brought back. Afterwards there is no older kernel to
# pick in GRUB and no rollback entry until the next dnf transaction takes a new snapshot (iceland-snapshot does that
# by itself). Kept: the running kernel, /home, /var, the update bundles' undo copies in /var/lib/iceland/backup-*.
# Refuses unless the running kernel is the confirmed default and no trial boot is pending.
set -u
DO=0; [ "${1:-}" = --delete ] && DO=1
[ "$(id -u)" = 0 ] || { echo "run with sudo"; exit 1; }
say() { echo "keep-only-current: $*"; }
die() { say "STOP: $*"; exit 1; }

RUN=$(uname -r)
TS=$(/usr/libexec/iceland/iceland-trial status 2>/dev/null)
CONF=$(echo "$TS" | sed -n 's/^confirmed: *//p'); PEND=$(echo "$TS" | sed -n 's/^pending: *//p')
SAVED=$(grub2-editenv - list 2>/dev/null | sed -n 's/^saved_entry=//p')
say "running kernel $RUN; confirmed '${CONF:-?}'; pending '${PEND:-none}'; saved_entry '$SAVED'"
[ -z "$PEND" ] || [ "$PEND" = none ] || die "a trial boot is pending ($PEND): restart into it first, then run again"
case "$SAVED" in *"-$RUN") ;; *) die "the GRUB default ($SAVED) is not the running kernel $RUN: confirm the running kernel first" ;; esac

# 1. kernels
mapfile -t KALL < <(rpm -q kernel-iceland --qf '%{NAME}-%{VERSION}-%{RELEASE}.%{ARCH}\n' 2>/dev/null)
KDEL=()
for k in "${KALL[@]}"; do
	# rpm version 7.3.0~rc7.iceland.00436.gf1673c99e731 = uname -r 7.3.0-rc7-iceland-00436-gf1673c99e731
	kv=$(rpm -q --qf '%{VERSION}' "$k" 2>/dev/null | sed 's/~/-/; s/\.iceland\./-iceland-/; s/\.g\([0-9a-f]*\)$/-g\1/')
	[ "$kv" = "$RUN" ] && { say "keep kernel  $k (running)"; continue; }
	KDEL+=("$k"); say "remove kernel $k${kv:+ ($kv)}"
done
rpm -q kernel-iceland --qf '%{VERSION}\n' | grep -q . || die "no kernel-iceland found"
[ ${#KDEL[@]} -lt ${#KALL[@]} ] || die "the running kernel is not among the kernel-iceland packages: nothing removed"

# 2. snapshots (top level of the root's btrfs)
SRC=$(findmnt -n -o SOURCE / | sed 's/\[.*//')
[ "$(findmnt -n -o FSTYPE /)" = btrfs ] || die "the root is not btrfs"
TOP=/run/iceland-cleanup-top; mkdir -p "$TOP"
mountpoint -q "$TOP" || mount -t btrfs -o subvolid=5,noatime "$SRC" "$TOP" || die "cannot mount the btrfs top level"
trap 'umount "$TOP" 2>/dev/null; rmdir "$TOP" 2>/dev/null' EXIT
[ -d "$TOP/root" ] || die "no subvolume 'root' at the top level: unexpected layout, nothing changed"
mapfile -t SDEL < <(ls -1d "$TOP"/snapshots/root-* "$TOP"/root.before-rollback-* 2>/dev/null | grep -v '\.info$' | sort)
for s in "${SDEL[@]}"; do say "delete snapshot ${s#$TOP/}"; done
mapfile -t EDEL < <(ls -1 /boot/loader/entries/iceland-rollback-*.conf 2>/dev/null)
for e in "${EDEL[@]}"; do say "delete GRUB entry ${e##*/}"; done
say "kept: the running kernel, subvolumes root / home / var, /var/lib/iceland/backup-* (undo copies)"
[ ${#KDEL[@]} -eq 0 ] && [ ${#SDEL[@]} -eq 0 ] && [ ${#EDEL[@]} -eq 0 ] && { say "nothing to remove"; exit 0; }
[ "$DO" = 1 ] || { say "READ ONLY - nothing changed. To do it: sudo bash $0 --delete"; exit 0; }

printf 'keep-only-current: this is PERMANENT. Type KEEP-ONLY to go on: ' > /dev/tty
read -r ans < /dev/tty; [ "$ans" = KEEP-ONLY ] || die "not confirmed: nothing changed"

if [ ${#KDEL[@]} -gt 0 ]; then
	# no new snapshot for this transaction; dnf itself still refuses to remove the running kernel
	ICELAND_NO_SNAPSHOT=1 dnf remove -y --setopt=protected_packages= --setopt=protect_running_kernel=True "${KDEL[@]}" \
		|| die "dnf remove failed: snapshots untouched"
fi
for s in "${SDEL[@]}"; do
	btrfs property set -ts "$s" ro false 2>/dev/null
	btrfs subvolume delete "$s" > /dev/null && rm -f "$s.info" && say "deleted ${s#$TOP/}" || say "could not delete ${s#$TOP/}"
done
rm -f /boot/loader/entries/iceland-rollback-*.conf
/usr/libexec/iceland/iceland-snapshot entries > /dev/null 2>&1
say "now: kernels $(rpm -q kernel-iceland | tr '\n' ' ')"
say "     GRUB entries: $(ls -1 /boot/loader/entries/ | tr '\n' ' ')"
say "     snapshots left: $(ls -1d "$TOP"/snapshots/root-* "$TOP"/root.before-rollback-* 2>/dev/null | grep -vc '\.info$')"
say "done; the default stays $SAVED"
