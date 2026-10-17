# SPDX-License-Identifier: GPL-2.0-or-later
#
# iceland-device: Fedora settings for the OnePlus Pad 4 (iceland) running kernel-iceland.
# No firmware and no binaries: configuration files and small scripts only.

Name:           iceland-device
Version:        0.28
Release:        24%{?dist}
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
# 0.28-4: iceland-firmware from its GitHub release, sha256-pinned (wf/fwfetch)
Source140:      iceland-firmware-fetch
Source141:      firmware-pins.tsv
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
# 0.28-5: stock's 14 dB recorder gain after the echo canceller, under a -1 dBFS limiter (ladspa-swh-plugins)
Source142:      61-iceland-mic-gain.conf
# update policy (0.24): read-only list of the upgrades offered, held back by the hold file and skipped by the resolver
Source121:      iceland-update-check
# platform defaults (0.26, from the tb323fu-linux review): the sensor stream stopped across a suspend, systemd
# feeds the hardware watchdog (0.28-6: the wakeup defaults are in the device tree, the GPU floor rule is gone)
Source124:      iceland-sensors-sleep
Source125:      iio-sensor-proxy-iceland-sleep.conf
# 0.28-21: the proxy's ExecStopPost: the resume mark for a stop in the suspend transaction
Source190:      iceland-sensors-mark
Source126:      watchdog-iceland.conf
# speaker protection (0.27, from the tb323fu-linux review; 0.28-3: make-up up to stock's measured loudness, the raw
# speaker sink named as unprotected, the raw mic named, the protected sink as the configured default output)
Source127:      62-iceland-speakers.conf
Source128:      62-iceland-speaker-raw.conf
Source134:      63-iceland-mic-raw.conf
Source135:      iceland-speaker-default
Source136:      iceland-speaker-default.service
# 0.28-23: the speaker tone switch (stock = the packaged default; classic / warm / bass / warmbass / superturtle as
# a per-account drop-in)
Source191:      iceland-audio-profile
# 0.27r5: mark the Android A/B slot successful after a good boot (qbootctl -m; never in a RAM kit / rehearsal)
Source132:      iceland-slot-mark
Source133:      iceland-slot-mark.service
# 0.28-9 (field report 14 Oct 2026), four separate changes:
# (1) stock's default brightness (102 / 255 of 3542 = 1417) on the first boot only
Source150:      iceland-backlight-default
Source151:      iceland-backlight-default.service
Source152:      70-iceland-backlight-default.rules
# (2) runtime PM for the USB-C controller (dwc3 forbids it at probe), never in a rehearsal / RAM kit / with a gadget
Source153:      iceland-usb-pm
Source154:      72-iceland-usb-pm.rules
# (3) presets: services without a job on this tablet off (ModemManager, md RAID, smartd); ABRT apart (owner decides)
Source155:      50-iceland-unused.preset
Source156:      50-iceland-abrt.preset
# (4) memory: no proactive compaction (stock), transparent huge pages madvise
Source157:      60-iceland-vm.conf
Source158:      iceland-thp.conf
# 0.28-11: no password prompt to override the guard's sleep block (power key on a charger)
Source159:      49-iceland-no-sleep-override.rules
# govtune: stock's app-launch boost (util clamp) + system services on the small cores
Source160:      iceland-launchboost
Source161:      iceland-launchboost.service
Source162:      launchboost.conf
Source163:      50-iceland-system-cpus.conf
# 0.28-13 (wf/chgmode): the charging mode of a cable power-on (ABL's off-mode charging start, passed on by U-Boot
# patch 0011 as /chosen/u-boot,abl-boot-mode): a generator picks the target, a watcher keeps the panel dark, powers
# off at the unplug and starts the desktop at the power key
Source164:      iceland-charging-generator
Source165:      iceland-charging.target
Source166:      iceland-charging.service
Source167:      iceland-charging
# 0.28-15 (wf/chgmode2): the PMIC's PON log (read only) as the sign of a cable power-on
Source168:      iceland-pon-log
# 0.28-15: the managed kernel options for a new kernel's entry (iceland-cmdline after kernel-install)
Source169:      97-iceland-cmdline.install
# 0.28-16 (wf/r16): the PON log is read by a service before the display manager, no longer by the generator
Source170:      iceland-charging-detect
Source171:      iceland-charging-detect.service
# 0.28-16: the sensor programs are started again when they stopped and nothing else starts them
Source172:      iceland-ssc-watch
Source173:      iceland-ssc-watch.service
Source174:      iceland-ssc-watch.timer
# 0.28-17 (wf/generic): the unit's own values on the first boot of a generic image (Bluetooth address, read only)
Source175:      iceland-provision
Source176:      iceland-provision.service
Source177:      provision-sources.tsv
# 0.28-17: the small generic image grows into userdata (checks systemd-repart / growfs, repairs what is missing; once)
Source178:      iceland-grow
Source179:      iceland-grow.service
# 0.28-18 (wf/scanfix C2): the login screen's own default - no automatic brightness, no light sensor claim
Source180:      50-iceland-greeter-ambient
# 0.28-19: stock's GPU pair (0.28-20: and the vendor pair) into every kernel-iceland initramfs that lacks it (once,
# %posttrans)
Source181:      iceland-gpu-initramfs

Requires:       kernel-iceland
# 0.28-19: stock's GPU GMU / SQE pair (/usr/lib/firmware/iceland-gpu-stock, GPU_FW=stock); 0.28-20: the vendor pair
# v5.3.33 / 0x094 (/usr/lib/firmware/iceland-gpu-vendor533, GPU_FW=vendor533, the default), both selected by
# iceland-cmdline
Requires:       iceland-firmware >= 11.A.38-6
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
# iceland-speaker-default (0.28-3): pw-cli / pw-metadata
Requires:       pipewire-utils
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
# 0.28-18: dconf update compiles GDM's system database (/etc/dconf/db/gdm.d -> /etc/dconf/db/gdm)
Requires(posttrans): dconf
Requires(postun): dconf

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
- the GPU runs the vendor GMU firmware v5.3.33 / SQE microcode 0x094 (iceland-firmware >= 11.A.38-6) with GPU
  preemption on: firmware_class.path=/usr/lib/firmware/iceland-gpu-vendor533 and msm.enable_preemption=1 on the
  kernel command line, both GPU pairs in the initramfs; GPU_FW=stock in /etc/iceland/boot.conf selects stock
  11.A.38's v5.3.39 / 0x103 with preemption off, GPU_FW=linux-firmware Fedora's pair (GPU_PREEMPT=auto|0|1;
  preemption is never switched on with stock's or linux-firmware's pair);
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
  ever lowers limits; the kernel's thermal zones stay underneath. The shell temperature model is stock's, decoded
  and generic (/etc/iceland/thermal-model.json, shipped by iceland-firmware >= 11.A.38-3); without it the battery
  temperature + 2 C stands in;
