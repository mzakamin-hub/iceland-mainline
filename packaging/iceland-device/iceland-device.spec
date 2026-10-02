# SPDX-License-Identifier: GPL-2.0-or-later
#
# iceland-device: Fedora settings for the OnePlus Pad 4 (iceland) running kernel-iceland.
# No firmware and no binaries: configuration files and small scripts only.

Name:           iceland-device
Version:        0.17
Release:        1%{?dist}
Summary:        OnePlus Pad 4 (iceland) device settings for Fedora
License:        GPL-2.0-or-later AND BSD-3-Clause
URL:            https://github.com/mzakamin-hub/iceland-mainline
BuildArch:      noarch
BuildRequires:  m4
BuildRequires:  alsa-utils
# alsatplg (Fedora ships it apart from alsa-utils)
BuildRequires:  alsa-topology-utils
Source0:        80-iceland-kernel.conf
# Fedora's repositories: GRUB, shim, firmware and the sensor programs held; the release pinned (dnf5 repository
# overrides; an empty file of the same name in /etc/dnf/repos.override.d masks either)
Source60:       50-iceland-fedora-hold.repo
Source61:       51-iceland-fedora-44-pin.repo
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
# upstream linux-msm/audioreach-topology at 993a17d (BSD-3-Clause) + our Pad 4 overlay (audio/ in iceland-mainline)
Source20:       audioreach-topology-993a17d.tar.gz
Source21:       iceland-audio.tar.gz
# the Pad 4 tuned profiles behind GNOME's power modes (tuned-ppd) + the script that maps tuned-ppd to them
Source22:       iceland-tuned.tar.gz
Source23:       iceland-power-profiles
Source24:       battery-guard.conf
Source25:       machine-info
# the sensors behind the ADSP (accelerometer / auto-rotate, light, proximity, compass): udev rule, unit ordering,
# the readiness wait, the restart after a suspend
Source26:       81-iceland-ssc.rules
Source27:       iio-sensor-proxy-iceland.conf
Source28:       hexagonrpcd-adsp-sensorspd-iceland.conf
Source29:       iceland-ssc-wait
Source30:       iceland-ssc-resume.service
# cameras: libcamera software-ISP tuning of the two sensors (the file name is the sensor model)
Source31:       sc1320cs.yaml
# the thresholds UPower writes for "Preserve Battery Health" (charge limit, kernel-iceland's qcom_battmgr)
Source32:       61-iceland-battery.hwdb
# UPower after udev's device scan (it reads the thresholds only once)
Source33:       upower-iceland.conf
Source34:       sc820cs.yaml
# cameras: hide the raw video nodes of the camera subsystem from the desktop's device list
Source35:       51-iceland-camera.conf
# cameras: a fixed focus position of the rear camera while it streams (no autofocus in libcamera's simple pipeline)
Source36:       iceland-camera-focus
Source37:       iceland-camera-focus.service
Source38:       camera-focus.conf
# cameras: the CMA dma-heaps for root only (libcamera's software ISP then allocates from the system heap)
Source39:       71-iceland-dma-heap.rules
# the skin temperature policy (stock's temperature gears): the daemon, its unit, its settings (the sources from 50 on
# belong to the guard / thermal part of 0.17, the camera part numbers below 50)
Source50:       iceland-thermal
Source51:       iceland-thermal.service
Source52:       thermal.conf
# what logind does when the cover closes: suspend on battery, lock (screen off, awake) with a charger in
Source53:       logind-iceland.conf

Requires:       kernel-iceland
Requires:       bluez
Requires:       python3
Requires:       python3-gobject
Requires:       createrepo_c
Requires:       curl
Requires:       iw
Requires:       alsa-utils
Requires:       tuned-ppd
# the sensor programs (packaging/sensors; not in Fedora 44, iio-sensor-proxy there has no SSC support)
Requires:       hexagonrpc
Requires:       libssc
Requires:       iio-sensor-proxy >= 3.9-10
# the desktop's way to the cameras: libcamera's software ISP, PipeWire's libcamera plug-in, the portal that asks
# for the camera permission (GNOME backend) and the document portal's FUSE helper
Requires:       libcamera-ipa
Requires:       pipewire-plugin-libcamera
Requires:       xdg-desktop-portal-gnome
Requires:       fuse3
Recommends:     snapshot
Recommends:     pipewire-gstreamer
Requires(posttrans): grubby

