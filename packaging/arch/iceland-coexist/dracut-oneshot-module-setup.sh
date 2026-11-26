#!/usr/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# dracut module "iceland-oneshot" (iceland-coexist 1.0-4): clear GRUB's one-shot next_entry from the initramfs,
# before systemd-udevd starts (see /usr/bin/iceland-oneshot). The unit is inert unless the kernel command line has
# iceland.oneshot=NAME, which only the entries iceland-oneshot writes carry.
check() { return 0; }
depends() { echo systemd; return 0; }
install() {
	inst_multiple grub2-editenv blkid mount umount dd cmp stat sed grep cat mkdir sleep head timeout sync rm cp mv date tr
	inst_script /usr/bin/iceland-oneshot /usr/bin/iceland-oneshot
	inst_simple "$moddir/iceland-oneshot-clear.service" "$systemdsystemunitdir/iceland-oneshot-clear.service"
	$SYSTEMCTL -q --root "$initdir" add-wants sysinit.target iceland-oneshot-clear.service
}
