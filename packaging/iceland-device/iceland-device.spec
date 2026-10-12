# SPDX-License-Identifier: GPL-2.0-or-later
#
# iceland-device: Fedora settings for the OnePlus Pad 4 (iceland) running kernel-iceland.
# No firmware and no binaries: configuration files and small scripts only.

Name:           iceland-device
Version:        0.28
Release:        2%{?dist}
Summary:        OnePlus Pad 4 (iceland) device settings for Fedora
License:        GPL-2.0-or-later AND BSD-3-Clause
URL:            https://github.com/mzakamin-hub/iceland-mainline
BuildArch:      noarch
BuildRequires:  m4
BuildRequires:  alsa-utils
# alsatplg (Fedora ships it apart from alsa-utils)
BuildRequires:  alsa-topology-utils
# the SELinux module (checkmodule, semodule_package)
BuildRequires:  checkpolicy
BuildRequires:  policycoreutils
Requires(post): policycoreutils
Requires(postun): policycoreutils
Source0:        80-iceland-kernel.conf
# Fedora's repositories: GRUB, shim, firmware and the sensor programs held; the release pinned (dnf5 repository
# overrides; an empty file of the same name in /etc/dnf/repos.override.d masks either)
Source60:       50-iceland-fedora-hold.repo
Source61:       51-iceland-fedora-44-pin.repo
# install plan (wf/install): read-only internal storage, the root inside userdata, snapshots, trial boots
Source62:       59-iceland-storage-ro.rules
Source63:       iceland-storage-ro
Source64:       dracut-iceland-module-setup.sh
Source65:       dracut-iceland-carrier
Source66:       dracut-iceland-rehearsal
Source67:       dracut-iceland-rollback
Source68:       dracut-iceland-carrier.unit
Source69:       dracut-iceland-rollback.unit
Source70:       91-iceland-install-dracut.conf
Source71:       iceland-snapshot
Source72:       iceland-snapshot.actions
Source73:       snapshot.conf
Source74:       96-iceland-trial.install
Source75:       iceland-trial
Source76:       iceland-trial-early.service
Source77:       iceland-boot-confirm.service
Source78:       iceland-grub-setup
Source79:       boot.conf
Source80:       iceland-protected.conf
Source81:       iceland-fwupd-guard
# charging safety (wf/chgsafe): the GNOME user service that shows the guard's safety stops as desktop notifications
Source82:       iceland-charge-alert
Source83:       iceland-charge-alert.service
# systemd preset (wf/fedtest): keeps the iceland units enabled through the first boot's preset-all
Source106:      50-iceland.preset
# storage: the UFS LUNs' I/O scheduler one LUN at a time (r2g: parallel writes got -EBUSY)
Source107:      60-block-scheduler.rules
Source108:      61-iceland-ufs-scheduler.rules
Source109:      iceland-ufs-scheduler
# sensors: the DSP file tree readable by group fastrpc (hexagonrpcd's user)
Source110:      iceland-dsp-tree.conf
# SELinux (wf/fedtest): iio-sensor-proxy's QRTR socket to the sensor hub (R2 enforcing: no rotation without it)
Source105:      iceland_sensors.te
# sound at boot (wf/fedtest): shadows alsa-lib's modprobe install hook that fails without a sequencer
Source104:      dist-alsa.conf
# the persistent clock (wf/fedtest): the PMIC RTC cannot be set; PID 1 restores the clock from the mtime of
# /var/lib/systemd/timesync/clock at boot, and these keep that stamp current (timer + shutdown)
Source100:      iceland-clock
Source101:      iceland-clock.service
Source102:      iceland-clock.timer
Source103:      iceland-clock-save.service
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
Source111:       iceland-regdomain
# bypass charging (wf/bypass): the Quick Settings toggle (a GNOME Shell extension), its D-Bus service with the
# polkit action, and the guard's bypass rule (iceland-battery-guard, battery-guard.conf)
Source112:      iceland-bypassd
Source113:      iceland-bypass.service
Source114:      org.iceland.Bypass.service
Source115:      org.iceland.Bypass.conf
Source116:      org.iceland.bypass.policy
Source117:      bypass-extension.js
Source118:      bypass-metadata.json
Source119:      zz_iceland-device.gschema.override
# the processed microphone (owner, 9 Oct 2026): PipeWire's echo-cancel with the WebRTC backend (pipewire-libs ships
# aec/libspa-aec-webrtc.so); fail-safe: a module that does not load leaves the raw UCM source the default
Source120:      60-iceland-mic-processing.conf
# update policy (0.24): read-only list of the upgrades offered, held back by the hold file and skipped by the resolver
Source121:      iceland-update-check
# platform defaults (0.26, from the tb323fu-linux review): no USB / PCIe wakeup, the GPU floor at boot, the sensor
# stream stopped across a suspend, systemd feeds the hardware watchdog
Source122:      72-iceland-nowake.rules
Source123:      73-iceland-gpu-devfreq.rules
Source124:      iceland-sensors-sleep
Source125:      iio-sensor-proxy-iceland-sleep.conf
Source126:      watchdog-iceland.conf
# speaker protection (0.27, from the tb323fu-linux review): a filter chain that only takes level away
Source127:      62-iceland-speakers.conf
Source128:      62-iceland-speaker-raw.conf
# Wi-Fi address kept stable across boots (0.27): changes nothing while the firmware's address is stable
Source129:      iceland-wifi-mac
Source130:      74-iceland-wifi-mac.rules
Source131:      iceland-wifi-mac-check.service
# 0.27r5: mark the Android A/B slot successful after a good boot (qbootctl -m; never in a RAM kit / rehearsal)
Source132:      iceland-slot-mark
Source133:      iceland-slot-mark.service

