#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# dracut module "iceland" (iceland-device): how the OnePlus Pad 4 finds its root.
#
# The whole Fedora disk (GPT in 4 KiB units: EFI partition, /boot, btrfs root) lies INSIDE the tablet's userdata
# partition. Linux does not look for a partition table inside a partition, so iceland-carrier attaches a loop
# device with partition scanning over the "carrier" - the partition named userdata (/dev/disk/by-partlabel) - and
# udev then finds the root by its UUID on loop0p3 exactly as on any disk. The loop device uses direct I/O, so it
# has the carrier's 4096-byte blocks and no second page cache.
# Rehearsal (only with iceland.rehearsal= on the kernel command line, which only the RAM-only rehearsal head
# sets): the carrier is a network block device served by the PC over the USB link; see iceland-rehearsal.
# Rollback (only with iceland.rollback=SNAPSHOT, from a "Roll back to ..." boot entry): see iceland-rollback.
# 0.28-32: with iceland.carrier.map=dm the partitions are device-mapper linear maps instead (iceland-dmmap; dracut's
# "dm" module brings dmsetup and the dm udev rules, sfdisk reads the inner GPT).
check() { return 0; }
depends() { echo systemd btrfs dm; return 0; }
installkernel() {
	# loop, btrfs, vfat are built into kernel-iceland; nbd (rehearsal) and the watchdog are modules
	hostonly='' instmods nbd qcom_wdt
}
install() {
	inst_multiple losetup blockdev sed grep cat sleep timeout ip mkdir ln readlink basename dd od tr head \
		mount umount mountpoint btrfs date modprobe seq cut touch chmod wc ls mv
	inst_multiple -o nbd-client busybox sha256sum
	inst_multiple sfdisk dmsetup stat
	inst_script /usr/libexec/iceland/iceland-dmmap /usr/libexec/iceland/iceland-dmmap
	inst_script "$moddir/iceland-carrier" /usr/libexec/iceland/iceland-carrier
	inst_script "$moddir/iceland-rehearsal" /usr/libexec/iceland/iceland-rehearsal
	inst_script "$moddir/iceland-rollback" /usr/libexec/iceland/iceland-rollback
	inst_script /usr/libexec/iceland/iceland-storage-ro /usr/libexec/iceland/iceland-storage-ro
	inst_rules 59-iceland-storage-ro.rules
	inst_simple "$moddir/iceland-carrier.service" "$systemdsystemunitdir/iceland-carrier.service"
	inst_simple "$moddir/iceland-rollback.service" "$systemdsystemunitdir/iceland-rollback.service"
	$SYSTEMCTL -q --root "$initdir" add-wants initrd-root-device.target iceland-carrier.service
	$SYSTEMCTL -q --root "$initdir" add-wants initrd-root-device.target iceland-rollback.service
}