%description
Settings that make Fedora 44 work safely on the OnePlus Pad 4 with the kernel-iceland package:
- Fedora's own kernel packages are excluded from dnf (they have no Pad 4 support);
  kernel-iceland is the default kernel;
- suspend uses s2idle (the only sleep state on this SoC);
- the cover: closing it suspends the tablet on battery and opening it wakes it; with a charger in, closing it
  locks the session and turns the screen off but the tablet stays awake, so that the charging guard keeps
  watching (logind drop-in);
- the journal is capped;
- Fedora version upgrades are blocked until they are tested with kernel-iceland;
- fwupd never uses the UEFI capsule path (U-Boot is not a firmware target);
- the tablet's own Bluetooth address is applied at boot from /etc/iceland/bdaddr (written by the installer from the
  stock value, never shipped);
- the kernel command line carries the options kernel-iceland still needs;
- the initramfs carries the display, touch and GPU drivers and their firmware;
- Wi-Fi power saving is on;
- iceland-battery-guard enforces the stock 11.A.38 charging limits as a second layer over the charger firmware
  (temperature regions, per-region voltages and currents, the USB-C connector thermistors, 70/77 C power-off)
  and the charge limit: it follows the kernel's thresholds (GNOME's "Preserve Battery Health", 85 % / 80 %,
  switched on at the first installation) or, on a kernel without them, /etc/iceland/battery-guard.conf; it keeps
  the tablet awake while a charger is in (as stock does), writes what was plugged in to the journal, and takes
  the charge-current cap of iceland-thermal when that is lower than its own;
- iceland-thermal applies stock's skin temperature policy (20 temperature gears: CPU, GPU, brightness and
  charging limits per gear, GNOME's power modes as stock's mode offsets; /etc/iceland/thermal.conf). It only
  ever lowers limits; the kernel's thermal zones stay underneath. The shell temperature model is a private local
  file (/etc/iceland/thermal-model.json, never shipped); without it the battery temperature + 2 C stands in;
- kernel-iceland updates come from a local dnf repository (/var/lib/iceland/repo, filled by iceland-repo-sync);
- the panel runs 60 Hz on battery and 120 Hz on AC (iceland-refresh, /etc/iceland/refresh.conf); live
  refresh-rate changes need kernel queue patch 0058 (RELIGHT=1 switches the display off and on after every
  change, for older kernels only);
- the CDSP (NPU) stays off until `iceland-npu on`;
- the Wi-Fi regulatory country comes from /etc/iceland/wifi-country (written at install: the owner's country);
- sound: the Pad 4 AudioReach topology (TDM speakers, stream gain capped until speaker protection exists) and the
  ALSA UCM profile (speakers + internal microphones for PipeWire/GNOME);
- GNOME's power modes (tuned-ppd) map to Pad 4 profiles: schedutil with the frequency floors of stock's own
  schedutil fallback, Power Saver capped at stock's efficient-range edges (2.61 / 3.51 GHz) and the GPU below its
  TURBO levels, Performance with stock's higher floors and no pinning (iceland-power-profiles apply|reset|show).
- GNOME's About page and hostnamectl name the tablet "OnePlus Pad 4": /etc/machine-info gets HARDWARE_VENDOR,
  HARDWARE_MODEL and CHASSIS (systemd-hostnamed prefers them over the firmware's DMI strings, which U-Boot derives
  from the device tree as "oneplus" / "OnePlus Pad 4").
- auto-rotate and the other sensors behind the ADSP: a udev rule gives iio-sensor-proxy the accelerometer and the
  proximity sensor with the Pad 4 mount matrix and starts hexagonrpcd (sensors PD) and then iio-sensor-proxy when
  /dev/fastrpc-adsp appears; iio-sensor-proxy waits until the accelerometer answers; hexagonrpcd is started again
  after a suspend. Needs the tablet's own DSP file tree in /usr/share/qcom/kaanapali/OnePlus/iceland (extracted
  at install time, never shipped).

