# SPDX-License-Identifier: GPL-2.0-or-later
#
# iceland-device: Fedora settings for the OnePlus Pad 4 (iceland) running kernel-iceland.
# No firmware and no binaries: configuration files and small scripts only.

Name:           iceland-device
Version:        0.5
Release:        1%{?dist}
Summary:        OnePlus Pad 4 (iceland) device settings for Fedora
License:        GPL-2.0-or-later
URL:            https://github.com/mzakamin-hub/iceland-mainline
BuildArch:      noarch
Source0:        80-iceland-kernel.conf
Source1:        sleep-iceland.conf
Source2:        journald-iceland.conf
Source3:        49-iceland-no-system-upgrade.rules
Source4:        iceland-bdaddr.service
Source5:        iceland-bdaddr
Source6:        iceland-cmdline
Source7:        90-iceland-dracut.conf
Source8:        60-iceland-wifi-powersave.conf
Source9:        iceland-battery-guard
Source10:       iceland-battery-guard.service
Source11:       iceland-local.repo
Source12:       iceland-repo-sync
Source13:       iceland-refresh
Source14:       iceland-refresh.service
Source15:       refresh.conf
Source16:       iceland-npu
Source17:       iceland-npu-off.service
Source18:       iceland-wifi-country
Source19:       iceland-wifi-country.service

Requires:       kernel-iceland
Requires:       bluez
Requires:       python3
Requires:       python3-gobject
Requires:       createrepo_c
Requires:       curl
Requires:       iw
Requires:       alsa-utils
Requires(posttrans): grubby

%description
Settings that make Fedora 44 work safely on the OnePlus Pad 4 with the kernel-iceland package:
- Fedora's own kernel packages are excluded from dnf (they have no Pad 4 support);
  kernel-iceland is the default kernel;
- suspend uses s2idle (the only sleep state on this SoC);
- the journal is capped;
- Fedora version upgrades are blocked until they are tested with kernel-iceland;
- fwupd never uses the UEFI capsule path (U-Boot is not a firmware target);
- the tablet's own Bluetooth address is applied at boot from /etc/iceland/bdaddr (written by the installer from the
  stock value, never shipped);
- the kernel command line carries the options kernel-iceland still needs;
- the initramfs carries the display, touch and GPU drivers and their firmware;
- Wi-Fi power saving is on;
- iceland-battery-guard enforces the stock 11.A.38 charging limits as a second layer over the charger firmware
  (temperature regions, per-region voltages and currents, USB-C connector temperature, 72/77 C power-off);