Requires:       kernel-iceland
Requires:       bluez
Requires:       python3
Requires:       python3-gobject
Requires:       polkit
Requires:       createrepo_c
Requires:       curl
Requires:       iw
Requires:       ethtool
Requires:       qbootctl
Requires:       iproute
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
# 51-iceland-camera.conf disables a V4L2 device: WirePlumber 0.5.16 / 0.5.17 then stall their event dispatcher (no camera
# source); fixed upstream in 0.5.18 (65519a1, wf/gpuisp)
Requires:       wireplumber >= 0.5.18
Requires:       ladspa-swh-plugins
Requires:       xdg-desktop-portal-gnome
Requires:       fuse3
Requires:       btrfs-progs
Requires:       libdnf5-plugin-actions
Requires:       grub2-tools
Requires:       util-linux
Requires:       nbd
Requires:       busybox
Recommends:     snapshot
# F1 (wf/fedtest, r2g 3 Oct 2026): GNOME Snapshot died with SIGBUS in pipewire 1.6.2's GStreamer device provider
# (libgstpipewire re-adds its metadata listener when the portal re-announces the default metadata); fixed upstream
# in PipeWire 1.6.8 (gst: device-provider: don't re-add metadata listener on permission change). The floor pulls
# Fedora 44's pipewire update (1.6.9) into the image; pipewire-libs moves with it (exact-version subpackages).
Requires:       pipewire-gstreamer >= 1.6.8
Requires:       pipewire-libs >= 1.6.8
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
  the charge-current cap of iceland-thermal when that is lower than its own; at a USB-C connector stop (too hot,
  far above the battery, warming fast) and at an input over-limit stop it also switches the charger input off
  through kernel-iceland's qcom-battmgr-usb/input_current_limit (as stock's connector protection does: the tablet
  runs from its battery, nothing flows through the hot connector; back once the cable is out and the connector
  is below 55 C), and the GNOME session shows every safety stop and its end as a desktop notification
  (iceland-charge-alert, a user service reading /run/iceland/charge-alert: no privilege path);
- iceland-thermal applies stock's skin temperature policy (20 temperature gears: CPU, GPU, brightness and
  charging limits per gear, GNOME's power modes as stock's mode offsets; /etc/iceland/thermal.conf). It only
  ever lowers limits; the kernel's thermal zones stay underneath. The shell temperature model is a private local
  file (/etc/iceland/thermal-model.json, never shipped); without it the battery temperature + 2 C stands in;
- kernel-iceland updates come from a local dnf repository (/var/lib/iceland/repo, filled by iceland-repo-sync);
- the panel runs 60 Hz on battery and 120 Hz on AC (iceland-refresh, /etc/iceland/refresh.conf); live
  refresh-rate changes need kernel queue patch 0058 (RELIGHT=1 switches the display off and on after every
  change, for older kernels only);
- the CDSP (NPU) runs from boot and idles by itself; the boot-time stop (iceland-npu-off.service) is opt-in
  through /etc/iceland/npu-off-at-boot, because a stopped CDSP keeps the SoC out of CX collapse in suspend
  until it runs again (iceland-npu on|off|status);