%prep
%setup -q -c -T
tar -xzf %{SOURCE20}
tar -xzf %{SOURCE21}
tar -xzf %{SOURCE22}

%build
# the Pad 4 AudioReach topology: upstream m4 + our overlay (TDM speakers, capped stream gain)
cp -a audio/topology/. audioreach-topology/
(cd audioreach-topology && m4 -I . OnePlus-Pad4.m4 > OnePlus-Pad4.conf && alsatplg -c OnePlus-Pad4.conf -o OnePlus-Pad4-tplg.bin)
grep -q 'max "2056"' audioreach-topology/OnePlus-Pad4.conf


%install
install -Dm0644 %{SOURCE0} %{buildroot}/usr/share/dnf5/libdnf.conf.d/80-iceland-kernel.conf
install -Dm0644 %{SOURCE60} %{buildroot}/usr/share/dnf5/repos.override.d/50-iceland-fedora-hold.repo
install -Dm0644 %{SOURCE61} %{buildroot}/usr/share/dnf5/repos.override.d/51-iceland-fedora-44-pin.repo
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
install -Dm0644 %{SOURCE24} %{buildroot}/etc/iceland/battery-guard.conf
install -Dm0755 %{SOURCE16} %{buildroot}/usr/bin/iceland-npu
install -Dm0644 %{SOURCE17} %{buildroot}/usr/lib/systemd/system/iceland-npu-off.service
install -Dm0755 %{SOURCE18} %{buildroot}/usr/libexec/iceland/iceland-wifi-country
install -Dm0644 %{SOURCE19} %{buildroot}/usr/lib/systemd/system/iceland-wifi-country.service
install -Dm0644 audioreach-topology/OnePlus-Pad4-tplg.bin %{buildroot}/usr/lib/firmware/qcom/kaanapali/OnePlus-Pad4-tplg.bin
install -Dm0644 audio/ucm/OnePlus-Pad4/OnePlus-Pad4.conf %{buildroot}/usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4/OnePlus-Pad4.conf
install -Dm0644 audio/ucm/OnePlus-Pad4/HiFi.conf %{buildroot}/usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4/HiFi.conf
install -d %{buildroot}/usr/share/alsa/ucm2/conf.d/kaanapali
ln -s ../../Qualcomm/kaanapali/OnePlus-Pad4/OnePlus-Pad4.conf %{buildroot}/usr/share/alsa/ucm2/conf.d/kaanapali/oneplus-OnePlusPad4.conf
for p in iceland-balanced iceland-balanced-battery iceland-powersave iceland-performance; do
	install -Dm0644 tuned/$p/tuned.conf %{buildroot}/usr/lib/tuned/profiles/$p/tuned.conf
