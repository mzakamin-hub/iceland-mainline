# iceland-device

Fedora settings package for the OnePlus Pad 4 (PLAN v4 Phase 4b). Configuration and scripts only: no firmware, no
binaries. `./build-rpm.sh OUT` builds `iceland-device-*.noarch.rpm` (rpmbuild; tested with rpm 4.18).

| File | Installed as | Why |
|---|---|---|
| `80-iceland-kernel.conf` | `/usr/share/dnf5/libdnf.conf.d/` | exclude Fedora's kernels (no Pad 4 support) |
| `sleep-iceland.conf` | `/usr/lib/systemd/sleep.conf.d/60-iceland.conf` | s2idle, the SoC's only sleep state |
| `journald-iceland.conf` | `/usr/lib/systemd/journald.conf.d/60-iceland.conf` | cap the journal at 200 MB |
| `49-iceland-no-system-upgrade.rules` | `/usr/share/polkit-1/rules.d/` | block Fedora version upgrades until tested |
| `iceland-bdaddr(.service)` | `/usr/libexec/iceland/`, systemd unit | apply the tablet's own BT address from `/etc/iceland/bdaddr` (written at install time, never shipped) |
| `iceland-cmdline` | `/usr/libexec/iceland/` | add `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` to all boot entries |
| `90-iceland-dracut.conf` | `/usr/lib/dracut/dracut.conf.d/` | display/touch/GPU drivers + firmware in the initramfs |
| `60-iceland-wifi-powersave.conf` | `/usr/lib/NetworkManager/conf.d/` | Wi-Fi power saving |
| `iceland-battery-guard(.service)` | `/usr/libexec/iceland/`, systemd unit | stock charging limits as a second safety layer (see the file header for each stock value) |
| `machine-info` | `/usr/share/iceland/machine-info`; missing keys added to `/etc/machine-info` | GNOME's About page and `hostnamectl` show "OnePlus Pad 4" (hostnamed prefers this file over the firmware's DMI strings) |
| `81-iceland-ssc.rules` | `/usr/lib/udev/rules.d/` | the sensors behind the ADSP for iio-sensor-proxy: accelerometer + proximity enabled, the mount matrix (stock: Android frame, natural portrait, panel native at ROTATION_90), hexagonrpcd and iio-sensor-proxy started when `/dev/fastrpc-adsp` appears |
| `hexagonrpcd-adsp-sensorspd-iceland.conf` | `/usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d/iceland.conf` | hexagonrpcd (sensors PD) with the tablet's own DSP file tree (`/usr/share/qcom/kaanapali/OnePlus/iceland`, extracted at install time, never shipped) |
| `iio-sensor-proxy-iceland.conf`, `iceland-ssc-wait` | `/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland.conf`, `/usr/libexec/iceland/` | iio-sensor-proxy after hexagonrpcd and only once the accelerometer delivers a sample (it looks for its sensors once) |
| `iceland-ssc-hold.service` | systemd unit (pulled in by iio-sensor-proxy's drop-in) | keeps the accelerometer streaming (`monitor-sensor --accel`): both cameras only answer on their control bus while a sensor of the hub streams |
| `61-iceland-battery.hwdb` | `/usr/lib/udev/hwdb.d/` | `CHARGE_LIMIT=80,85` for the battery: the thresholds UPower writes when GNOME's "Preserve Battery Health" is selected (UPower's default would be 75 / 80) |
| `upower-iceland.conf` | `/usr/lib/systemd/system/upower.service.d/iceland.conf` | UPower starts after udev's first device scan: it reads the charge-limit thresholds only once |
| `iceland-ssc-resume.service` | systemd unit | hexagonrpcd's unit stops for a suspend; this starts it again after the resume |
| (%posttrans) | `/etc/sysconfig/kernel` | `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=yes` |
| (%triggerin fwupd) | `/etc/fwupd/fwupd.conf` | `DisabledPlugins=uefi_capsule` |

Still to add as the hardware work lands: ALSA UCM with volume caps (no speaker playback before TFA9865 protection),
60 Hz on battery, charge limit, lid/keyboard wake tweaks.
