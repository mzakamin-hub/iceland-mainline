#!/bin/bash
# SPDX-License-Identifier: GPL-2.0-or-later
# image/kiwi/desc/config.sh - kiwi's post-prepare script (runs CHROOTED in the image root after every package is installed).
# The distro configuration of the B-run recipe (wf/generic/recipe/tablet-b150g.sh, steps build1a / build2a / build2b and the
# B150g generic additions gen_clean / gen_check), done here on the PC instead of on the tablet. What the packages do
# themselves (iceland-device's %posttrans: units, presets, holds 80-iceland-kernel.conf / 50-iceland-fedora-hold.repo,
# the SELinux module, GRUB settings) is NOT repeated; this script only does what the B run did around the packages.
# Not here: the SELinux labels (kiwi relabels the disk with setfiles at the sync, as build2b did), the partition layout
# (config.kiwi), the firmware (iceland-firmware owns it; the tablet extractor does not run in a PC build).
# Every step prints one "iceland-config:" line; any failed invariant exits 1 (kiwi stops, no image).
set -euo pipefail
test -f /.kconfig && . /.kconfig
test -f /.profile && . /.profile
say() { echo "iceland-config: $*"; }
die() { say "FAIL $*"; exit 1; }

# 0. what the image must not contain at all (B149 build1a's rm_list; kiwi's <ignore> kept them out of the transaction)
left=$(rpm -qa --qf '%{NAME}\n' 'kernel' 'kernel-core' 'kernel-modules*' 'dracut-config-rescue' 'uboot-images-*' 'bcm2*-firmware' \
	'fwupd-efi' 'fwupd-plugin-uefi-capsule-data' 'gnome-boxes' 'hyperv-daemons' 'open-vm-tools*' 'qemu-guest-agent' 'spice-vdagent' \
	'spice-webdavd' 2>/dev/null | sort -u | tr '\n' ' ')
[ -z "$left" ] || die "left-out packages installed: $left"
say "left-out packages: none"

# 1. accounts of sysusers.d entries the image lacks (systemd-sysusers.service skips at the first boot: ConditionNeedsUpdate)
systemd-sysusers > /dev/null 2>&1 || die "systemd-sysusers"
say "sysusers: done"

# 2. the kernel: exactly one kernel-iceland; its boot entry and a GENERIC initramfs
kv=(); for m in /usr/lib/modules/*-iceland*; do [ -d "$m" ] && kv+=("${m##*/}"); done
[ "${#kv[@]}" = 1 ] || die "want exactly one kernel-iceland module tree, have: ${kv[*]:-none}"
KVER=${kv[0]}
rm -f /boot/vmlinuz-0-rescue-* /boot/initramfs-0-rescue-* /boot/loader/entries/*-0-rescue.conf
if ! ls /boot/loader/entries/*-"$KVER".conf > /dev/null 2>&1; then
	# kernel-install needs an entry token; the image's machine id stays "uninitialized" for its first boot (B149 used the
	# token of the official image's entries: one fixed 32-hex token per build here, written nowhere else)
	TOK=$(tr -d '-' < /proc/sys/kernel/random/uuid)
	KERNEL_INSTALL_MACHINE_ID=$TOK MACHINE_ID=$TOK kernel-install add "$KVER" "/usr/lib/modules/$KVER/vmlinuz" > /dev/null || die "kernel-install add $KVER"
fi
e=$(ls /boot/loader/entries/*-"$KVER".conf 2>/dev/null | head -n 1); [ -n "$e" ] || die "no boot entry for $KVER"
# dracut's default is host-only: in a build chroot that would describe the BUILD host, not the tablet. The image's initramfs
# is built generic once (the device package's 90/91-iceland dracut confs still apply: their drivers, firmware, the iceland
# module and the omit list); later kernel updates on the tablet go host-only as on the B149 install.
printf 'hostonly="no"\nhostonly_cmdline="no"\n' > /etc/dracut.conf.d/00-iceland-image-build.conf
dracut -f --kver "$KVER" "/boot/initramfs-$KVER.img" > /dev/null 2>&1 || { rm -f /etc/dracut.conf.d/00-iceland-image-build.conf; die "dracut $KVER"; }
rm -f /etc/dracut.conf.d/00-iceland-image-build.conf
lsi=$(lsinitrd "/boot/initramfs-$KVER.img" 2>/dev/null)
for want in iceland-carrier /nbd.ko 59-iceland-storage-ro gen80200_zap qcom_q6v5_pas; do
	printf '%s\n' "$lsi" | grep -q -- "$want" || die "initramfs lacks $want"
done
[ -e "/boot/dtb-$KVER/qcom/kaanapali-oneplus-iceland.dtb" ] || die "no /boot/dtb-$KVER/qcom/kaanapali-oneplus-iceland.dtb"
say "kernel $KVER: entry ${e##*/}, generic initramfs $(du -m "/boot/initramfs-$KVER.img" | cut -f1) MiB, device tree present"