done
install -Dm0755 %{SOURCE23} %{buildroot}/usr/bin/iceland-power-profiles
install -d %{buildroot}/var/lib/iceland/repo/aarch64
install -d %{buildroot}/etc/iceland
install -Dm0644 %{SOURCE25} %{buildroot}/usr/share/iceland/machine-info
install -Dm0644 %{SOURCE26} %{buildroot}/usr/lib/udev/rules.d/81-iceland-ssc.rules
install -Dm0644 %{SOURCE27} %{buildroot}/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland.conf
install -Dm0644 %{SOURCE28} %{buildroot}/usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d/iceland.conf
install -Dm0755 %{SOURCE29} %{buildroot}/usr/libexec/iceland/iceland-ssc-wait
install -Dm0644 %{SOURCE30} %{buildroot}/usr/lib/systemd/system/iceland-ssc-resume.service
install -Dm0644 %{SOURCE31} %{buildroot}/usr/share/libcamera/ipa/simple/sc1320cs.yaml
install -Dm0644 %{SOURCE34} %{buildroot}/usr/share/libcamera/ipa/simple/sc820cs.yaml
install -Dm0644 %{SOURCE35} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/51-iceland-camera.conf
install -Dm0755 %{SOURCE36} %{buildroot}/usr/libexec/iceland/iceland-camera-focus
install -Dm0644 %{SOURCE37} %{buildroot}/usr/lib/systemd/system/iceland-camera-focus.service
install -Dm0644 %{SOURCE38} %{buildroot}/etc/iceland/camera-focus.conf
install -Dm0644 %{SOURCE39} %{buildroot}/usr/lib/udev/rules.d/71-iceland-dma-heap.rules
install -Dm0644 %{SOURCE32} %{buildroot}/usr/lib/udev/hwdb.d/61-iceland-battery.hwdb
install -Dm0644 %{SOURCE33} %{buildroot}/usr/lib/systemd/system/upower.service.d/iceland.conf
install -Dm0755 %{SOURCE50} %{buildroot}/usr/libexec/iceland/iceland-thermal
install -Dm0644 %{SOURCE51} %{buildroot}/usr/lib/systemd/system/iceland-thermal.service
install -Dm0644 %{SOURCE52} %{buildroot}/etc/iceland/thermal.conf
install -Dm0644 %{SOURCE53} %{buildroot}/usr/lib/systemd/logind.conf.d/60-iceland.conf

%posttrans
# kernel-iceland is the default kernel and new kernel-iceland versions become the default
cat > /etc/sysconfig/kernel <<'EOT'
# written by iceland-device
UPDATEDEFAULT=yes
DEFAULTKERNEL=kernel-iceland
EOT
/usr/libexec/iceland/iceland-cmdline || :
# a stale saved ALSA mixer state can route MultiMedia1 into back ends the ADSP can't open (pc-026 S12: GNOME showed
# only a Dummy Output); drop it once, the UCM FixedBootSequence then sets the routes at every boot
if [ ! -e /var/lib/iceland/.asound-state-reset ]; then
	rm -f /var/lib/alsa/asound.state
	mkdir -p /var/lib/iceland && touch /var/lib/iceland/.asound-state-reset
fi
systemctl enable iceland-battery-guard.service iceland-npu-off.service iceland-wifi-country.service iceland-ssc-resume.service iceland-camera-focus.service >/dev/null 2>&1 || :
# 0.16 had a unit that kept a sensor-hub sensor streaming for the cameras; the kernel keeps their bus connected now
systemctl stop iceland-ssc-hold.service >/dev/null 2>&1 || :
# the DMA heap permissions (71-iceland-dma-heap.rules) at once; a running WirePlumber keeps the heap it has open
# until the user's next login
if [ -d /run/systemd/system ]; then udevadm control --reload >/dev/null 2>&1 || :; udevadm trigger --action=add -s dma_heap >/dev/null 2>&1 || :; fi
# the skin temperature policy starts at boot, like the guard
systemctl enable iceland-thermal.service >/dev/null 2>&1 || :
# logind reads the cover settings again (a reload, not a restart: a restart would end the sessions)
if [ -d /run/systemd/system ]; then systemctl kill -s HUP systemd-logind.service >/dev/null 2>&1 || :; fi
# the charge limit starts switched on ("Preserve Battery Health": before 0.17 the guard's 85 % limit was always on).
# UPower's switch is seeded once; afterwards the file is UPower's own (GNOME Settings > Power). Exactly "1".
if [ ! -e /var/lib/upower/charging-threshold-status ]; then
	mkdir -p /var/lib/upower && printf 1 > /var/lib/upower/charging-threshold-status
	restorecon /var/lib/upower/charging-threshold-status >/dev/null 2>&1 || :