- kernel-iceland updates come from a local dnf repository (/var/lib/iceland/repo, filled by iceland-repo-sync);
- the panel runs 60 Hz on battery and 120 Hz on AC (iceland-refresh, /etc/iceland/refresh.conf);
- the CDSP (NPU) stays off until `iceland-npu on`;
- the Wi-Fi regulatory country comes from /etc/iceland/wifi-country (written at install: the owner's country).

%prep
%build

%install
install -Dm0644 %{SOURCE0} %{buildroot}/usr/share/dnf5/libdnf.conf.d/80-iceland-kernel.conf
install -Dm0644 %{SOURCE1} %{buildroot}/usr/lib/systemd/sleep.conf.d/60-iceland.conf
install -Dm0644 %{SOURCE2} %{buildroot}/usr/lib/systemd/journald.conf.d/60-iceland.conf
install -Dm0644 %{SOURCE3} %{buildroot}/usr/share/polkit-1/rules.d/49-iceland-no-system-upgrade.rules
install -Dm0644 %{SOURCE4} %{buildroot}/usr/lib/systemd/system/iceland-bdaddr.service
install -Dm0755 %{SOURCE5} %{buildroot}/usr/libexec/iceland/iceland-bdaddr
install -Dm0755 %{SOURCE6} %{buildroot}/usr/libexec/iceland/iceland-cmdline
install -Dm0644 %{SOURCE7} %{buildroot}/usr/lib/dracut/dracut.conf.d/90-iceland.conf
install -Dm0644 %{SOURCE8} %{buildroot}/usr/lib/NetworkManager/conf.d/60-iceland-wifi-powersave.conf
install -Dm0755 %{SOURCE9} %{buildroot}/usr/libexec/iceland/iceland-battery-guard
install -Dm0644 %{SOURCE10} %{buildroot}/usr/lib/systemd/system/iceland-battery-guard.service
install -Dm0644 %{SOURCE11} %{buildroot}/etc/yum.repos.d/iceland-local.repo
install -Dm0755 %{SOURCE12} %{buildroot}/usr/bin/iceland-repo-sync
install -Dm0755 %{SOURCE13} %{buildroot}/usr/libexec/iceland/iceland-refresh
install -Dm0644 %{SOURCE14} %{buildroot}/usr/lib/systemd/user/iceland-refresh.service
install -Dm0644 %{SOURCE15} %{buildroot}/etc/iceland/refresh.conf
install -Dm0755 %{SOURCE16} %{buildroot}/usr/bin/iceland-npu
install -Dm0644 %{SOURCE17} %{buildroot}/usr/lib/systemd/system/iceland-npu-off.service
install -Dm0755 %{SOURCE18} %{buildroot}/usr/libexec/iceland/iceland-wifi-country
install -Dm0644 %{SOURCE19} %{buildroot}/usr/lib/systemd/system/iceland-wifi-country.service
install -d %{buildroot}/var/lib/iceland/repo/aarch64
install -d %{buildroot}/etc/iceland

%posttrans
# kernel-iceland is the default kernel and new kernel-iceland versions become the default
cat > /etc/sysconfig/kernel <<'EOT'
# written by iceland-device
UPDATEDEFAULT=yes
DEFAULTKERNEL=kernel-iceland
EOT
/usr/libexec/iceland/iceland-cmdline || :
systemctl enable iceland-battery-guard.service iceland-npu-off.service iceland-wifi-country.service >/dev/null 2>&1 || :
systemctl --global enable iceland-refresh.service >/dev/null 2>&1 || :
# an empty local repository, so dnf doesn't complain before the first iceland-repo-sync
[ -d /var/lib/iceland/repo/aarch64/repodata ] || createrepo_c -q /var/lib/iceland/repo/aarch64 || :
systemctl preset iceland-bdaddr.service >/dev/null 2>&1 || systemctl enable iceland-bdaddr.service >/dev/null 2>&1 || :

%triggerin -- fwupd
f=/etc/fwupd/fwupd.conf
if [ -f "$f" ] && ! grep -q '^DisabledPlugins=.*uefi_capsule' "$f"; then
	if grep -q '^DisabledPlugins=' "$f"; then
		sed -i 's/^DisabledPlugins=\(.*\)$/DisabledPlugins=\1;uefi_capsule/; s/=;/=/' "$f"
	else
		sed -i '0,/^\[fwupd\]/s//[fwupd]\nDisabledPlugins=uefi_capsule/' "$f"
	fi
fi

%preun
[ "$1" -eq 0 ] && systemctl --global disable iceland-refresh.service >/dev/null 2>&1; [ "$1" -eq 0 ] && systemctl disable iceland-wifi-country.service iceland-npu-off.service iceland-battery-guard.service iceland-bdaddr.service >/dev/null 2>&1 || :

%files
/usr/share/dnf5/libdnf.conf.d/80-iceland-kernel.conf
/usr/lib/systemd/sleep.conf.d/60-iceland.conf
/usr/lib/systemd/journald.conf.d/60-iceland.conf
/usr/share/polkit-1/rules.d/49-iceland-no-system-upgrade.rules
/usr/lib/systemd/system/iceland-bdaddr.service
/usr/libexec/iceland/iceland-bdaddr
/usr/libexec/iceland/iceland-cmdline
/usr/lib/dracut/dracut.conf.d/90-iceland.conf
/usr/lib/NetworkManager/conf.d/60-iceland-wifi-powersave.conf
/usr/libexec/iceland/iceland-battery-guard
/usr/lib/systemd/system/iceland-battery-guard.service
%config(noreplace) /etc/yum.repos.d/iceland-local.repo
/usr/bin/iceland-repo-sync
/usr/libexec/iceland/iceland-refresh
/usr/lib/systemd/user/iceland-refresh.service
%config(noreplace) /etc/iceland/refresh.conf
/usr/bin/iceland-npu
/usr/lib/systemd/system/iceland-npu-off.service
/usr/libexec/iceland/iceland-wifi-country
/usr/lib/systemd/system/iceland-wifi-country.service
%dir /var/lib/iceland
%dir /var/lib/iceland/repo
%dir /var/lib/iceland/repo/aarch64
%dir /etc/iceland

%changelog
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.5-1
- Wi-Fi regulatory country from /etc/iceland/wifi-country; requires iw and alsa-utils (UCM FixedBootSequence)
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.4-1
- local kernel update repository + iceland-repo-sync; 60/120 Hz by power source; CDSP off unless used
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.3-1
- battery guard verified against stock: per-region stop/recharge voltages and charge currents, the stock
  USB-C connector rules (57/69 C, gaps, latch until unplug, cool-down), stop when the temperature is unreadable
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.2-1
- iceland-battery-guard with the stock 11.A.38 charging limits
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.1-1
- First version: kernel exclusion, s2idle, journald cap, upgrade block, fwupd guard, BT address, cmdline