# 3. GRUB as on the installed tablet: per-kernel device tree, 3 s menu, $iceland_args (idempotent; kiwi's grub2-mkconfig
# runs later and keeps GRUB_DEVICETREE; edit_boot_install.sh re-applies the entry lines kiwi rewrites)
/usr/libexec/iceland/iceland-grub-setup || die "iceland-grub-setup"
[ -x /usr/libexec/iceland/iceland-cmdline ] && { /usr/libexec/iceland/iceland-cmdline > /dev/null 2>&1 || say "iceland-cmdline rc $? (entries keep their options)"; }
grep -q '^GRUB_DEVICETREE="qcom/kaanapali-oneplus-iceland.dtb"' /etc/default/grub || die "GRUB_DEVICETREE not set"
say "grub: $(grep -c '^devicetree ' "$e") devicetree line(s), timeout $(sed -n 's/^GRUB_TIMEOUT=//p' /etc/default/grub)"

# 4. the desktop: graphical target, the first-boot wizard (gnome-initial-setup makes the first user), no autologin
systemctl set-default graphical.target > /dev/null 2>&1
rpm -q gnome-initial-setup > /dev/null || die "gnome-initial-setup missing"
if [ -f /etc/gdm/custom.conf ]; then
	sed -i -E '/^[[:space:]]*(AutomaticLoginEnable|AutomaticLogin|TimedLoginEnable|InitialSetupEnable)[[:space:]]*=/d' /etc/gdm/custom.conf
fi
passwd -l root > /dev/null 2>&1 || :
say "desktop: graphical.target, wizard on, root locked"

# 5. the clock stamp (wf/fedtest 2.1): systemd advances the boot clock to this file's mtime (the tablet's RTC cannot be set)
install -d /var/lib/systemd/timesync && touch /var/lib/systemd/timesync/clock
say "clock stamp: $(date -u -r /var/lib/systemd/timesync/clock +%FT%TZ)"

# 6. B150g gen_clean: unit data and build residues out (none expected in a PC build: nothing here came from a unit)
for p in /usr/lib/firmware/updates/.iceland-extracted /etc/iceland/bdaddr /etc/iceland/wifimac /var/lib/systemd/random-seed \
	/root/.bash_history /root/.lesshst /root/.python_history /var/lib/iceland/refresh-before.tsv /var/lib/iceland/refresh-fw-before.txt \
	/var/lib/iceland/install-build /var/lib/iceland/provisioned /var/lib/iceland/grown; do rm -f "$p"; done
rm -rf /var/lib/iceland/unheld-rpms /root/.ssh /var/cache/dnf /var/cache/libdnf5 /etc/ssh/ssh_host_* \
	/etc/NetworkManager/system-connections/* /var/lib/NetworkManager/*.lease /var/lib/NetworkManager/seen-bssids \
	/var/lib/NetworkManager/timestamps /var/log/journal/*/* /var/log/dnf5.log*
printf 'uninitialized\n' > /etc/machine-id
# the generic-image marker, exactly as the B150g recipe's gen_clean writes it (iceland-grow acts only when it exists)
mkdir -p /etc/iceland
printf 'B150g generic image (Fedora Remix for OnePlus Pad 4), built %s\n' "$(date -u +%Y-%m-%d)" > /etc/iceland/generic-image
chmod 644 /etc/iceland/generic-image
say "generic clean: done (machine-id uninitialized, generic-image marker)"

# 7. the generic invariants (gen_check's list, the parts that are checkable in the chroot; image-check.sh repeats all of
# them on the finished disk, plus the layout)
bad=""
chk() { [ "$1" = 0 ] || bad="$bad $2"; }
chk "$(grep -q '^B150g generic image' /etc/iceland/generic-image 2>/dev/null && [ "$(wc -l < /etc/iceland/generic-image)" = 1 ] && echo 0 || echo 1)" generic-image-marker
chk "$(awk -F: '$3 >= 1000 && $3 < 60000' /etc/passwd | grep -c .)" users
chk "$(find /home -mindepth 1 -maxdepth 1 2>/dev/null | grep -c .)" homes
chk "$(grep -q '^Type=root' /etc/repart.d/50-root.conf 2>/dev/null && echo 0 || echo 1)" repart-root-rule
chk "$([ "$(readlink /etc/systemd/system/systemd-repart.service 2>/dev/null)" = /dev/null ] && echo 1 || echo 0)" repart-masked
chk "$([ -x /usr/libexec/iceland/iceland-provision ] && [ -L /usr/lib/systemd/system/multi-user.target.wants/iceland-provision.service ] && echo 0 || echo 1)" provision-unit
chk "$([ -x /usr/libexec/iceland/iceland-grow ] && [ -L /usr/lib/systemd/system/multi-user.target.wants/iceland-grow.service ] && echo 0 || echo 1)" grow-unit
chk "$(find /var/lib/gdm -name gnome-initial-setup-done 2>/dev/null | grep -c .)" wizard-done-stamp
[ -z "$bad" ] || die "generic invariants:$bad"
say "generic invariants: PASS"
exit 0