- the Wi-Fi regulatory country comes from /etc/iceland/wifi-country (written at install: the owner's country);
- the clock survives reboots without a settable RTC: iceland-clock keeps the mtime of
  /var/lib/systemd/timesync/clock current (every 15 min and at shutdown); systemd's PID 1 takes it as the lower bound
  of the system time at boot, so rpm's signature checks and TLS work before the first NTP sync
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
- bypass charging, as stock's: a "Bypass Charging" toggle in GNOME's Quick Settings (threshold from 20 %); with a
  charger in, charging stops at the threshold and the tablet runs from the charger, the level held within 1 % by
  iceland-battery-guard; it ends at unplug, at a charger-input safety stop and 5 minutes after the toggle stops
  renewing it (screen locked), and every charging limit still applies (iceland-bypassd, polkit
  org.iceland.bypass.set: the user at the tablet).

%prep
%setup -q -c -T
tar -xzf %{SOURCE20}
tar -xzf %{SOURCE21}
tar -xzf %{SOURCE22}

%build
# the sensors' SELinux module (raw module syntax, no policy headers needed)
checkmodule -M -m -o iceland_sensors.mod %{SOURCE105}
semodule_package -o iceland_sensors.pp -m iceland_sensors.mod
# the Pad 4 AudioReach topology: upstream m4 + our overlay (TDM speakers, capped stream gain)
cp -a audio/topology/. audioreach-topology/
(cd audioreach-topology && m4 -I . OnePlus-Pad4.m4 > OnePlus-Pad4.conf && alsatplg -c OnePlus-Pad4.conf -o OnePlus-Pad4-tplg.bin)
grep -q 'max "8192"' audioreach-topology/OnePlus-Pad4.conf


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
install -Dm0644 %{SOURCE111} %{buildroot}/etc/sysconfig/regdomain
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
install -Dm0644 %{SOURCE110} %{buildroot}/usr/lib/tmpfiles.d/iceland-dsp-tree.conf
install -Dm0755 %{SOURCE29} %{buildroot}/usr/libexec/iceland/iceland-ssc-wait
install -Dm0644 %{SOURCE30} %{buildroot}/usr/lib/systemd/system/iceland-ssc-resume.service
install -Dm0644 %{SOURCE31} %{buildroot}/usr/share/libcamera/ipa/simple/sc1320cs.yaml
install -Dm0644 %{SOURCE34} %{buildroot}/usr/share/libcamera/ipa/simple/sc820cs.yaml
install -Dm0644 %{SOURCE107} %{buildroot}/etc/udev/rules.d/60-block-scheduler.rules
install -Dm0644 %{SOURCE108} %{buildroot}/usr/lib/udev/rules.d/61-iceland-ufs-scheduler.rules
install -Dm0755 %{SOURCE109} %{buildroot}/usr/libexec/iceland/iceland-ufs-scheduler
install -Dm0644 %{SOURCE35} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/51-iceland-camera.conf
install -Dm0755 %{SOURCE36} %{buildroot}/usr/libexec/iceland/iceland-camera-focus
install -Dm0644 %{SOURCE37} %{buildroot}/usr/lib/systemd/system/iceland-camera-focus.service
install -Dm0644 %{SOURCE38} %{buildroot}/etc/iceland/camera-focus.conf
install -Dm0644 %{SOURCE39} %{buildroot}/usr/lib/udev/rules.d/71-iceland-dma-heap.rules
install -Dm0644 %{SOURCE32} %{buildroot}/usr/lib/udev/hwdb.d/61-iceland-battery.hwdb
install -Dm0644 %{SOURCE33} %{buildroot}/usr/lib/systemd/system/upower.service.d/iceland.conf
install -Dm0755 %{SOURCE50} %{buildroot}/usr/libexec/iceland/iceland-thermal
install -Dm0644 %{SOURCE51} %{buildroot}/usr/lib/systemd/system/iceland-thermal.service
install -Dm0644 %{SOURCE106} %{buildroot}/usr/lib/systemd/system-preset/50-iceland.preset
install -Dm0644 iceland_sensors.pp %{buildroot}/usr/share/selinux/packages/iceland/iceland_sensors.pp
install -Dm0644 %{SOURCE105} %{buildroot}/usr/share/selinux/packages/iceland/iceland_sensors.te
install -Dm0644 %{SOURCE104} %{buildroot}/etc/modprobe.d/dist-alsa.conf
install -Dm0755 %{SOURCE100} %{buildroot}/usr/libexec/iceland/iceland-clock
install -Dm0644 %{SOURCE101} %{buildroot}/usr/lib/systemd/system/iceland-clock.service
install -Dm0644 %{SOURCE102} %{buildroot}/usr/lib/systemd/system/iceland-clock.timer
install -Dm0644 %{SOURCE103} %{buildroot}/usr/lib/systemd/system/iceland-clock-save.service
install -Dm0644 %{SOURCE52} %{buildroot}/etc/iceland/thermal.conf
install -Dm0644 %{SOURCE53} %{buildroot}/usr/lib/systemd/logind.conf.d/60-iceland.conf

install -Dm0644 %{SOURCE62} %{buildroot}/usr/lib/udev/rules.d/59-iceland-storage-ro.rules
install -Dm0755 %{SOURCE63} %{buildroot}/usr/libexec/iceland/iceland-storage-ro
install -Dm0755 %{SOURCE64} %{buildroot}/usr/lib/dracut/modules.d/90iceland/module-setup.sh
install -Dm0755 %{SOURCE65} %{buildroot}/usr/lib/dracut/modules.d/90iceland/iceland-carrier
install -Dm0755 %{SOURCE66} %{buildroot}/usr/lib/dracut/modules.d/90iceland/iceland-rehearsal
install -Dm0755 %{SOURCE67} %{buildroot}/usr/lib/dracut/modules.d/90iceland/iceland-rollback
install -Dm0644 %{SOURCE68} %{buildroot}/usr/lib/dracut/modules.d/90iceland/iceland-carrier.service
install -Dm0644 %{SOURCE69} %{buildroot}/usr/lib/dracut/modules.d/90iceland/iceland-rollback.service
install -Dm0644 %{SOURCE70} %{buildroot}/usr/lib/dracut/dracut.conf.d/91-iceland-install.conf
install -Dm0755 %{SOURCE71} %{buildroot}/usr/libexec/iceland/iceland-snapshot
install -Dm0644 %{SOURCE72} %{buildroot}/etc/dnf/libdnf5-plugins/actions.d/iceland-snapshot.actions
install -Dm0644 %{SOURCE73} %{buildroot}/etc/iceland/snapshot.conf
install -Dm0755 %{SOURCE74} %{buildroot}/usr/lib/kernel/install.d/96-iceland-trial.install
install -Dm0755 %{SOURCE75} %{buildroot}/usr/libexec/iceland/iceland-trial
install -Dm0644 %{SOURCE76} %{buildroot}/usr/lib/systemd/system/iceland-trial-early.service
install -Dm0644 %{SOURCE77} %{buildroot}/usr/lib/systemd/system/iceland-boot-confirm.service
install -Dm0755 %{SOURCE78} %{buildroot}/usr/libexec/iceland/iceland-grub-setup
install -Dm0644 %{SOURCE79} %{buildroot}/etc/iceland/boot.conf
install -Dm0644 %{SOURCE80} %{buildroot}/etc/dnf/protected.d/iceland-device.conf
install -Dm0755 %{SOURCE81} %{buildroot}/usr/libexec/iceland/iceland-fwupd-guard
install -Dm0755 %{SOURCE82} %{buildroot}/usr/libexec/iceland/iceland-charge-alert
install -Dm0644 %{SOURCE83} %{buildroot}/usr/lib/systemd/user/iceland-charge-alert.service
install -Dm0755 %{SOURCE112} %{buildroot}/usr/libexec/iceland/iceland-bypassd
install -Dm0644 %{SOURCE113} %{buildroot}/usr/lib/systemd/system/iceland-bypass.service
install -Dm0644 %{SOURCE114} %{buildroot}/usr/share/dbus-1/system-services/org.iceland.Bypass.service
install -Dm0644 %{SOURCE115} %{buildroot}/usr/share/dbus-1/system.d/org.iceland.Bypass.conf
install -Dm0644 %{SOURCE116} %{buildroot}/usr/share/polkit-1/actions/org.iceland.bypass.policy
install -Dm0644 %{SOURCE117} %{buildroot}/usr/share/gnome-shell/extensions/iceland-bypass@oneplus-pad4/extension.js
install -Dm0644 %{SOURCE118} %{buildroot}/usr/share/gnome-shell/extensions/iceland-bypass@oneplus-pad4/metadata.json
install -Dm0644 %{SOURCE119} %{buildroot}/usr/share/glib-2.0/schemas/zz_iceland-device.gschema.override
install -Dm0644 %{SOURCE120} %{buildroot}/usr/share/pipewire/pipewire.conf.d/60-iceland-mic-processing.conf
install -Dm0755 %{SOURCE121} %{buildroot}/usr/bin/iceland-update-check
install -Dm0644 %{SOURCE122} %{buildroot}/usr/lib/udev/rules.d/72-iceland-nowake.rules
install -Dm0644 %{SOURCE123} %{buildroot}/usr/lib/udev/rules.d/73-iceland-gpu-devfreq.rules
install -Dm0755 %{SOURCE124} %{buildroot}/usr/lib/systemd/system-sleep/iceland-sensors
install -Dm0644 %{SOURCE125} %{buildroot}/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland-sleep.conf
install -Dm0644 %{SOURCE126} %{buildroot}/usr/lib/systemd/system.conf.d/60-iceland-watchdog.conf
install -Dm0644 %{SOURCE127} %{buildroot}/usr/share/pipewire/pipewire.conf.d/62-iceland-speakers.conf
install -Dm0644 %{SOURCE128} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/62-iceland-speaker-raw.conf
install -Dm0755 %{SOURCE129} %{buildroot}/usr/libexec/iceland/iceland-wifi-mac
install -Dm0644 %{SOURCE130} %{buildroot}/usr/lib/udev/rules.d/74-iceland-wifi-mac.rules
install -Dm0644 %{SOURCE131} %{buildroot}/usr/lib/systemd/system/iceland-wifi-mac-check.service
install -Dm0755 %{SOURCE132} %{buildroot}/usr/libexec/iceland/iceland-slot-mark
install -Dm0644 %{SOURCE133} %{buildroot}/usr/lib/systemd/system/iceland-slot-mark.service
install -d %{buildroot}/var/lib/iceland/trial

%posttrans
# install plan: GRUB settings (per-kernel device tree, visible menu, $iceland_args), trial-boot units, udev
/usr/libexec/iceland/iceland-grub-setup || :
systemctl enable iceland-trial-early.service iceland-boot-confirm.service >/dev/null 2>&1 || :
systemctl enable iceland-slot-mark.service >/dev/null 2>&1 || :
[ -d /run/systemd/system ] && udevadm control --reload >/dev/null 2>&1 || :
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
# 0.26: the wakeup defaults (72-iceland-nowake.rules) and the GPU floor (73-iceland-gpu-devfreq.rules) at once; the
# watchdog drop-in (system.conf.d) takes effect at the next boot
if [ -d /run/systemd/system ]; then udevadm trigger --action=change -s devfreq -s pci >/dev/null 2>&1 || :; udevadm trigger --action=change -s platform --sysname-match=a600000.usb >/dev/null 2>&1 || :; fi
# the skin temperature policy starts at boot, like the guard
systemctl enable iceland-thermal.service >/dev/null 2>&1 || :
# the sensors' SELinux module: into the policy store; loaded at once on a booted system, else at the next boot
if [ -d /run/systemd/system ] && [ -e /sys/fs/selinux/enforce ]; then semodule -i /usr/share/selinux/packages/iceland/iceland_sensors.pp >/dev/null 2>&1 || :
else semodule -n -i /usr/share/selinux/packages/iceland/iceland_sensors.pp >/dev/null 2>&1 || :; fi
# the persistent clock: enabled here (no Fedora preset names it); the stamp is saved once now if the clock is trusted
systemctl enable iceland-clock.service iceland-clock.timer >/dev/null 2>&1 || :
[ -d /run/systemd/system ] && /usr/libexec/iceland/iceland-clock save >/dev/null 2>&1 || :
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
systemctl --global enable iceland-refresh.service iceland-charge-alert.service >/dev/null 2>&1 || :
# bypass charging: the bus reads the D-Bus policy of iceland-bypassd again (the service starts on demand); a running
# one takes the new version. polkit sees the new action by itself; the GSettings override is compiled by glib2's
# file trigger; GNOME Shell loads the extension at the next login.
if [ -d /run/systemd/system ]; then systemctl reload dbus-broker.service >/dev/null 2>&1 || systemctl reload dbus.service >/dev/null 2>&1 || :; systemctl try-restart iceland-bypass.service >/dev/null 2>&1 || :; fi
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
/usr/libexec/iceland/iceland-fwupd-guard || :
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
[ "$1" -eq 0 ] && systemctl disable iceland-trial-early.service iceland-boot-confirm.service >/dev/null 2>&1 || :
[ "$1" -eq 0 ] && systemctl disable iceland-slot-mark.service >/dev/null 2>&1 || :
[ "$1" -eq 0 ] && systemctl --global disable iceland-refresh.service iceland-charge-alert.service >/dev/null 2>&1; [ "$1" -eq 0 ] && systemctl disable iceland-camera-focus.service iceland-ssc-resume.service iceland-wifi-country.service iceland-npu-off.service iceland-battery-guard.service iceland-bdaddr.service >/dev/null 2>&1 || :
# the thermal policy hands its limits back when it stops
[ "$1" -eq 0 ] && systemctl disable --now iceland-thermal.service >/dev/null 2>&1 || :
if [ "$1" -eq 0 ]; then if [ -d /run/systemd/system ] && [ -e /sys/fs/selinux/enforce ]; then semodule -r iceland_sensors >/dev/null 2>&1 || :; else semodule -n -r iceland_sensors >/dev/null 2>&1 || :; fi; fi
[ "$1" -eq 0 ] && systemctl disable --now iceland-clock.timer iceland-clock.service >/dev/null 2>&1 || :
[ "$1" -eq 0 ] && /usr/bin/iceland-power-profiles reset >/dev/null 2>&1 || :
# bypass charging ends with the package (the running guard gives charging back at its next step)
[ "$1" -eq 0 ] && { systemctl stop iceland-bypass.service >/dev/null 2>&1; rm -f /run/iceland/bypass-request; } || :

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
/usr/bin/iceland-update-check
/usr/lib/udev/rules.d/72-iceland-nowake.rules
/usr/lib/udev/rules.d/73-iceland-gpu-devfreq.rules
/usr/lib/systemd/system-sleep/iceland-sensors
/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland-sleep.conf
/usr/lib/systemd/system.conf.d/60-iceland-watchdog.conf
/usr/share/pipewire/pipewire.conf.d/62-iceland-speakers.conf
/usr/share/wireplumber/wireplumber.conf.d/62-iceland-speaker-raw.conf
/usr/libexec/iceland/iceland-wifi-mac
/usr/lib/udev/rules.d/74-iceland-wifi-mac.rules
/usr/lib/systemd/system/iceland-wifi-mac-check.service
/usr/libexec/iceland/iceland-slot-mark
/usr/lib/systemd/system/iceland-slot-mark.service
/usr/lib/systemd/system/iceland-npu-off.service
/usr/libexec/iceland/iceland-wifi-country
/usr/lib/systemd/system/iceland-wifi-country.service
%config(noreplace) /etc/sysconfig/regdomain
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
/usr/lib/tmpfiles.d/iceland-dsp-tree.conf
/usr/libexec/iceland/iceland-ssc-wait
/usr/lib/systemd/system/iceland-ssc-resume.service
/usr/share/libcamera/ipa/simple/sc1320cs.yaml
/usr/share/libcamera/ipa/simple/sc820cs.yaml
%config(noreplace) /etc/udev/rules.d/60-block-scheduler.rules
/usr/lib/udev/rules.d/61-iceland-ufs-scheduler.rules
/usr/libexec/iceland/iceland-ufs-scheduler
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
/usr/lib/systemd/system-preset/50-iceland.preset
%dir /usr/share/selinux/packages/iceland
/usr/share/selinux/packages/iceland/iceland_sensors.pp
/usr/share/selinux/packages/iceland/iceland_sensors.te
%config(noreplace) /etc/modprobe.d/dist-alsa.conf
/usr/libexec/iceland/iceland-clock
/usr/lib/systemd/system/iceland-clock.service
/usr/lib/systemd/system/iceland-clock.timer
/usr/lib/systemd/system/iceland-clock-save.service
%config(noreplace) /etc/iceland/thermal.conf
/usr/lib/systemd/logind.conf.d/60-iceland.conf

%dir /usr/lib/dracut/modules.d/90iceland
%dir /etc/dnf/libdnf5-plugins/actions.d
%dir /var/lib/iceland/trial
/usr/lib/udev/rules.d/59-iceland-storage-ro.rules
/usr/libexec/iceland/iceland-storage-ro
/usr/lib/dracut/modules.d/90iceland/module-setup.sh
/usr/lib/dracut/modules.d/90iceland/iceland-carrier
/usr/lib/dracut/modules.d/90iceland/iceland-rehearsal
/usr/lib/dracut/modules.d/90iceland/iceland-rollback
/usr/lib/dracut/modules.d/90iceland/iceland-carrier.service
/usr/lib/dracut/modules.d/90iceland/iceland-rollback.service
/usr/lib/dracut/dracut.conf.d/91-iceland-install.conf
/usr/libexec/iceland/iceland-snapshot
%config(noreplace) /etc/dnf/libdnf5-plugins/actions.d/iceland-snapshot.actions
%config(noreplace) /etc/iceland/snapshot.conf
/usr/lib/kernel/install.d/96-iceland-trial.install
/usr/libexec/iceland/iceland-trial
/usr/lib/systemd/system/iceland-trial-early.service
/usr/lib/systemd/system/iceland-boot-confirm.service
/usr/libexec/iceland/iceland-grub-setup
%config(noreplace) /etc/iceland/boot.conf
%config(noreplace) /etc/dnf/protected.d/iceland-device.conf
/usr/libexec/iceland/iceland-fwupd-guard
/usr/libexec/iceland/iceland-charge-alert
/usr/lib/systemd/user/iceland-charge-alert.service
/usr/libexec/iceland/iceland-bypassd
/usr/lib/systemd/system/iceland-bypass.service
/usr/share/dbus-1/system-services/org.iceland.Bypass.service
/usr/share/dbus-1/system.d/org.iceland.Bypass.conf
/usr/share/polkit-1/actions/org.iceland.bypass.policy
%dir /usr/share/gnome-shell/extensions/iceland-bypass@oneplus-pad4
/usr/share/gnome-shell/extensions/iceland-bypass@oneplus-pad4/extension.js
/usr/share/gnome-shell/extensions/iceland-bypass@oneplus-pad4/metadata.json
/usr/share/glib-2.0/schemas/zz_iceland-device.gschema.override
/usr/share/pipewire/pipewire.conf.d/60-iceland-mic-processing.conf

%changelog
* Sun Oct 11 2026 mzak <mzak.amin@gmail.com> - 0.28-2
- bluetooth: iceland-bdaddr v2 - a real power-on, power-off, then the own address, then wait for the index to come back
  with it (v1 set the address inside the kernel's 2 s auto-off window after the controller setup; with bluez 5.87
  the hci0 index then never came back: no powered controller for the whole boot, r139 / r139a); new test_bdaddr.py

* Sun Oct 11 2026 mzak <mzak.amin@gmail.com> - 0.28-1
- final release for the install image: the content of the rehearsed 0.27r6 tarball (sha256 7c1273d8) unchanged,
  only the version raised; rehearsal tarballs 0.28rN map to Release N from now on

* Sat Oct 10 2026 mzak <mzak.amin@gmail.com> - 0.27-1
- speakers: protection in PipeWire (62-iceland-speakers.conf, adapted from tb323fu-linux, MIT): the sink
  "Speakers" runs a 150 Hz 4th-order high-pass, a gentle compressor (0 dB makeup) and a
  -3 dBFS look-ahead limiter (-3 dB input gain, 250 ms release) in front of the speaker; every stage only takes level away and the topology / UCM DSP cap
  (0 dB = stock's stream ceiling) stays the hard ceiling. The direct speaker sink stays as "Speakers (direct, no protection filter)" with a low
  priority (62-iceland-speaker-raw.conf). Fail-safe (ifexists nofail; Requires ladspa-swh-plugins); off switch:
  context.properties = { iceland.speaker-protection = false } in a pipewire.conf.d drop-in
- wifi: a stable Wi-Fi address (iceland-wifi-mac, 74-iceland-wifi-mac.rules, iceland-wifi-mac-check.service): nothing
  changes while the firmware's address is stable; a fixed locally administered address from the machine id once it
  changed between boots (or is marked random), or the installer's /etc/iceland/wifimac; only a salted hash of the
  firmware's address is stored; off switch /etc/iceland/wifimac-keep
- boot: iceland-slot-mark.service marks the Android A/B slot successful (qbootctl -m, Requires qbootctl) once the
  desktop is up (system running / degraded, graphical.target active, +30 s), only when it is not marked yet; it skips
  with a log line in install rehearsals (iceland.rehearsal=), with iceland.noslotmark or /etc/iceland/slot-mark-off,
  and when / is not on the tablet's storage (RAM kits, NBD); iceland-slot-mark --dry-run / status only read
- speakers (0.27r6, owner 11 Oct): the DSP stream cap is stock's ceiling, 0 dB (Q13 8192; was the -12 dB placeholder
  2056): topology VOL_CTRL_MAX and the UCM pin; the chain's slow RMS cap (10:1 over -16 dBFS) is gone (one limiting
  stage). Microphone unchanged at stock (ADC1/2 14, TX_DEC0/1 98 = stock's 84 + its 14 dB DSP recorder gain).
  Every gain is at or below its stock counterpart (tests/test_stock_levels.py)
- tests: test_speaker_protection.py, test_wifi_mac.py, test_slot_mark.py, test_stock_levels.py

* Sat Oct 10 2026 mzak <mzak.amin@gmail.com> - 0.26-1
- sleep: the sensor stream stops across a suspend: the system-sleep hook iceland-sensors stops iio-sensor-proxy
  before the sleep and starts it again after the resume (the streaming accelerometer of the sensor hub kept the SoC
  out of its deepest idle on the same SoC, tb323fu-linux); iio-sensor-proxy is killed 3 s after a stop that hangs
  (TimeoutStopSec=3); a file /run/iceland/sensors-keep keeps the stream (tests)
- wakeup: the USB controller (a600000.usb) and the Wi-Fi PCIe root port (0000:00:00.0) are no wakeup sources
  (72-iceland-nowake.rules: a USB 2 hub woke the tablet at once on the same SoC); the charger (battery manager),
  the cover, the power key and the RTC alarm keep waking it
- watchdog: systemd feeds the hardware watchdog (qcom_wdt, /dev/watchdog0): RuntimeWatchdogSec=30s,
  RebootWatchdogSec=30s (system.conf.d/60-iceland-watchdog.conf; the rehearsals' values; effective after the next
  boot)
- cameras: 71-iceland-dma-heap.rules also gives the system dma-heap to the group video (0660), as libcamera's
  70-libcamera.rules does today, so the cameras do not depend on that rule
- GPU: devfreq min_freq 160 MHz at boot (73-iceland-gpu-devfreq.rules; 160 MHz is the lowest operating point of
  kernel-iceland's GPU table, so it documents the floor and changes nothing yet)
- tests: test_platform_defaults.py

* Sat Oct 10 2026 mzak <mzak.amin@gmail.com> - 0.25-1
- microphone: the processed source can be turned off with a PipeWire drop-in: the echo-cancel module of
  60-iceland-mic-processing.conf now carries condition = [ { iceland.mic-processing = !false } ], so a file with
  context.properties = { iceland.mic-processing = false } in /etc/pipewire/pipewire.conf.d/ (every account) or
  ~/.config/pipewire/pipewire.conf.d/ (one account) skips it after a PipeWire restart; without such a file nothing
  changes. The header's earlier advice (a same-name copy with an empty context.modules) was wrong: PipeWire loads
  every drop-in of all three directories and appends their module lists

* Sat Oct 10 2026 mzak <mzak.amin@gmail.com> - 0.24-1
- update policy: alsa-ucm (Fedora's ALSA UCM data) is held in the three Fedora repositories like libcamera
  (50-iceland-fedora-hold.repo): the tablet's sound profile includes its shared lib/card-init.conf, lib/ctl-remap.conf
  and codecs/wcd939x/init.conf, so a Fedora update could change the audio without a rehearsal (or conflict with our
  UCM files); our UCM now changes only through iceland-device. alsa-ucm requires alsa-lib >= its version: alsa-lib
  keeps updating
- update policy: dnf best=False and skip_broken=True (80-iceland-kernel.conf): an upgrade that cannot be resolved
  with the holds is skipped and the rest of the update goes ahead instead of the whole update failing (dnf,
  dnf5daemon / GNOME Software). Example: a Fedora PipeWire whose pipewire-plugin-libcamera needs a newer libcamera
  than the held one keeps the whole PipeWire set (exact-version sub-packages) at the installed version
- iceland-update-check (new, read-only): lists the upgrades offered now, those held back by the hold file and (as
  root) those the resolver skips

* Sat Oct 10 2026 mzak <mzak.amin@gmail.com> - 0.23-1
- battery guard, bypass service, thermal daemon: a sysfs attribute that exists but cannot be read (qcom_battmgr
  answers over pmic_glink; while the ADSP stalls a read fails with -110) is now unknown, never the benign value: an
  unreadable usb online keeps the previous "cable in" decision, an unreadable input limit never releases a cut,
  unreadable status / current / capacity keep the counters and holds as they were (chgsafe G1)
- microphone: UCM TX_DEC0/1 Volume 98 (was 96, +2 dB), which matches stock's measured recording level (-37.5 dBFS;
  96 gave about -39.6); ADC1/2 stay at 14
- microphone: a processed source "Internal microphones (voice processing)" (PipeWire drop-in
  60-iceland-mic-processing.conf: echo-cancel with the WebRTC backend - AGC, noise suppression, high-pass, echo
  cancellation against the speakers); the default for accounts without a stored choice, the raw source stays; a
  module or library that does not load leaves the raw source the default
  (its capture stream waits for the ALSA microphone with node.linger: WirePlumber 0.5 destroyed it at every
  PipeWire start because the microphone appears after the module, r2t / r2u)
- rehearsal guard: the nbd read check runs in the background and the guard waits at most 20 s for it, so a read
  stuck in D state (which ignores KILL) no longer hangs the guard; it logs "nbd probe stuck" and "the PC's disk does
  not answer" instead of going silent until its watchdog (r2o)

* Sat Oct 03 2026 mzak <mzak.amin@gmail.com> - 0.22-1
- bypass charging: the GSettings override that enables the Quick Settings toggle is now
  zz_iceland-device.gschema.override and keeps Fedora's background-logo entry: as 90_... it sorted before
  Fedora's org.gnome.shell.gschema.override, which won, and new accounts had the toggle off (r2k accept)

* Sat Oct 03 2026 mzak <mzak.amin@gmail.com> - 0.21-1
- bypass charging (stock "Bypass charging", oplus_chg_plc): a "Bypass Charging" toggle in GNOME's Quick Settings
  (GNOME Shell extension iceland-bypass@oneplus-pad4, enabled by a GSettings override) with a threshold menu from
  20 % (stock's picker); the D-Bus service iceland-bypassd (org.iceland.Bypass, polkit org.iceland.bypass.set: the
  active session's user, no password) writes the request; iceland-battery-guard holds the level from the
  threshold with charging off and the input kept (charge_behaviour inhibit-charge = stock's output_suspend vote),
  charges again when the level falls 1 % (stock simple strategy), ends bypass at unplug, at a charger-input safety
  stop (USB-C latch / input cut) and 5 minutes without renewal (stock plc_support_timeout; the toggle renews it
  every minute while the session is unlocked), never restores it after a reboot; every stock limit, the input cut
  and the charge limit still stop charging (BYPASS=0: off). Safety (wf/bypasssafe): a hold that was bypass's alone
  ends with the guard, a fault in the bypass code ends bypass and never the stock rules, a request that is not
  text or has no finite end is not used
- tests: test_guard_bypass.py, test_bypassd.py, test_guard_bypass_safety.py, test_guard_bypass_cut.py
- sensors: hexagonrpcd runs as the upstream user fastrpc with systemd hardening (no capabilities, read-only
  system, no network, only /dev/fastrpc-adsp); it never writes (it refuses write opens itself); the DSP file
  tree goes to group fastrpc at boot (tmpfiles.d/iceland-dsp-tree.conf: stock's registry files are 0600)

* Sat Oct 03 2026 mzak <mzak.amin@gmail.com> - 0.20-1
- cameras: local libcamera 0.7.1-1.fc44.iceland2 = iceland1 + SmartSens sensor properties (F05) +
  simple-pipeline link state without cache (F44); installed from the tablet inputs like iceland1

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.19-1
- cameras / Snapshot (F1, r2g): Requires pipewire-gstreamer >= 1.6.8 and pipewire-libs >= 1.6.8 - GNOME Snapshot
  crashed (SIGBUS in the PipeWire GStreamer device provider: the metadata listener re-added when the camera
  portal re-announces the default metadata); fixed in PipeWire 1.6.8, Fedora 44 ships 1.6.9
- clock: iceland-clock keeps /var/lib/systemd/timesync/clock current (every 15 min and at shutdown);
  systemd advances the clock to it at boot (the PMIC RTC cannot be set): rpm's signatures, TLS and the
  logs have a sane time before NTP (R1d / R2 started at systemd's built-in 2026-03-13)
- sound: /etc/modprobe.d/dist-alsa.conf shadows alsa-lib's install hook with a softdep on snd-seq: a kernel
  without the sequencer no longer loses the sound card at boot (R1d / R2)
- SELinux: module iceland_sensors for iio-sensor-proxy's QRTR socket to the sensor hub (R2 enforcing: no
  rotation, 60 denials)
- 50-iceland.preset: the first boot's preset-all keeps the iceland units enabled (Fedora's default preset
  would disable them)
- kernel command line: iceland-cmdline no longer adds clk_ignore_unused pd_ignore_unused
  regulator_ignore_unused but removes them: every install rehearsal booted without them (the call ran
  before kernel-iceland's entry existed) with everything working, and that is the lower-power state
- storage: the internal UFS LUNs get Fedora's bfq scheduler one at a time (61-iceland-ufs-scheduler.rules,
  /etc/udev/rules.d/60-block-scheduler.rules without them): they share one blk-mq tag set and parallel
  changes failed with "Device or resource busy" on 4-5 of the 6 LUNs at every boot
- cameras: the tuning files carry stock's colour-correction matrices (5 rear / 6 front colour
  temperatures) besides the black level (the owner's decision, 3 Oct 2026; private repository only)
- iceland-battery-guard: at a USB-C connector stop (57 / 69 C, the gap rules, rise fast) and at the input
  over-limit stop the guard also cuts the charger input through kernel-iceland's
  qcom-battmgr-usb/input_current_limit (0 = stock's OPLUS_USB_INPUT_CURRENT_LIMIT 0, the input suspend of
  stock's connector protection; CC stays closed, the USB data link stays), so that the system's load no longer
  flows through the hot connector; released once the cable is out, the connector reads below 55 C (stock's
  USB_55C recover rule) and no connector rule fires, by writing back the limit read before (the kernel applies
  its stock limit whatever is written: the guard never raises a current). VBUS over-voltage stays a charging
  stop only (stock). INPUT_SUSPEND=0 or a kernel without the lever: charging off only, as before.
- iceland-charge-alert (GNOME user service): desktop notifications for the guard's safety stops (USB-C
  connector, input current, charger voltage, battery temperature window, battery over-voltage, unreadable
  sensor) and their end; the guard writes one event per change to /run/iceland/charge-alert, the user's session
  reads it (no privilege path); one notification per event, a repeated stop within 2 minutes is not shown again
- tests: test_guard_input_suspend.py, test_charge_alert.py

* Fri Oct 02 2026 mzak <mzak.amin@gmail.com> - 0.18-1
- cameras: Fedora's libcamera updates held (50-iceland-fedora-hold.repo): the tablet keeps the local
  libcamera 0.7.1-1.fc44.iceland1 (GPU software ISP: border scaling, EGL probe with CPU fallback, the
  EGL context destroyed at stop): libcamera and libcamera-ipa from the local repository
- cameras: Requires wireplumber >= 0.5.18: with 0.5.16 / 0.5.17 the camera rule (51-iceland-camera.conf) stalls
  WirePlumber's event dispatcher and GNOME Camera gets no camera (area-combo-84; upstream 65519a1)
- install plan: every internal UFS partition read-only except userdata (udev, also in the initramfs);
  dracut module iceland: the root is a loop device over the Fedora disk inside userdata (rehearsal over
  the USB network and snapshot rollback only when their boot entry asks); a btrfs snapshot of the root
  before every package transaction (3 kept) with "Roll back to ..." boot entries; a new kernel-iceland
  boots once as a trial and becomes the default when the desktop is reached; GRUB loads each kernel's own
  device tree, shows its menu 3 s; iceland-device and the last kernel-iceland are protected from removal;
  fwupd's storage-firmware plugins (scsi, ufs) are disabled next to the UEFI capsule one

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