- kernel-iceland updates come from a local dnf repository (/var/lib/iceland/repo, filled by iceland-repo-sync);
  iceland-firmware comes from its GitHub release through iceland-firmware-fetch: one https download, checked
  against the sha256 pins in /usr/share/iceland/firmware-pins.tsv (the rpms are unsigned: the pin is the trust
  anchor) and the rpm's own name and digests, installed by dnf from the local file with every repository off;
  a mismatch installs nothing, no network keeps the installed package;
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
install -Dm0755 %{SOURCE181} %{buildroot}/usr/libexec/iceland/iceland-gpu-initramfs
install -Dm0644 %{SOURCE7} %{buildroot}/usr/lib/dracut/dracut.conf.d/90-iceland.conf
install -Dm0644 %{SOURCE8} %{buildroot}/usr/lib/NetworkManager/conf.d/60-iceland-wifi-powersave.conf
install -Dm0755 %{SOURCE9} %{buildroot}/usr/libexec/iceland/iceland-battery-guard
install -Dm0644 %{SOURCE10} %{buildroot}/usr/lib/systemd/system/iceland-battery-guard.service
install -Dm0644 %{SOURCE11} %{buildroot}/etc/yum.repos.d/iceland-local.repo
install -Dm0755 %{SOURCE12} %{buildroot}/usr/bin/iceland-repo-sync
install -Dm0755 %{SOURCE140} %{buildroot}/usr/bin/iceland-firmware-fetch
install -Dm0644 %{SOURCE141} %{buildroot}/usr/share/iceland/firmware-pins.tsv
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
install -Dm0644 %{SOURCE35} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/51-iceland-camera.conf
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
install -Dm0755 %{SOURCE160} %{buildroot}/usr/libexec/iceland/iceland-launchboost
install -Dm0644 %{SOURCE161} %{buildroot}/usr/lib/systemd/system/iceland-launchboost.service
install -Dm0644 %{SOURCE162} %{buildroot}/etc/iceland/launchboost.conf
install -Dm0644 %{SOURCE163} %{buildroot}/usr/lib/systemd/system/system.slice.d/50-iceland-system-cpus.conf
install -Dm0755 %{SOURCE164} %{buildroot}/usr/lib/systemd/system-generators/iceland-charging-generator
install -Dm0644 %{SOURCE165} %{buildroot}/usr/lib/systemd/system/iceland-charging.target
install -Dm0644 %{SOURCE166} %{buildroot}/usr/lib/systemd/system/iceland-charging.service
install -Dm0755 %{SOURCE167} %{buildroot}/usr/libexec/iceland/iceland-charging
install -Dm0755 %{SOURCE168} %{buildroot}/usr/libexec/iceland/iceland-pon-log
install -Dm0755 %{SOURCE170} %{buildroot}/usr/libexec/iceland/iceland-charging-detect
install -Dm0644 %{SOURCE171} %{buildroot}/usr/lib/systemd/system/iceland-charging-detect.service
install -Dm0755 %{SOURCE172} %{buildroot}/usr/libexec/iceland/iceland-ssc-watch
install -Dm0644 %{SOURCE173} %{buildroot}/usr/lib/systemd/system/iceland-ssc-watch.service
install -Dm0644 %{SOURCE174} %{buildroot}/usr/lib/systemd/system/iceland-ssc-watch.timer
install -Dm0755 %{SOURCE175} %{buildroot}/usr/libexec/iceland/iceland-provision
install -Dm0644 %{SOURCE176} %{buildroot}/usr/lib/systemd/system/iceland-provision.service
install -Dm0644 %{SOURCE177} %{buildroot}/usr/share/iceland/provision-sources.tsv
install -Dm0755 %{SOURCE178} %{buildroot}/usr/libexec/iceland/iceland-grow
install -Dm0644 %{SOURCE179} %{buildroot}/usr/lib/systemd/system/iceland-grow.service
install -Dm0644 %{SOURCE180} %{buildroot}/etc/dconf/db/gdm.d/50-iceland-greeter-ambient
# static links (not a preset, not "enable"): part of every graphical boot / every boot
install -d %{buildroot}/usr/lib/systemd/system/graphical.target.wants %{buildroot}/usr/lib/systemd/system/timers.target.wants
ln -s ../iceland-charging-detect.service %{buildroot}/usr/lib/systemd/system/graphical.target.wants/iceland-charging-detect.service
ln -s ../iceland-ssc-watch.timer %{buildroot}/usr/lib/systemd/system/timers.target.wants/iceland-ssc-watch.timer
mkdir -p %{buildroot}/usr/lib/systemd/system/multi-user.target.wants
ln -s ../iceland-provision.service %{buildroot}/usr/lib/systemd/system/multi-user.target.wants/iceland-provision.service
ln -s ../iceland-grow.service %{buildroot}/usr/lib/systemd/system/multi-user.target.wants/iceland-grow.service
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
install -Dm0755 %{SOURCE169} %{buildroot}/usr/lib/kernel/install.d/97-iceland-cmdline.install
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
install -Dm0644 %{SOURCE142} %{buildroot}/usr/share/pipewire/pipewire.conf.d/61-iceland-mic-gain.conf
install -Dm0755 %{SOURCE121} %{buildroot}/usr/bin/iceland-update-check
install -Dm0755 %{SOURCE124} %{buildroot}/usr/lib/systemd/system-sleep/iceland-sensors
install -Dm0644 %{SOURCE125} %{buildroot}/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland-sleep.conf
install -Dm0755 %{SOURCE190} %{buildroot}/usr/libexec/iceland/iceland-sensors-mark
install -Dm0644 %{SOURCE126} %{buildroot}/usr/lib/systemd/system.conf.d/60-iceland-watchdog.conf
install -Dm0644 %{SOURCE127} %{buildroot}/usr/share/pipewire/pipewire.conf.d/62-iceland-speakers.conf
install -Dm0644 %{SOURCE128} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/62-iceland-speaker-raw.conf
install -Dm0644 %{SOURCE134} %{buildroot}/usr/share/wireplumber/wireplumber.conf.d/63-iceland-mic-raw.conf
install -Dm0755 %{SOURCE135} %{buildroot}/usr/libexec/iceland/iceland-speaker-default
install -Dm0644 %{SOURCE136} %{buildroot}/usr/lib/systemd/user/iceland-speaker-default.service
install -Dm0755 %{SOURCE191} %{buildroot}/usr/bin/iceland-audio-profile
install -Dm0755 %{SOURCE132} %{buildroot}/usr/libexec/iceland/iceland-slot-mark
install -Dm0644 %{SOURCE133} %{buildroot}/usr/lib/systemd/system/iceland-slot-mark.service
install -Dm0755 %{SOURCE150} %{buildroot}/usr/libexec/iceland/iceland-backlight-default
install -Dm0644 %{SOURCE151} %{buildroot}/usr/lib/systemd/system/iceland-backlight-default.service
install -Dm0644 %{SOURCE152} %{buildroot}/usr/lib/udev/rules.d/70-iceland-backlight-default.rules
install -Dm0755 %{SOURCE153} %{buildroot}/usr/libexec/iceland/iceland-usb-pm
install -Dm0644 %{SOURCE154} %{buildroot}/usr/lib/udev/rules.d/72-iceland-usb-pm.rules
install -Dm0644 %{SOURCE155} %{buildroot}/usr/lib/systemd/system-preset/50-iceland-unused.preset
install -Dm0644 %{SOURCE156} %{buildroot}/usr/lib/systemd/system-preset/50-iceland-abrt.preset
install -Dm0644 %{SOURCE157} %{buildroot}/usr/lib/sysctl.d/60-iceland-vm.conf
install -Dm0644 %{SOURCE158} %{buildroot}/usr/lib/tmpfiles.d/iceland-thp.conf
install -Dm0644 %{SOURCE159} %{buildroot}/usr/share/polkit-1/rules.d/49-iceland-no-sleep-override.rules
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
# 0.28-19: stock's GPU pair (90-iceland.conf; 0.28-20: and the vendor pair) into the existing kernel-iceland
# initramfs images that lack one; a new
# kernel's initramfs gets it from dracut. Without it firmware_class.path would find linux-firmware's copies there.
/usr/libexec/iceland/iceland-gpu-initramfs || :
# a stale saved ALSA mixer state can route MultiMedia1 into back ends the ADSP can't open (pc-026 S12: GNOME showed
# only a Dummy Output); drop it once, the UCM FixedBootSequence then sets the routes at every boot
if [ ! -e /var/lib/iceland/.asound-state-reset ]; then
	rm -f /var/lib/alsa/asound.state
	mkdir -p /var/lib/iceland && touch /var/lib/iceland/.asound-state-reset