fi
# the charge-limit thresholds: rebuild the hardware database and let udev and UPower read it again
systemd-hwdb update >/dev/null 2>&1 || :
if [ -d /run/systemd/system ]; then udevadm control --reload >/dev/null 2>&1 || :; udevadm trigger -s power_supply >/dev/null 2>&1 || :; udevadm settle --timeout=5 >/dev/null 2>&1 || :; systemctl try-restart upower.service >/dev/null 2>&1 || :; fi
# a running guard or thermal policy takes the new version at once (both start at boot; an installation alone
# does not start them)
if [ -d /run/systemd/system ]; then systemctl daemon-reload >/dev/null 2>&1 || :; systemctl try-restart iceland-battery-guard.service iceland-thermal.service >/dev/null 2>&1 || :; fi
systemctl --global enable iceland-refresh.service >/dev/null 2>&1 || :
# GNOME's power modes -> the Pad 4 tuned profiles (edits tuned-ppd's mapping between marker lines)
/usr/bin/iceland-power-profiles apply >/dev/null 2>&1 || :
# an empty local repository, so dnf doesn't complain before the first iceland-repo-sync
[ -d /var/lib/iceland/repo/aarch64/repodata ] || createrepo_c -q /var/lib/iceland/repo/aarch64 || :
systemctl preset iceland-bdaddr.service >/dev/null 2>&1 || systemctl enable iceland-bdaddr.service >/dev/null 2>&1 || :
# the names GNOME's About page and hostnamectl show: add the Pad 4 keys to /etc/machine-info unless they are set
# (hostnamed prefers this file over the firmware's DMI strings); every other key stays as it is
mi=/etc/machine-info
[ -s "$mi" ] && [ -n "$(tail -c 1 "$mi")" ] && echo >> "$mi"
grep -v '^#' /usr/share/iceland/machine-info | while IFS= read -r kv; do
	k=$(echo "$kv" | cut -d= -f1); [ -n "$k" ] || continue
	grep -q "^$k=" "$mi" 2>/dev/null || echo "$kv" >> "$mi"
done
chmod 644 "$mi" 2>/dev/null; restorecon "$mi" >/dev/null 2>&1 || :

%triggerin -- fwupd
# fwupd plug-ins that could write boot code, EFI variables, the storage's own firmware (UFS = scsi) or GPIOs: off
f=/etc/fwupd/fwupd.conf
dis="uefi_capsule;uefi_dbx;uefi_db;uefi_kek;uefi_pk;uefi_mok;uefi_sbat;uefi_recovery;uefi_esrt;android_boot;scsi;emmc;mtd;nvme;gpio;vbe;bootupd"
if [ -f "$f" ]; then
	if grep -q '^DisabledPlugins=' "$f"; then
		cur=$(sed -n 's/^DisabledPlugins=//p' "$f" | head -n 1); new=$cur
		for p in $(echo "$dis" | tr ';' ' '); do case ";$new;" in *";$p;"*) ;; *) new="${new:+$new;}$p" ;; esac; done
		[ "$new" = "$cur" ] || sed -i "s/^DisabledPlugins=.*/DisabledPlugins=$new/" "$f"
	else
		sed -i "0,/^\[fwupd\]/s//[fwupd]\nDisabledPlugins=$dis/" "$f"
	fi
	# the daemon reads its configuration only when it starts (a running fwupd kept the old list in RAM run area-combo-55)
	systemctl try-restart fwupd.service >/dev/null 2>&1 || :
fi

%preun
[ "$1" -eq 0 ] && systemctl --global disable iceland-refresh.service >/dev/null 2>&1; [ "$1" -eq 0 ] && systemctl disable iceland-camera-focus.service iceland-ssc-resume.service iceland-wifi-country.service iceland-npu-off.service iceland-battery-guard.service iceland-bdaddr.service >/dev/null 2>&1 || :
# the thermal policy hands its limits back when it stops
[ "$1" -eq 0 ] && systemctl disable --now iceland-thermal.service >/dev/null 2>&1 || :
[ "$1" -eq 0 ] && /usr/bin/iceland-power-profiles reset >/dev/null 2>&1 || :

