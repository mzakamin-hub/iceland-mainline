#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-only
# gunyah-rehearsal.sh - Gunyah VM manager smoke test for one kernel-iceland kernel (OnePlus Pad 4). Side package:
# the modules come from build-modules.sh and run only on the kernel their vermagic names.
#
#   sudo ./gunyah-rehearsal.sh [installed] probe|vm|teardown|all
#
#   probe     insmod the 10 add-on modules from /run/gunyah/mods; read-only checks (hypervisor id, resource
#             manager, /dev/gunyah)
#   vm        protected VMs only: 4 MiB lent memory, 1 vCPU; power-off x5, MMIO exit, hello text
#   teardown  rmmod in reverse order, check /dev/gunyah is gone and the memory came back
#   all       probe -> vm -> teardown (stops after probe if probe fails)
#
# installed  run on the installed system: the btrfs root/home/var subvolumes may be mounted rw (by design), no
#            other block device may be; needs battery >= 30 % or a charger; a paste-safe summary goes to
#            ~/gunyah-test-<time>.txt of the calling user. Without the flag (RAM rehearsal) no block device may
#            be mounted rw.
#
# Writes: /run/gunyah (tmpfs) and, in installed mode, the one summary file. Nothing goes to /lib/modules, /etc,
# /boot or any partition. Never runs the unprotected mode (the RM loses a VMID per refused attempt). The VM tool
# is one process that never forks while it holds lent guest memory (a fork then hangs the box: SuperTurtleDev).
# A reboot clears everything (modules, lost VMIDs, pinned pages).
set -u
D=/run/gunyah
KR=$(modinfo -F vermagic "$D/mods/gunyah.ko" 2>/dev/null | cut -d' ' -f1 || true)
MODS="gunyah_hypercall timer gunyah_platform_hooks gunyah gunyah_rsc_mgr gunyah_vcpu gunyah_qcom gunyah_irqfd gunyah_ioeventfd gunyah_qtvm"
INSTALLED=0
[ "${1:-}" = installed ] && { INSTALLED=1; shift; }
STEP=${1:-}
case "$STEP" in probe|vm|teardown|all) ;; *) echo "usage: $0 [installed] probe|vm|teardown|all"; exit 2 ;; esac
[ "$(id -u)" = 0 ] || { echo "FAIL not root (use sudo)"; exit 1; }
mkdir -p "$D"; L=$D/log; S=$D/summary

say() { echo "$*" | tee -a "$L"; echo "$*" >> "$S"; echo "gunyah-rh: $*" > /dev/kmsg 2>/dev/null || true; }
fail() { say "FAIL $*"; finish; exit 1; }

finish() {
	[ "$INSTALLED" = 1 ] || return 0
	u=${SUDO_USER:-root}; h=$(getent passwd "$u" | cut -d: -f6); [ -d "$h" ] || h=/root
	out=$h/gunyah-test-$(date +%Y%m%d-%H%M%S).txt
	{ echo "gunyah side-package test, step '$STEP', $(date -Is)"; echo "kernel $(uname -r)"; cat "$S"
	  echo "note: a reboot clears everything (modules, VM state); nothing was written to /lib/modules, /etc, /boot or a partition"; } > "$out"
	chown "$u": "$out" 2>/dev/null || true
	echo "summary: $out"
}

power_ok() {
	local ps=/sys/class/power_supply b cap st on=0 s
	for s in "$ps"/*; do
		[ "$(cat "$s/type" 2>/dev/null)" = Battery ] && b=$s
		case "$(cat "$s/type" 2>/dev/null)" in USB|USB_PD|USB_C|Mains|Wireless)
			[ "$(cat "$s/online" 2>/dev/null)" = 1 ] && on=1 ;; esac
	done
	[ -n "${b:-}" ] || { say "power: no battery supply found"; return 1; }
	cap=$(cat "$b/capacity" 2>/dev/null || echo 0); st=$(cat "$b/status" 2>/dev/null || echo unknown)
	case "$st" in Charging|Full) on=1 ;; esac
	say "power: battery ${cap} % ($st), charger online: $on"
	[ "$on" = 1 ] || [ "$cap" -ge 30 ]
}

rw_mounts() {
	# every block-device mount that is rw, minus (installed mode) the btrfs root/home/var subvolumes
	awk -v inst="$INSTALLED" '$1 ~ /^\/dev\// && $4 ~ /(^|,)rw(,|$)/ {
		if (inst == 1 && $3 == "btrfs" && $4 ~ /(^|,)subvol=\/?(root|home|var)(,|$)/) next
		print $1, $2, $3 }' /proc/mounts
}

guard() {
	[ "$(id -u)" = 0 ] || fail "not root (use sudo)"
	[ -n "$KR" ] || fail "no $D/mods/gunyah.ko (unpack gunyah-mods-<kver>.tar.gz into /run first)"
	[ "$(uname -r)" = "$KR" ] || fail "kernel $(uname -r) is not the one the modules were built for ($KR)"
	rw=$(rw_mounts)
	[ -z "$rw" ] || { echo "$rw" | sed 's/^/rw mount: /' | tee -a "$L"; fail "a block device other than the allowed ones is mounted read-write (see $L)"; }
	if [ "$INSTALLED" = 1 ]; then power_ok || fail "battery below 30 % and no charger"; fi
	[ -d "$D/mods" ] || fail "no $D/mods (unpack gunyah-mods-<kver>.tar.gz into /run first)"
	(cd "$D" && sha256sum -c --quiet SHA256SUMS) || fail "package checksums"
	command -v python3 > /dev/null || fail "no python3"
}

probe() {
	dmesg > "$D/dmesg-before"
	awk '/MemAvailable/ {print $2}' /proc/meminfo > "$D/mem-before"
	for m in $MODS; do
		lsmod | grep -q "^$m " && { say "already loaded: $m"; continue; }
		insmod "$D/mods/$m.ko" || fail "insmod $m"
	done
	say "loaded: $MODS"
	dmesg | diff "$D/dmesg-before" - | grep '^>' > "$D/dmesg-probe"
	grep -i -E 'gunyah|gh_rm|RM rejected' "$D/dmesg-probe" | sed 's/^> *//' | head -20 > "$D/dmesg-probe-gunyah"
	sed 's/^/dmesg: /' "$D/dmesg-probe-gunyah" | while IFS= read -r x; do say "$x"; done
	hyp=$(grep -o 'Running under Gunyah hypervisor.*' "$D/dmesg-probe" | head -1)
	[ -n "$hyp" ] && say "PASS hyp identify: $hyp" || fail "hyp identify (no 'Running under Gunyah hypervisor')"
	[ -c /dev/gunyah ] && say "PASS /dev/gunyah present" || fail "/dev/gunyah missing"
	ls /sys/bus/auxiliary/devices/ 2>/dev/null | grep -qi gunyah && say "PASS RM auxiliary device" || fail "no RM auxiliary device"
	grep -E -i "BUG|WARNING|Oops|Unable to handle|SError" "$D/dmesg-probe" > /dev/null && fail "kernel warnings at probe (see $D/dmesg-probe)"
	say "PASS no kernel warnings at probe"
}