fi
systemctl enable iceland-battery-guard.service iceland-npu-off.service iceland-wifi-country.service iceland-ssc-resume.service >/dev/null 2>&1 || :
# 0.16 had a unit that kept a sensor-hub sensor streaming for the cameras; the kernel keeps their bus connected now
systemctl stop iceland-ssc-hold.service >/dev/null 2>&1 || :
# K7: the kernel holds the rear lens at its default position while the rear sensor streams; the old
# focus helper is stopped and disabled once (its unit file goes with the old package)
systemctl disable --now iceland-camera-focus.service >/dev/null 2>&1 || :
# the DMA heap permissions (71-iceland-dma-heap.rules) at once; a running WirePlumber keeps the heap it has open
# until the user's next login
if [ -d /run/systemd/system ]; then udevadm control --reload >/dev/null 2>&1 || :; udevadm trigger --action=add -s dma_heap >/dev/null 2>&1 || :; fi
# the watchdog drop-in (system.conf.d) takes effect at the next boot. 0.28-6: no wakeup or GPU rules any more (the
# device tree has the wakeup defaults, 160 MHz is the GPU's lowest operating point anyway)
# the skin temperature policy starts at boot, like the guard
systemctl enable iceland-thermal.service >/dev/null 2>&1 || :
systemctl enable iceland-launchboost.service >/dev/null 2>&1 || :
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
if [ -d /run/systemd/system ]; then systemctl daemon-reload >/dev/null 2>&1 || :; systemctl try-restart iceland-battery-guard.service iceland-thermal.service >/dev/null 2>&1 || :; systemctl start iceland-launchboost.service >/dev/null 2>&1 || :; fi
# 0.28-16: the sensor watch runs from now on (its timer is linked into timers.target.wants)
[ -d /run/systemd/system ] && systemctl start iceland-ssc-watch.timer >/dev/null 2>&1 || :
systemctl --global enable iceland-refresh.service iceland-charge-alert.service iceland-speaker-default.service >/dev/null 2>&1 || :
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
# 0.28-9 (2): the USB-C controller's runtime PM now (iceland-usb-pm applies its guards; the rule covers every boot)
if [ -d /run/systemd/system ]; then udevadm control --reload >/dev/null 2>&1 || :; /usr/libexec/iceland/iceland-usb-pm apply >/dev/null 2>&1 || :; fi
# 0.28-9 (3): the services without a job on this tablet (50-iceland-unused.preset, 50-iceland-abrt.preset) are
# preset once per system, and only those still enabled: a unit the owner enabled or masked keeps that state
# afterwards, a new image gets the same at its first boot's preset-all
if [ ! -e /var/lib/iceland/.preset-unused-0.28-9 ]; then
	for f in /usr/lib/systemd/system-preset/50-iceland-unused.preset /usr/lib/systemd/system-preset/50-iceland-abrt.preset; do
		[ -f "$f" ] || continue
		for u in $(sed -n 's/^disable //p' "$f"); do
			[ "$(systemctl is-enabled "$u" 2>/dev/null)" = enabled ] && systemctl preset "$u" >/dev/null 2>&1 || :
		done
	done
	mkdir -p /var/lib/iceland && touch /var/lib/iceland/.preset-unused-0.28-9
fi
# 0.28-9 (4): sysctl.d / tmpfiles.d take effect through systemd's file triggers at once and at every boot
# 0.28-18: GDM's dconf database with the greeter default (ambient-enabled=false); the greeter reads it at its next
# start (the next login screen), user sessions are not touched
dconf update >/dev/null 2>&1 || :

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
[ "$1" -eq 0 ] && systemctl --global disable iceland-refresh.service iceland-charge-alert.service iceland-speaker-default.service >/dev/null 2>&1; [ "$1" -eq 0 ] && systemctl disable iceland-ssc-resume.service iceland-wifi-country.service iceland-npu-off.service iceland-battery-guard.service iceland-bdaddr.service >/dev/null 2>&1 || :
# the thermal policy hands its limits back when it stops
[ "$1" -eq 0 ] && systemctl disable --now iceland-thermal.service >/dev/null 2>&1 || :
# the launch boost hands every clamp back when it stops
[ "$1" -eq 0 ] && systemctl disable --now iceland-launchboost.service >/dev/null 2>&1 || :
if [ "$1" -eq 0 ]; then if [ -d /run/systemd/system ] && [ -e /sys/fs/selinux/enforce ]; then semodule -r iceland_sensors >/dev/null 2>&1 || :; else semodule -n -r iceland_sensors >/dev/null 2>&1 || :; fi; fi
[ "$1" -eq 0 ] && systemctl disable --now iceland-clock.timer iceland-clock.service >/dev/null 2>&1 || :
[ "$1" -eq 0 ] && /usr/bin/iceland-power-profiles reset >/dev/null 2>&1 || :
# bypass charging ends with the package (the running guard gives charging back at its next step)
[ "$1" -eq 0 ] && { systemctl stop iceland-bypass.service >/dev/null 2>&1; rm -f /run/iceland/bypass-request; } || :

%postun
# 0.28-18: on removal GDM's dconf database is compiled again without the greeter default (an upgrade does it in
# %posttrans)
[ "$1" -eq 0 ] && { dconf update >/dev/null 2>&1 || :; } || :

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
/usr/libexec/iceland/iceland-gpu-initramfs
/usr/lib/dracut/dracut.conf.d/90-iceland.conf
/usr/lib/NetworkManager/conf.d/60-iceland-wifi-powersave.conf
/usr/libexec/iceland/iceland-battery-guard
/usr/lib/systemd/system/iceland-battery-guard.service
%config(noreplace) /etc/yum.repos.d/iceland-local.repo
/usr/bin/iceland-repo-sync
/usr/bin/iceland-firmware-fetch
/usr/libexec/iceland/iceland-refresh
/usr/lib/systemd/user/iceland-refresh.service
%config(noreplace) /etc/iceland/refresh.conf
%config(noreplace) /etc/iceland/battery-guard.conf
/usr/bin/iceland-npu
/usr/bin/iceland-update-check
/usr/lib/systemd/system-sleep/iceland-sensors
/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland-sleep.conf
/usr/libexec/iceland/iceland-sensors-mark
/usr/lib/systemd/system.conf.d/60-iceland-watchdog.conf
/usr/share/pipewire/pipewire.conf.d/62-iceland-speakers.conf
/usr/share/wireplumber/wireplumber.conf.d/62-iceland-speaker-raw.conf
/usr/share/wireplumber/wireplumber.conf.d/63-iceland-mic-raw.conf
/usr/libexec/iceland/iceland-speaker-default
/usr/lib/systemd/user/iceland-speaker-default.service
/usr/bin/iceland-audio-profile
/usr/libexec/iceland/iceland-slot-mark
/usr/lib/systemd/system/iceland-slot-mark.service
/usr/libexec/iceland/iceland-backlight-default
/usr/lib/systemd/system/iceland-backlight-default.service
/usr/lib/udev/rules.d/70-iceland-backlight-default.rules
/usr/libexec/iceland/iceland-usb-pm
/usr/lib/udev/rules.d/72-iceland-usb-pm.rules
/usr/lib/systemd/system-preset/50-iceland-unused.preset
/usr/lib/systemd/system-preset/50-iceland-abrt.preset
/usr/lib/sysctl.d/60-iceland-vm.conf
/usr/lib/tmpfiles.d/iceland-thp.conf
/usr/share/polkit-1/rules.d/49-iceland-no-sleep-override.rules
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
/usr/share/iceland/firmware-pins.tsv
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
/usr/share/wireplumber/wireplumber.conf.d/51-iceland-camera.conf
/usr/lib/udev/rules.d/71-iceland-dma-heap.rules
/usr/lib/udev/hwdb.d/61-iceland-battery.hwdb
%dir /usr/lib/systemd/system/upower.service.d
/usr/lib/systemd/system/upower.service.d/iceland.conf
/usr/libexec/iceland/iceland-thermal
/usr/lib/systemd/system/iceland-thermal.service
/usr/libexec/iceland/iceland-launchboost
/usr/lib/systemd/system/iceland-launchboost.service
/usr/lib/systemd/system/system.slice.d/50-iceland-system-cpus.conf
/usr/lib/systemd/system-generators/iceland-charging-generator
/usr/lib/systemd/system/iceland-charging.target
/usr/lib/systemd/system/iceland-charging.service
/usr/libexec/iceland/iceland-charging
/usr/libexec/iceland/iceland-pon-log
/usr/libexec/iceland/iceland-charging-detect
/usr/lib/systemd/system/iceland-charging-detect.service
/usr/lib/systemd/system/graphical.target.wants/iceland-charging-detect.service
/usr/libexec/iceland/iceland-ssc-watch
/usr/lib/systemd/system/iceland-ssc-watch.service
/usr/lib/systemd/system/iceland-ssc-watch.timer
/usr/lib/systemd/system/timers.target.wants/iceland-ssc-watch.timer
/usr/libexec/iceland/iceland-provision
/usr/lib/systemd/system/iceland-provision.service
/usr/lib/systemd/system/multi-user.target.wants/iceland-provision.service
/usr/share/iceland/provision-sources.tsv
/usr/libexec/iceland/iceland-grow
/usr/lib/systemd/system/iceland-grow.service
/usr/lib/systemd/system/multi-user.target.wants/iceland-grow.service
%dir /etc/dconf/db/gdm.d
%config(noreplace) /etc/dconf/db/gdm.d/50-iceland-greeter-ambient
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
%config(noreplace) /etc/iceland/launchboost.conf
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
/usr/lib/kernel/install.d/97-iceland-cmdline.install
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
/usr/share/pipewire/pipewire.conf.d/61-iceland-mic-gain.conf