%files
/usr/share/dnf5/libdnf.conf.d/80-iceland-kernel.conf
/usr/share/dnf5/repos.override.d/50-iceland-fedora-hold.repo
/usr/share/dnf5/repos.override.d/51-iceland-fedora-44-pin.repo
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
%config(noreplace) /etc/iceland/battery-guard.conf
/usr/bin/iceland-npu
/usr/lib/systemd/system/iceland-npu-off.service
/usr/libexec/iceland/iceland-wifi-country
/usr/lib/systemd/system/iceland-wifi-country.service
/usr/lib/firmware/qcom/kaanapali/OnePlus-Pad4-tplg.bin
%dir /usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4
/usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4/OnePlus-Pad4.conf
/usr/share/alsa/ucm2/Qualcomm/kaanapali/OnePlus-Pad4/HiFi.conf
/usr/share/alsa/ucm2/conf.d/kaanapali/oneplus-OnePlusPad4.conf
/usr/lib/tuned/profiles/iceland-balanced/
/usr/lib/tuned/profiles/iceland-balanced-battery/
/usr/lib/tuned/profiles/iceland-powersave/
/usr/lib/tuned/profiles/iceland-performance/
/usr/bin/iceland-power-profiles
%dir /var/lib/iceland
%dir /var/lib/iceland/repo
%dir /var/lib/iceland/repo/aarch64
%dir /etc/iceland
%dir /usr/share/iceland
/usr/share/iceland/machine-info
/usr/lib/udev/rules.d/81-iceland-ssc.rules
%dir /usr/lib/systemd/system/iio-sensor-proxy.service.d
/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland.conf
%dir /usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d
/usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d/iceland.conf
/usr/libexec/iceland/iceland-ssc-wait
/usr/lib/systemd/system/iceland-ssc-resume.service
/usr/share/libcamera/ipa/simple/sc1320cs.yaml
/usr/share/libcamera/ipa/simple/sc820cs.yaml
/usr/share/wireplumber/wireplumber.conf.d/51-iceland-camera.conf
/usr/libexec/iceland/iceland-camera-focus
/usr/lib/systemd/system/iceland-camera-focus.service
%config(noreplace) /etc/iceland/camera-focus.conf
/usr/lib/udev/rules.d/71-iceland-dma-heap.rules
/usr/lib/udev/hwdb.d/61-iceland-battery.hwdb
%dir /usr/lib/systemd/system/upower.service.d
/usr/lib/systemd/system/upower.service.d/iceland.conf
/usr/libexec/iceland/iceland-thermal
/usr/lib/systemd/system/iceland-thermal.service
%config(noreplace) /etc/iceland/thermal.conf
/usr/lib/systemd/logind.conf.d/60-iceland.conf

%changelog
* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.17-1
- cameras: iceland-ssc-hold.service and its Wants= line are gone: the kernel keeps the level shifters of the
  camera bus on (queue 0084-0086; area-combo-44: both sensors answer with the sensor hub configured and idle)
- cameras: libcamera tuning files for the two sensors (black level 64 / 65 of 1023 from the stock camera
  characteristics) in /usr/share/libcamera/ipa/simple/