vm() {
	[ -c /dev/gunyah ] || fail "no /dev/gunyah (run probe)"
	dmesg > "$D/dmesg-vm-before"
	n=0
	for i in 1 2 3 4 5; do
		timeout 30 python3 -I "$D/gh_vmtest.py" off lend > "$D/vm-off-$i.txt" 2>&1
		if grep -q "exit STATUS EXITED" "$D/vm-off-$i.txt"; then n=$((n + 1)); else
			grep -h -E '^\[(7|8)' "$D/vm-off-$i.txt" | sed "s/^/vm-off-$i (no EXITED): /" | while IFS= read -r x; do say "$x"; done
		fi
	done
	[ "$n" = 5 ] && say "PASS vm power-off (protected, 4 MiB, 1 vCPU): 5/5 EXITED" || say "FAIL vm power-off: $n/5 EXITED"
	timeout 30 python3 -I "$D/gh_vmtest.py" mmio lend > "$D/vm-mmio.txt" 2>&1
	grep -q "exit MMIO write pa=0x10000000 len=4 data=34120000" "$D/vm-mmio.txt" && grep -q "EXITED" "$D/vm-mmio.txt" \
		&& say "PASS vm MMIO exit" || say "FAIL vm MMIO exit"
	timeout 30 python3 -I "$D/gh_vmtest.py" hello lend > "$D/vm-hello.txt" 2>&1
	grep -q "HELLO OK" "$D/vm-hello.txt" && grep -q "EXITED" "$D/vm-hello.txt" \
		&& say "PASS vm hello: $(grep -o "guest wrote.*" "$D/vm-hello.txt")" || say "FAIL vm hello"
	for f in "$D"/vm-*.txt; do echo "== $f"; cat "$f"; done >> "$L"
	grep -h -E '^\[(7|8)' "$D/vm-off-1.txt" "$D/vm-mmio.txt" | sed 's/^/vm: /' | while IFS= read -r x; do say "$x"; done
	dmesg | diff "$D/dmesg-vm-before" - | grep '^>' > "$D/dmesg-vm"
	grep -E -i "BUG|WARNING|Oops|Unable to handle|SError" "$D/dmesg-vm" > /dev/null \
		&& say "FAIL kernel messages during the VM runs (see $D/dmesg-vm)" || say "PASS no kernel warnings during the VM runs"
}

teardown() {
	for m in $(echo $MODS | tr ' ' '\n' | tac); do
		lsmod | grep -q "^$m " || continue
		rmmod "$m" || say "FAIL rmmod $m (stays loaded until the reboot)"
	done
	[ -e /dev/gunyah ] && say "FAIL /dev/gunyah still present" || say "PASS modules unloaded, /dev/gunyah gone"
	now=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
	if [ -s "$D/mem-before" ]; then
		b=$(cat "$D/mem-before"); d=$(( (b - now) / 1024 ))
		[ "$d" -le 64 ] && say "PASS memory: MemAvailable $((now / 1024)) MiB, $d MiB below the start (<= 64 MiB)" \
			|| say "FAIL memory: MemAvailable $d MiB below the start"
	else
		say "memory: MemAvailable $((now / 1024)) MiB (no start value)"
	fi
}

: > "$S"
case "$STEP" in
	probe) guard; probe ;;
	vm) guard; vm ;;
	teardown) teardown ;;
	all) guard; probe; vm; teardown ;;
	*) echo "usage: $0 [installed] probe|vm|teardown|all"; exit 2 ;;
esac
say "done. A reboot clears everything."
finish