%changelog
* Sat Oct 17 2026 mzak <mzak.amin@gmail.com> - 0.28-24
- the dual-boot package (wf/dualboot3, procedure step W0; numbered after 0.28-23, the number 0.28-22 stays unused)
- storage seat belt follows Fedora's carrier: iceland-storage-ro chooses it as dracut-iceland-carrier does
  (iceland.carrier=, else the UFS partition "fedora" if there is one, else "userdata"; none in a rehearsal) and keeps
  only the carrier and its LUN writable. Once a "fedora" partition exists, "userdata" belongs to Android and is
  read-only; without one (today's layout) nothing changes. Up to 0.28-23 the rule kept "userdata" writable and
  would have made a "fedora" carrier read-only under Fedora's root. 59-iceland-storage-ro.rules hands both names
  to the helper (ICELAND_STORAGE=carrier-candidate); new "iceland-storage-ro --explain" (reads only)
- iceland-slot-mark: the stray-write guard. Before qbootctl -m it reads blocks 6-255 and the last 256 blocks
  (without the backup table) of the LUN holding userdata / fedora and of the boot LUN, and compares them after the
  mark: a change is a FAIL, the bytes from before are kept in /var/lib/iceland/slot-mark/, the off switch
  /etc/iceland/slot-mark-off is created. With a "fedora" partition an unreadable region means no mark. Reason: the
  17 Oct backup holds 5 stray GPT attribute bytes 4 blocks before LUN 0's backup entry array (inside userdata);
  qbootctl 0.2.2 itself was proven clean on 4 KiB-block loop LUNs, the writer is most likely the boot loader, and
  the guard makes every mark from Fedora prove it. A loop root over "fedora" was already accepted (0.28-8)
- tests: new tests/test_storage_dualboot.py (both layouts, the guard), test_install_parts.py follows the rule
- carries 0.28-23 unchanged (and 0.28-18's login screen default 50-iceland-greeter-ambient)

* Sat Oct 17 2026 mzak <mzak.amin@gmail.com> - 0.28-23
- (numbering: 0.28-22 is the dual-boot package; this one builds on 0.28-21)
- speakers: the stock tone is the packaged default (the owner's choice of 17 Oct 2026 after the listening A/B):
  62-iceland-speakers.conf keeps the 150 Hz 4th-order high-pass, the compressor (2.5:1 @ -24 dBFS, +9 dB make-up)
  and the -1 dBFS limiter unchanged and adds a cuts-only set fitted to the stock reference (LineageOS 24, vendor
  DSP; predicted residual rms 1.7 dB, max 4.0 dB, 90 Hz - 10 kHz): a second 4th-order high-pass 228 Hz, peaking
  -10 dB @ 280 Hz (Q 0.73), -15 dB @ 612 Hz (Q 1.55), high-shelf -22 dB @ 2.52 kHz, peaking -15 dB @ 3.91 kHz
  (Q 0.98) and -8.1 dB @ 9.09 kHz (Q 4). Every band is at or below the 0.28-21 chain (1 kHz -9 dB before the
  compressor). Sink name effect_input.speakers and the off switch iceland.speaker-protection unchanged
- new /usr/bin/iceland-audio-profile stock|classic|warm|bass|warmbass|superturtle|status|print: one account's tone
  as a drop-in ~/.config/pipewire/pipewire.conf.d/63-iceland-audio-profile.conf (the packaged chain off, the
  chosen one under the same sink name); stock removes the drop-in; classic = the 0.28-21 chain. Refuses root, an
  unknown name and (except superturtle) missing LADSPA plug-ins. A drop-in left by the A/B test script stays (the
  account's own file): 'iceland-audio-profile stock' returns to the default
- tests: test_audio_profiles.py (cuts only vs classic, residual bound vs tests/stock_response.json, every drop-in
  parses, sink identical, dry run); test_speaker_protection.py follows the longer chain
- carries 0.28-21 otherwise unchanged (and 0.28-18's login screen default 50-iceland-greeter-ambient)

* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 0.28-21
- (numbering: this fix package is 0.28-21, the dual-boot package becomes 0.28-22)
- carries 0.28-20 otherwise unchanged (and 0.28-18's login screen default 50-iceland-greeter-ambient)
- sensors at suspend (owner's finding, 2 of 14 suspends since 13 Oct: iio-sensor-proxy killed after its 3 s stop
  timeout with a core dump): the proxy now stops in the suspend transaction itself, before the sensor hub's file
  server - iio-sensor-proxy.service.d/iceland-sleep.conf: Conflicts=suspend.target (as hexagonrpcd's own unit) and
  Before=sleep.target; iceland.conf's After=hexagonrpcd-adsp-sensorspd.service orders the proxy's stop first. Its
  ExecStopPost iceland-sensors-mark leaves /run/iceland/sensors-stopped when a suspend.target / sleep.target start
  job is queued, so iceland-ssc-resume.service starts both again after the resume (unchanged, outside the suspend
  transaction). The system-sleep hook stays as the fallback, still starts nothing (0.26 / A52); the test switch
  /run/iceland/sensors-keep no longer keeps the stream (the file server stops in any case)
- clock: iceland-clock restore logs the RTC's state (no time / the bare counter / its time) and that the restored
  stamp is a lower bound until chrony steps the clock; status shows the same. chrony unchanged: on 16 Oct its
  "wrong by 1068 s" and "stepped by 1068 s" lines were one step 13 s after its start (the second line is stamped
  after the step), so makestep 1.0 3 worked. Kernel side: queue 0337 (rtc-pm8xxx gives no time while the SDAM2
  offset reads 0)
- kernel retention (from the parked COPR candidate wf/copr, without the COPR repository): kernel-iceland out of
  /etc/dnf/protected.d (a protected installonly package cannot lose its oldest version: every transaction failed once
  installonly_limit was reached); installonly_limit=3 and protect_running_kernel=True written in
  80-iceland-kernel.conf; when dnf removes the confirmed kernel the trial plugin makes the running kernel the
  confirmed one if it remains, else the newest remaining kernel whose trial did not fail, else the newest remaining

* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 0.28-20
- the GPU runs the vendor firmware pair GMU v5.3.33 / SQE 0x094 (iceland-firmware 11.A.38-6, as SuperTurtleDev and
  the TB323FU port) with GPU preemption ON, keeping kernel-iceland's GPU power-vote patches (the owner's decision
  of 16 Oct 2026 after the RAM rehearsal P2: kernel q89m, msm.enable_preemption=1, 48356 preemption ring switches,
  0 fenced-write failures / preemption timeouts / faults / recoveries, Chromium WebGL 0 crashes, vkmark 22112).
  GPU_FW in /etc/iceland/boot.conf gains vendor533, the new default: iceland-cmdline puts
  firmware_class.path=/usr/lib/firmware/iceland-gpu-vendor533 and msm.enable_preemption=1 on every boot entry
  and /etc/kernel/cmdline; GPU_FW=stock = stock's path and no preemption option (kernel default off);
  GPU_FW=linux-firmware = neither. A missing vendor pair falls back to stock's, a missing stock pair to
  linux-firmware's
- new switch GPU_PREEMPT=auto|0|1 (auto = on exactly with vendor533; 1 is refused with stock's or
  linux-firmware's pair: preemption with them reset the tablet early in boot, rehearsals P1 / R3); with
  preemption off every msm.enable_preemption value other than 0 is removed from the entries
- 90-iceland.conf: both GPU pairs in the initramfs; iceland-gpu-initramfs checks / rebuilds for every installed
  pair. Requires iceland-firmware >= 11.A.38-6; firmware-pins.tsv: 11.A.38-6 (f8e202b3, the new
  iceland-firmware-fetch default). tests/test_gpu_fw.py: the firmware x preemption matrix
- carries 0.28-19 otherwise unchanged (and 0.28-18's login screen default 50-iceland-greeter-ambient)

* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 0.28-19
- the GPU runs stock 11.A.38's firmware pair, GMU v5.3.39 / SQE 0x103 (the owner's decision of 16 Oct 2026 after
  the RAM rehearsal R4: kernel q89m, GPU preemption off, clean GPU start, 0 GMU errors, 0 fenced writes, Chromium
  WebGL 180 s without a GPU-process exit, vkmark 23613). iceland-cmdline puts
  firmware_class.path=/usr/lib/firmware/iceland-gpu-stock on every boot entry and /etc/kernel/cmdline (switch
  GPU_FW=stock|linux-firmware in /etc/iceland/boot.conf, default stock; only when both files are installed, else
  the option is removed); the kernel searches that directory first and finds only the GMU and SQE files there.
  Requires iceland-firmware >= 11.A.38-5 (the pair; linux-firmware's files are not replaced)
- 90-iceland.conf: the pair in the initramfs (the GPU loads its microcode there); new iceland-gpu-initramfs
  (%posttrans) rebuilds the existing kernel-iceland initramfs images that lack it (--check lists them)
- firmware-pins.tsv: iceland-firmware 11.A.38-4 (fb86f5fa) and 11.A.38-5 (8e430110, the new default of
  iceland-firmware-fetch). New tests/test_gpu_fw.py
- carries 0.28-18 unchanged (the login screen's 50-iceland-greeter-ambient, wf/scanfix C2) and 0.28-17
* Fri Oct 16 2026 mzak <mzak.amin@gmail.com> - 0.28-18
- the login screen no longer claims the ambient light sensor (wf/scanfix C2): /etc/dconf/db/gdm.d/
  50-iceland-greeter-ambient sets org.gnome.settings-daemon.plugins.power ambient-enabled=false in GDM's system
  database (system-db:gdm of GDM's dconf profile; dconf update in %posttrans, and in %postun on removal). With
  GNOME's default the greeter's gsd-power claimed the light sensor from the boot to the login and could not
  release it after the login ('Release of light sensors failed: AccessDenied', its session no longer active) until
  GDM stopped the greeter; the proxy streamed the sensor for the login screen. User sessions keep their own
  Automatic Screen Brightness setting. New tests/test_gdm_ambient.py
- carries 0.28-17 unchanged (an installed 0.28-16 gets the 0.28-17 fixes through this package)
* Thu Oct 15 2026 mzak <mzak.amin@gmail.com> - 0.28-17
- generic image "Fedora Remix for OnePlus Pad 4" (wf/generic, the owner's decisions of 15 Oct 2026):
  iceland-provision.service runs once on the first boot (ConditionPathExists=!/var/lib/iceland/provisioned; a static
  multi-user.target.wants link, before bluetooth and iceland-bdaddr) and finds the unit's own Bluetooth address: the
  device tree's local-bd-address when U-Boot filled it (K1, later; then nothing is written), else a kept
  /etc/iceland/bdaddr, else the first usable address of /usr/share/iceland/provision-sources.tsv, read from the
  tablet's own partitions with debugfs -c (never mounted, the partition read-only in the kernel first) into
  /etc/iceland/bdaddr (0600), else one WARNING line (the controller's shared default address). Install-Pad4Linux.ps1
  reads the address read-only from Android (persist.vendor.service.bdroid.bdaddr) in its backup phase, saves it as
  bdaddr.txt next to the backup manifest and prints "sudo iceland-provision --bdaddr XX:XX:XX:XX:XX:XX" for the first
  login; --bdaddr applies it at once (restarts iceland-bdaddr.service). Placeholders are never taken; the address is
  never logged; the machine id and the SSH host keys are only reported (systemd / sshd make them). The sensor registry
  is kept as it is (owner). New tests/test_provision.py
- iceland-grow.service (once, after systemd-repart and systemd-growfs-root; static multi-user.target.wants link): the
  generic image is small and must fill userdata on any storage size. It checks the loop container (losetup -c), the
  backup GPT at the disk end, the root partition (the last one) up to the last usable block and btrfs up to its
  partition; what systemd-repart / growfs left undone it repairs (sfdisk --relocate gpt-bak-std, sfdisk -N ", +",
  partx -u, btrfs filesystem resize max /), never shrinking or moving a start; no stamp on a failure (the next boot
  tries again). Skipped in a rehearsal, with systemd-repart masked (dual boot) or a carrier other than userdata /
  fedora. One line; /var/lib/iceland/grown. New tests/test_grow.py (decisions with stubs, the repair on a real
  4 KiB-sector GPT disk file with util-linux sfdisk)
- iceland-slot-mark.service is Type=exec (was oneshot; RuntimeMaxSec=8min): the first issue scan (16 Oct) showed
  'FAIL not a good boot: system state starting after 300 s' on every boot - the oneshot, pulled in by
  graphical.target, was itself a job of the boot transaction, so systemd stayed 'starting' while the script waited
  for 'running', and the slot was never marked. The rules are unchanged (good boot only, the boot LUN writable for
  the one qbootctl -m only). A FAIL line now names the jobs still queued, a degraded boot its failed units
- iceland-snapshot pre / post print to stderr and the journal only: the libdnf5 actions plugin parses the
  command's standard output as key=value requests, and every 'iceland-snapshot: ...' line was an action error in
  dnf5.log ('Missing equal sign (=) in action output line'; the snapshots were made). iceland-snapshot.actions:
  enabled=host-only (no snapshot of this root for a dnf --installroot transaction). The installed 0.28-16 copy is
  unmodified (rpm -V clean), so rpm replaces this %config(noreplace) file; a hand-edited copy keeps its edits and
  gets the new one as .rpmnew. New tests/test_snapshot_actions.py (the actions syntax, the plugin's stdout grammar)
- iceland-grow acts only on the first boot of a generic image: the marker /etc/iceland/generic-image (written by the
  B150g recipe, removed after a successful grow) and the root under half of the disk. Without the marker (an
  installed system such as the owner's, root already 218 GiB, loop0's inner backup GPT left as it is) one line
  'not a generic first boot: nothing to do' and no command at all
* Thu Oct 15 2026 mzak <mzak.amin@gmail.com> - 0.28-16
- charging mode (wf/r16): the 0.28-15 generator never wrote its "PMIC PON log" line at boot on the installed tablet,
  although the same command worked by hand as root. Generators run in systemd 258's sandbox (own mount namespace,
  / read only, private /tmp) and, on Fedora, in the confined SELinux domain systemd_generator_t, while the reader
  needs python3, debugfs (or unshare + a debugfs mount) and the PMIC's regmap. The PON log is now read by the new
  iceland-charging-detect.service: a plain oneshot service of every graphical boot (a static link in
  graphical.target.wants), ordered before display-manager.service / gdm.service, after sys-kernel-debug.mount;
  verdict charger -> systemctl --no-block isolate iceland-charging.target (the queued desktop start is dropped),
  anything else -> the boot goes on unchanged; at most about 10 s (reader timeout 6 s, retries for 4 s while it
  says unknown), TimeoutStartSec=30, a failure fails only this unit. Exactly one "iceland-charging-detect: ..."
  line per boot in the kernel log; never twice in a boot (/run/iceland/charging-detect, RemainAfterExit,
  IgnoreOnIsolate), never once the display manager runs, never with a target / run level on the command line, a
  missing target or guard unit, a masked guard. Off switches unchanged: iceland.charging=0, CHARGING_PON=0
  (boot.conf's comment still names the generator; the setting is read by the service now)
- iceland-charging-generator: ABL's /chosen/u-boot,abl-boot-mode = charger and iceland.charging=1 only (no PON
  read, no python, no debugfs); as before 0.28-15 for those
- sensors: iio-sensor-proxy and hexagonrpcd (adsp sensorspd) get IgnoreOnIsolate=yes: an isolate (the charging
  mode's way in and out) stopped these udev-started units and nothing started them again; the new
  iceland-ssc-watch.timer (every minute from
  90 s after the boot, AccuracySec 30 s) starts hexagonrpcd + iio-sensor-proxy again when the proxy is down with
  the sensor hub there and no systemd job pending (at most 5 times per boot, one log line each;
  /run/iceland/sensors-off keeps them down). Field finding of 15 Oct: the proxy was stopped cleanly about 5 min
  after the boot and stayed down (no Automatic Brightness switch, no light events)
* Thu Oct 15 2026 mzak <mzak.amin@gmail.com> - 0.28-15
- charging mode (wf/chgmode2): on the installed tablet a power-off with the cable in started the desktop (and U-Boot
  v4's menu). Two causes: this ABL did not hand over "charger" (U-Boot showed its menu), and even if it had, the
  /chosen/u-boot,abl-boot-mode property cannot reach Linux while GRUB loads its own device tree (GRUB_DEVICETREE,
  PER_KERNEL_DT=1): Fedora's GRUB 2.12 (grub2-efi-aa64 2.12-66.fc44) does not call U-Boot's EFI_DT_FIXUP_PROTOCOL
  (no such GUID in grubaa64.efi), so none of U-Boot's fixups are in the device tree Linux gets
- iceland-pon-log (new, /usr/libexec/iceland/): reads the PMK8850's PON log (the PBS event ring in SDAM 0x7400 /
  0x7500, format of stock's pmic-pon-log.ko) read only - from nvmem if a device tree names the SDAMs, else only the
  needed lines of the pmk8850's SPMI regmap in debugfs (in a private mount namespace when debugfs is not mounted
  yet); verdict charger only when the last power-on was triggered by the USB charger alone (no power key, no reset
  trigger, no warm reset after it); unreadable = unknown
- iceland-charging-generator: the PON log verdict "charger" is a second sign of a cable power-on (ABL's mode stays the
  first); one kernel log line with the verdict at every boot; CHARGING_PON=0 in /etc/iceland/boot.conf turns it
  off, iceland.charging=0 still turns everything off
- boot.conf / iceland-grub-setup: the comments no longer claim that GRUB uses the DT fixup protocol; PER_KERNEL_DT
  stays 1 (the trial kernel boots with its own device tree); CHARGING_PON=1 added
- idle power on by default (owner, 15 Oct): iceland-cmdline puts cpuidle.governor=teo (the TEO idle governor;
  menu has the higher rating and would stay without it) and rcu_nocbs=all rcutree.enable_rcu_lazy=1 (RCU callbacks
  of every CPU offloaded and batched lazily) on every boot entry and /etc/kernel/cmdline, before $iceland_args;
  the new 97-iceland-cmdline.install does the same for each new kernel-iceland's entry. Kernel q89i builds both
  (iceland-linux queue 0312); Android's GKI kernel ships TEO and lazy RCU. Off switches in /etc/iceland/boot.conf:
  IDLE_GOV=menu, RCU_LAZY=0 (then run /usr/libexec/iceland/iceland-cmdline; next boot). Context: the owner's
  powerperf runs of 15 Oct (idle, app closed: CPU busy 0.7 %, IPI1 114/s, timer 361/s, system domain 78 %); the
  A/B measurements on the tablet (powerperf.sh --ab-gov / --rcu-lazy) follow
- GPU preemption (no package change): off by default in kernel q89i (iceland-linux queue 0311,
  adreno_device.c enable_preemption default 0); on the installed tablet msm.enable_preemption=0 took the
  'delay in fenced register write' warnings from 3 in 16 min to 0, with no GPU faults, and the owner reports it
  smoother (the measured govtune A/B is still pending). msm.enable_preemption=1 on the kernel command line turns
  it back on (grub2-editenv - set iceland_args=msm.enable_preemption=1, every kernel-iceland entry, until
  grub2-editenv - unset iceland_args); -1 = the per-GPU choice of the driver
* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-14
- the power key has one handler, iceland-battery-guard (owner, 14 Oct: with a charger in and the screen on, a press
  opened GNOME's power-off menu). Cause: 0.28-11's polkit rule refuses login1.*-ignore-inhibit, so
  gnome-settings-daemon saw suspend as not allowed and fell back to its interactive power-off dialog while the guard
  also locked and blanked. The polkit rule stays (nothing may prompt to override the charger block).
- zz_iceland-device.gschema.override: org.gnome.settings-daemon.plugins.power power-button-action='nothing' (also
  the login screen; a running GNOME reads it at its next start: log out and in, or reboot); a user who picks
  another action in Settings > Power makes GNOME act on the key as well, and the guard's journal line says so
  (gsettings read as the session user)
- iceland-battery-guard watches the power key always, acting at the release as 0.28-10 (once per press, auto-repeat
  and SYN_DROPPED handled, at most one action per second, one journal line per action): the panel off at the press
  (DSI dpms Off or bl_power != 0), the screen saver on, or a press within 3 s of a resume (the press that woke the
  tablet): nothing, the press wakes the screen. Charger in (the guard's block): lock + blank as 0.28-10. No
  charger: suspend as GNOME's 'suspend' did (systemctl suspend as root, never -i; GNOME locks on
  PrepareForSleep); another program's block on sleep (logind ListInhibitors, asked first) or a refused suspend:
  lock + blank instead, said in the line. battery-guard.conf: POWER_KEY_SUSPEND=1 (0 = nothing without a
  charger; GNOME's setting then decides); POWER_KEY_BLANK keeps its meaning (the charger case)

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-13
- charging mode (wf/chgmode): switched off with a USB cable in, the tablet is powered on again by VBUS and ABL starts
  the boot partition in its off-mode charging mode (stock: Android's charging screen); Fedora came up with its
  desktop. With U-Boot patch 0011 (ABL's boot mode in /chosen/u-boot,abl-boot-mode) the new
  iceland-charging-generator makes iceland-charging.target the default target of such a boot: multi-user.target
  without the desktop, so the battery guard (stock limits, JEITA regions, USB-C connector rules, the 85 % limit),
  the thermal policy and the firmware / charger services run as in every boot. iceland-charging.service (under a
  logind handle-power-key / handle-lid-switch lock) keeps the panel dark (bl_power and frame buffer blank; the
  brightness is never written, everything is put back when it stops), powers off once the cable has been out for
  5 s (online and the port's present both 0; an unreadable or undecided reading never counts as out), and starts
  the desktop (isolate graphical.target) at a press of the power key, or after 120 s without any cable. The slot
  mark and the kernel trial confirmation stay with graphical.target: a charging boot marks and confirms nothing.
  Off switch: iceland.charging=0 on the kernel command line; a U-Boot without patch 0011 or any other mode: the
  normal boot as before

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-12
- (govtune, not yet measured on the tablet) iceland-launchboost, stock's app-launch boost
  (perfboostsconfig.xml 0x1081 Type 5: 600 ms, sched_boost 1, minimum 3302400 / 4070400 kHz) as util_min 904
  on the threads of every new unit in the user's app.slice for 600 ms (sched_setattr; systemd 259 has no
  uclamp properties); never above scaling_max_freq, off while the battery guard cuts input, one start per 1 s
- system.slice.d/50-iceland-system-cpus.conf: system services on cpu0-5 (stock's system-background cpuset)
- iceland-performance: stock's performance-mode floors 1785600 / 1747200 kHz (0x1091: 0x6F9 / 0x699 MHz)

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-11
- polkit: 49-iceland-no-sleep-override.rules refuses org.freedesktop.login1.*-ignore-inhibit (suspend,
  hibernate, hybrid-sleep, suspend-then-hibernate) without a prompt. With a charger in the guard blocks sleep;
  GNOME's power key asks to suspend past the block and showed an "authentication required" dialog after the
  screen woke up (owner, 14 Oct, with 0.28-10's lock-and-blank). Without a block nothing changes (logind asks
  for these actions only when a block exists); root is not affected

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-10
- iceland-battery-guard: the power key with a charger in (owner, 14 Oct: on a charger the power key did nothing).
  The guard's logind sleep block (KEEP_AWAKE=1, kept: the guard has to keep enforcing the temperature regions, the
  USB-C connector rules and the 85 % limit) makes logind refuse GNOME's power-button suspend (gnome-settings-daemon
  50.1 SuspendWithFlags(SKIP_INHIBITORS) needs the polkit grant suspend-ignore-inhibit, auth_admin_keep), and GNOME
  has no fallback. Now, only while that block is in force, a short press of the power key (KEY_POWER from the PMIC
  power key's evdev node, found by its capabilities, read only, never grabbed; one select() thread) locks and blanks
  seat0's active graphical session: org.gnome.ScreenSaver.SetActive(true) on that user's session bus (setpriv as
  the user, 3 s time-out; gsd-power blanks the panel when the screen saver comes on), as stock turns the screen off
  while charging. Acts at the release of the press (an event after the blank would light the panel again), once per
  press, auto-repeat ignored, at most one action per second; a screen saver that is on already is left to GNOME (the
  press wakes the screen); GNOME not reachable: loginctl lock-session. One journal line per action. Without a
  charger nothing changes. POWER_KEY_BLANK=1 in battery-guard.conf (0 = as 0.28-9)

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-9
- field report of the installed system (14 Oct 2026), four separate changes, none above stock:
- (1) brightness on the first boot: iceland-backlight-default (a oneshot pulled in by 70-iceland-backlight-default.rules
  when ktz8869-backlight appears, after systemd-backlight, before the display manager) lowers the brightness to stock
  OxygenOS's default, 102 / 255 of stock's manual range 3542 = 1417 (SettingsProvider def_screen_brightness;
  display_brightness_config_P_D.xml), only when systemd-backlight has no saved state for it (the first boot) and
  only once per system (/var/lib/iceland/backlight-default.done); never raises it, never touches the cooling device
  of iceland-thermal's cap. Off: /etc/iceland/backlight-default-off or iceland.nobacklightdefault. The installed
  tablet was at 4095 of 4095 on first use (9.23 W against 2.2-3.0 W at 1305); the driver starts at 2047
- (2) USB-C controller runtime PM: iceland-usb-pm (72-iceland-usb-pm.rules, add / bind of a600000.usb) sets
  power/control to auto (the dwc3 core forbids runtime PM at every probe; with nothing plugged in the USB GDSCs
  stayed on and CX was held at level 256). Never in a rehearsal (iceland.rehearsal=), a RAM kit or any boot whose
  root is not on the tablet's storage, never while a configfs gadget is bound, never with iceland.nousbpm or
  /etc/iceland/usb-pm-off. Host mode is unchanged (xhci-plat keeps its own runtime PM off)
- (3) presets: ModemManager (no modem; disabling also drops the D-Bus alias NetworkManager-wwan would start),
  mdmonitor, mdmonitor-takeover, raid-check.timer (no md in kernel-iceland), smartd (no SMART on UFS) disabled
  (50-iceland-unused.preset); the five ABRT units in their own file (50-iceland-abrt.preset; OWNER DECISION,
  systemd-coredump stays). Applied once per system to units still enabled (/var/lib/iceland/.preset-unused-0.28-9)
- (4) memory: vm.compaction_proactiveness = 0 (60-iceland-vm.conf; stock writes 0 at every boot; kcompactd 4.7 %
  CPU in the owner's measurement) and transparent huge pages madvise (tmpfiles.d/iceland-thp.conf; stock: never)
- not added: a UFS WriteBooster unit (the field report's local one fails: wb_on returns EOPNOTSUPP, WriteBooster
  follows clock scaling by design)
- iceland-slot-mark: the loop-name cleanup kept loop0 as 'loo' (sed 's/p[0-9]*$//'); now
  sed -E 's/^(loop[0-9]+)p[0-9]+$/\1/', so a root on a whole loop device is recognised too (test added)

* Wed Oct 14 2026 mzak <mzak.amin@gmail.com> - 0.28-8
- iceland-thermal: stock's screenOff table (sys_thermal_control_config.xml screenOff section): while the panel is
  off (DSI dpms Off or a backlight's bl_power != 0) the CPU / GPU caps are min(globalPolicy, that entry), a gear
  the section does not list taking the nearest listed gear below it (Battery.apk's lookup); closes the one case
  where 0.28-7 was above stock (screen off at gears 6-8 / 10-12). SCREEN_OFF=1 in thermal.conf (0 = as 0.28-7)
- iceland-thermal: stock's boostCeiling: on touchscreen / pen / touchpad / mouse / keyboard input (evdev, read
  only, never grabbed, one epoll, debounced to 250 ms) the CPU maxima rise to the gear's CPU-level boostCeiling,
  never above the power mode's maximum, until BOOST_HOLD_MS (1000) after the last event and at most boostBreak2
  seconds continuously; never with the screen off, from gear 10 (boostBreak -1), during a kernel cpufreq trip or a
  battery-guard stop, or with the battery reading unknown. BOOST=1 in thermal.conf (0 = no boost). Installed on
  the tablet 14 Oct by hand (tablet/thermal-fix-0.28-8.sh): service active, the five input devices found
- iceland-slot-mark: the installed system was never marked (every boot: "SKIP: / is on '/dev/loop0p3'"; ABL
  counted retry 7 -> 3): the guard now accepts a loop root whose backing file is the partition labelled userdata
  or fedora on /dev/sd* (dracut-iceland-carrier's loop0), and the LUN holding boot_<current slot> (sde), which
  iceland-storage-ro makes read-only, is made writable for the one qbootctl -m only and read-only again right
  after (also on any exit), both logged. RAM kits, loop devices without userdata behind them, NBD roots and
  rehearsals still skip. 14 Oct: the owner marked slot b by hand the same way (Successful 1)

* Tue Oct 13 2026 mzak <mzak.amin@gmail.com> - 0.28-7
- iceland-speaker-default waits for WirePlumber's "default" metadata before it reads or writes the configured
  default output, reads the value back and writes again until WirePlumber holds it, and reports success only
  then; a choice WirePlumber restores meanwhile is kept. r157: the unit ran 40 ms after WirePlumber started,
  pw-metadata found no "default" metadata, changed nothing and exited 0, and the configured default output
  stayed unset (the effective default was still the protected Speakers, by priority)

* Tue Oct 13 2026 mzak <mzak.amin@gmail.com> - 0.28-6
- kernel instead of package (owner, 13 Oct 2026; needs kernel-iceland q89f); switches on: BLCLAMP K3 K7 K6K5 K2
- iceland-thermal: the brightness cap is back, through the kernel (owner's choice, 13 Oct): the ktz8869 backlight
  driver's cooling device "ktz8869-backlight" has one state per temperature gear (max_state 19) with stock's
  per-gear limit built in, and lowers only what the backlight ICs get; the backlight's brightness (GNOME's slider)
  keeps the user's value, so GNOME no longer writes the cap back (r151). The service writes the effective gear to
  its cur_state, only when it changes, 0 on stop / ENABLE=0 / BRIGHTNESS=0, and clears a state an earlier run left.
  No such device (an older kernel) = no brightness cap, one log line. The backlight itself is never written.
  thermal.conf and the daemon default: BRIGHTNESS=1. CPU / GPU / charge caps and the gear table unchanged;
  test_thermal.py / test_thermal_nobl.py follow
- UFS I/O scheduler (K3): kernel-iceland no longer refuses parallel scheduler changes on the LUNs of one tag
  set (block: restart instead of failing a sysfs store on a busy tag set lock), so Fedora's own
  60-block-scheduler.rules sets bfq on the UFS LUNs as on every disk: 60-block-scheduler.rules (/etc),
  61-iceland-ufs-scheduler.rules and iceland-ufs-scheduler are gone
- rear camera focus (K7): the kernel holds the lens at stock's start position 450 while the rear sensor
  streams (dw9719 dongwoon,default-position, sc1320cs lens power, DT); iceland-camera-focus, its unit and
  camera-focus.conf are gone (a changed /etc/iceland/camera-focus.conf stays as .rpmsave)
- wakeup defaults (K6): 72-iceland-nowake.rules removed; the device tree no longer makes the USB controller or
  the Wi-Fi PCIe root port a wakeup source. GPU (K5): 73-iceland-gpu-devfreq.rules removed; 160 MHz is the
  lowest operating point of every speed bin, so devfreq's min_freq is 160 MHz without it
- Wi-Fi address (K2): 74-iceland-wifi-mac.rules, iceland-wifi-mac and iceland-wifi-mac-check.service removed;
  the firmware's address was the same on every boot measured, so the helper never changed it
- kept: iceland-bdaddr(.service) (the boot loader route for the Bluetooth address is deferred) and
  /etc/sysconfig/regdomain (iceland-regdomain)

* Tue Oct 13 2026 mzak <mzak.amin@gmail.com> - 0.28-5
- microphone: stock's 14 dB recorder gain after the echo canceller (owner, 13 Oct; r155: with TX_DEC at stock's
  84 the processed speech was 14 dB lower and the WebRTC gain control did not make up for it). New
  61-iceland-mic-gain.conf: a filter-chain with fast_lookahead_limiter_1913 (input gain +14 dB, ceiling -1 dBFS,
  release 0.25 s) records from the canceller's output and is "Internal microphones (voice processing)"
  (iceland_mic_processed, priority 2000: name, description and default unchanged). The canceller's output is now
  the hidden internal node iceland_mic_aec (Audio/Source/Internal). TX_DEC0/1 stay 84, so the raw source and the
  canceller's input keep stock's headroom; the canceller's settings are unchanged; one off switch for both
  (iceland.mic-processing = false); new test_mic_gain.py

* Mon Oct 12 2026 mzak <mzak.amin@gmail.com> - 0.28-4
- iceland-firmware-fetch + /usr/share/iceland/firmware-pins.tsv (pins 11.A.38-2 14833f71, 11.A.38-3 297669a0):
  iceland-firmware from its GitHub release, sha256-pinned, fail-closed (mismatch: refused and deleted; no
  network: the installed package kept; dnf from the local file with every repository off); the kernel and
  this package keep the local repository (iceland-repo-sync)
- the shell temperature model now comes from iceland-firmware 11.A.38-3 (/etc/iceland/thermal-model.json, a
  package file); the installer no longer decodes it
- updates: the MINIMAL Fedora hold (owner, 13 Oct; = the B run's): 50-iceland-fedora-hold.repo excludes only
  iio-sensor-proxy*, hexagonrpc*, libssc*, alsa-ucm (our UCM includes its shared files), kernel-iceland*, iceland-*;
  GRUB, shim, linux-firmware / *-firmware and libcamera now update from Fedora (Fedora kernels stay refused by
  80-iceland-kernel.conf; GRUB / shim stay protected from removal)
- iceland-thermal: the brightness cap is off by default (thermal.conf BRIGHTNESS=0, the daemon's default 0): the
  backlight is never written by the service (GNOME's own brightness writes fought the sysfs cap, r150 / r150b); the
  cap returns as a kernel clamp in the ktz8869 driver. CPU / GPU / charge caps and the gear table unchanged;
  new test_thermal_nobl.py
- microphone: UCM TX_DEC0/1 Volume 98 -> 84 (stock's own decimator value): the speakers' echo clipped the raw
  capture in the decimator's +14 dB with the tablet upright (r141: 68749 clipped samples); the processed source's
  WebRTC gain control restores the speech level after the echo canceller (stock adds its 14 dB in its DSP). The
  raw source is 14 dB quieter; ADC1/2 stay 14; the voice-processing source unchanged; new test_mic_headroom.py

* Mon Oct 12 2026 mzak <mzak.amin@gmail.com> - 0.28-3
- speakers: louder, toward stock (the owner's choice, 12 Oct; stock's loudness is the aim, not a measured proof): the
  compressor's make-up gain is
  9 dB (owner-chosen; never-above-stock not proven by measurement - references inconclusive; cap 14 dB), the limiter runs at 0 dB input / -1 dBFS (was -3 / -3); the high-pass stays
  150 Hz; the DSP stream (0 dB) and the amplifiers stay at stock; tests/stock_loudness.json records the cap
- speakers: the raw ALSA sink is "Speakers (raw, unprotected)" (priority 100); iceland-speaker-default (user unit)
  makes the protected "Speakers" the configured default output unless the account chose another one
- microphone: the raw source is "Internal microphones (raw)"; the processed source stays the default
- tests: test_stock_levels / test_speaker_protection follow the rule; new test_speaker_default.py
- sensors (A52, kit 144): the sleep hook only stops iio-sensor-proxy and leaves its mark; iceland-ssc-resume.service
  (after suspend.target, outside the suspend transaction) starts hexagonrpcd-adsp-sensorspd and, with the mark,
  iio-sensor-proxy (the hook's own start inside systemd-suspend left the accelerometer 0/3; 3/3 now); new test_ssc_resume.py
- updates (r142): kernel-iceland* and iceland-* excluded from the three Fedora repositories, so a same-named Fedora
  package can never replace ours (iceland-firmware was held by *-firmware already); test_update_policy checks the names

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