- cameras: a WirePlumber rule hides the raw video nodes of the camera subsystem (the two libcamera sources stay)
- cameras: iceland-camera-focus puts the rear camera's lens at a fixed position while it streams
  (/etc/iceland/camera-focus.conf, default 450 = stock's start position); needs the focus motor of queue 0087-0089
- cameras: 71-iceland-dma-heap.rules gives the CMA dma-heaps to root only, so that libcamera's software ISP in
  the desktop session allocates from the system heap: the 32 MiB CMA area does not hold GNOME Camera's four
  1080p buffers (area-combo-46: "dma-heap allocation failure", PipeWire "Format negotiation failed")
- Requires libcamera-ipa, pipewire-plugin-libcamera, xdg-desktop-portal-gnome, fuse3; Recommends snapshot,
  pipewire-gstreamer
- battery guard, one program from three candidates (the stock limits of 0.16 are unchanged, nothing is raised):
  the charge limit follows the kernel's charge_control thresholds when the kernel has them (GNOME's "Preserve
  Battery Health" decides; the config file's CHARGE_LIMIT / CHARGE_RESUME only on a kernel without; LIMIT_SOURCE);
  the install scriptlet switches "Preserve Battery Health" on once, so the 85 % limit stays on by default
- battery guard: awake while a charger is in, as on stock (a logind block on sleep, KEEP_AWAKE; "systemctl
  suspend -i" still suspends); the block covers the lid switch too unless logind only locks a closing cover with
  a charger in (BLOCK_LID_SWITCH=auto; "yes" = always); a journal line at plug-in, 10 s later, every 10 minutes
  and at unplug
  (type, VBUS, input current of its limit, battery, cap); charging stops until unplug when the measured input
  current stays above its limit (15 % + 50 mA, three readings)
- battery guard: takes the charge-current cap of iceland-thermal (/run/iceland/thermal-fcc-ma) when it is lower
  than its own; a cap file older than 60 s is ignored (THERMAL_CAP)
- iceland-thermal (new, enabled like the guard): stock's skin temperature gears as a daemon: CPU, GPU, brightness
  and charging limits per gear, GNOME's power modes as stock's mode offsets (/etc/iceland/thermal.conf). Without
  the private model file it runs on the battery temperature + 2 C. Shipped with OFFSET_BALANCED=-4 (nothing
  changes at idle while the kernel's skin loop is at 48 / 51 C) and CHARGE_SHIFT=0 (the charging cool-down never
  takes a negative offset). It writes only user space's frequency maxima, the backlight and its two files under
  /run/iceland: the kernel's cooling devices keep their own requests, so it cannot lift a kernel limit
- the cover (logind drop-in logind.conf.d/60-iceland.conf, wf/wake): closing it suspends on battery, with a charger
  in it locks the session and the screen goes dark but the tablet stays awake (the guard keeps watching the
  charge), with an external display it does nothing; logind reads it again at the installation (SIGHUP)
- install scriptlet: udev settles before UPower is restarted; a running guard / thermal policy is restarted on
  an update
- tests: test_battery_guard.py extended (thermal cap); new: test_guard_kernel_limit.py, test_guard_awake.py,
  test_thermal.py, test_spec.py, test_logind.py (wf/wake)
- dnf (workflow apps): excludes for every Fedora kernel flavour, dracut's rescue / generic images, akmods /
  dkms, fwupd's EFI binaries, bootupd, sdubby, systemd-boot and U-Boot images (append lists in libdnf5: other
  configuration files keep their own); protected: iceland-device, grub2-efi-aa64, shim-aa64; kernel-iceland is
  install-only (three versions kept)
- dnf: GRUB, shim, linux-firmware / *-firmware, iio-sensor-proxy, hexagonrpc and libssc are held against Fedora's
  repositories (repos.override.d/50-iceland-fedora-hold.repo)
- dnf: Fedora's repositories pinned to release 44 (repos.override.d/51-iceland-fedora-44-pin.repo): GNOME
  Software 50 upgrades through dnf5daemon, whose polkit actions do not tell a version upgrade from an update,
  so the PackageKit rule alone no longer blocks it
- fwupd: every plug-in that can write boot code, EFI variables, storage firmware or GPIOs is disabled

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.16-1
- cameras: iceland-ssc-hold.service keeps the accelerometer of the sensor hub streaming whenever iio-sensor-proxy
  runs (bound to it, pulled in by its drop-in): the control bus of both cameras is only connected to the SoC
  while a sensor of the hub streams (area-combo-24..35)
- charge limit: 61-iceland-battery.hwdb gives UPower the thresholds 80 / 85 % for "Preserve Battery Health"
  (the kernel side is the qcom_battmgr charge limit of kernel-iceland); the database is rebuilt and udev reloaded
  after the installation; a drop-in starts UPower after udev's first device scan, because UPower reads the
  thresholds only once (not yet proven at a real boot: the RAM sessions start UPower before the package is there)

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.15-1
- sensors / auto-rotate: 81-iceland-ssc.rules (the SSC accelerometer and proximity sensor for iio-sensor-proxy, the
  mount matrix "0, 1, 0; -1, 0, 0; 0, 0, -1" derived from stock, both services started by udev when
  /dev/fastrpc-adsp appears), drop-ins that start hexagonrpcd (sensors PD, the tablet's own DSP file tree) before
  iio-sensor-proxy, iceland-ssc-wait (waits until the accelerometer delivers a sample; area-combo-17: 2.5 s),
  iceland-ssc-resume.service (hexagonrpcd again after a suspend); requires hexagonrpc, libssc and
  iio-sensor-proxy >= 3.9-10 (packaging/sensors)

* Thu Oct 01 2026 mzak <mzak.amin@gmail.com> - 0.14-1
- /etc/machine-info: HARDWARE_VENDOR=OnePlus, HARDWARE_MODEL="Pad 4", CHASSIS=tablet (the missing keys are added at
  install from /usr/share/iceland/machine-info): GNOME's About page and hostnamectl show "OnePlus Pad 4" instead of
  the firmware's "oneplus OnePlus Pad 4" (stock: ro.product.manufacturer OnePlus, market name OnePlus Pad 4)
- GNOME power modes: Balanced uses stock's floors for SoC revision 2.0 (787200 / 864000 kHz), Performance turns
  on the big cores' turbo steps (up to 4608000 kHz, stock's maximum); Power Saver unchanged (area-combo-11:
  the three modes switch as the GNOME user and give three sets of limits)
- iceland-npu-off.service starts /usr/bin/iceland-npu (the path the package installs)

* Thu Oct 01 2026 mzak <mzak.amin@gmail.com> - 0.13-1
- UCM: microphone TX decimator volume 96 (+12 dB): the mic now matches stock's recorder level for the same sound
  (stock adds the gain in its DSP; area-combo-1..3). GNOME's input meter moves with speech

* Wed Sep 30 2026 mzak <mzak.amin@gmail.com> - 0.12-1
- iceland-refresh: RELIGHT off by default - kernel queue patch 0058 (drm/msm/dpu: no CTL_START in the video
  encoder's cleanup) keeps the picture on every live refresh-rate change (area-display-7: 11 of 11 on camera);
  RELIGHT=1 stays available for kernels without it
* Wed Sep 30 2026 mzak <mzak.amin@gmail.com> - 0.11-1
- battery guard: power off at 70 C (stock framework high-temperature shutdown, before the DT's 72 C); read the
  USB-C connector on the usb-temp-l / usb-temp-r / usb-therm zones (the hottest valid reading; stock's protection
  reads the L/R pair); charge limit 85 %, resume at 80 % (/etc/iceland/battery-guard.conf, CHARGE_LIMIT=100 = off)
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.10-1
- power profiles: GNOME's power modes (tuned-ppd) map to iceland-balanced / -balanced-battery / -powersave /
  -performance - schedutil with stock's frequency floors (614400/864000 kHz), Power Saver capped at stock's
  efficient-range edges (2611200 / 3513600 kHz) and the GPU at 902 MHz, Performance with stock's higher floors
  (787200/864000 kHz); iceland-power-profiles apply|reset|show edits tuned-ppd's mapping (requires tuned-ppd)
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.9-1
- iceland-refresh: relight the panel after every refresh-rate change of the built-in panel (one display off/on
  through mutter's PowerSaveMode, coalesced over a burst of changes; RELIGHT, RELIGHT_OFF_MS) - a live rate change
  leaves the panel black until an off/on (area-display-2/3)
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.8-1
- battery guard: retry failed writes (cache only on success), re-assert charge_behaviour every step, stop on an
  unreadable battery voltage, on VBUS above 11 V (stock OV) and on a 3 C connector rise in one step (stock
  rise_fast_temp); log the missing inputs at start and every 5 min while plugged (offline review B8/B9/B11)
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.7-1
- drop a stale /var/lib/alsa/asound.state once (it broke the speaker route, pc-026 S12); UCM switches stray routes off
* Tue Sep 29 2026 mzak <mzak.amin@gmail.com> - 0.6-1
- ship the Pad 4 topology (built from m4, speaker gain capped) and the UCM profile
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
