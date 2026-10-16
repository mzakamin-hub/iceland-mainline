#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# image/kiwi/desc/edit_boot_install.sh - kiwi's editbootinstall hook: runs NOT chrooted on the build host after kiwi installed
# the boot loader, with "DISK_FILE BOOT_PARTITION_DEVICE" (here: the /boot partition, ext4, on kiwi's 4 KiB loop device).
# Why: kiwi's grub2 setup rewrites every BLS entry's "options" line with its own command line (bootloader/config/grub2.py
# _fix_grub_loader_entries_boot_cmdline), which drops what iceland-grub-setup added in config.sh. This re-applies exactly
# iceland-grub-setup's per-entry rules (iceland-device 0.28-17): "$iceland_args" at the end of every kernel-iceland entry's
# options (not the rollback entries), and "devicetree /dtb-<version>/qcom/kaanapali-oneplus-iceland.dtb" when that file
# exists (PER_KERNEL_DT=1, the package default). Then the grubenv: no menu_auto_hide (the menu is shown 3 s for the
# volume keys). Writes only the /boot partition of the image being built. One "iceland-editboot:" line; exit 1 on a miss.
set -euo pipefail
read -r -a A <<< "$*"
BOOTDEV=${A[1]:-}
say() { echo "iceland-editboot: $*"; }
[ -b "$BOOTDEV" ] || { say "FAIL no boot partition device (args: $*)"; exit 1; }
M=$(mktemp -d)
trap 'umount "$M" 2>/dev/null || :; rmdir "$M"' EXIT
mount "$BOOTDEV" "$M"
[ -d "$M/loader/entries" ] || { say "FAIL $BOOTDEV holds no loader/entries (not /boot?)"; exit 1; }
DT=qcom/kaanapali-oneplus-iceland.dtb; n=0; d=0
for e in "$M"/loader/entries/*iceland*.conf; do
	[ -f "$e" ] || continue
	case "$e" in */iceland-rollback-*) continue ;; esac
	grep -q '^options .*\$iceland_args' "$e" || sed -i 's/^\(options .*\)$/\1 $iceland_args/' "$e"
	grep -q '^options .*rootflags=subvol=root' "$e" || sed -i 's/^\(options \)/\1rootflags=subvol=root /' "$e"
	v=$(sed -n 's/^version //p' "$e")
	if ! grep -q '^devicetree ' "$e" && [ -e "$M/dtb-$v/$DT" ]; then echo "devicetree /dtb-$v/$DT" >> "$e"; fi
	grep -q '^devicetree ' "$e" && d=$((d + 1))
	n=$((n + 1))
done
[ "$n" -ge 1 ] && [ "$d" = "$n" ] || { say "FAIL kernel-iceland entries $n, with a device tree $d"; exit 1; }
if [ -f "$M/grub2/grubenv" ] && grep -q '^menu_auto_hide=' "$M/grub2/grubenv"; then
	if command -v grub2-editenv > /dev/null; then grub2-editenv "$M/grub2/grubenv" unset menu_auto_hide
	else say "FAIL grubenv has menu_auto_hide and no grub2-editenv on the build host"; exit 1; fi
fi
sync
say "entries $n: \$iceland_args + devicetree; grubenv menu_auto_hide $(grep -c '^menu_auto_hide=' "$M/grub2/grubenv" 2>/dev/null || echo 0)"
