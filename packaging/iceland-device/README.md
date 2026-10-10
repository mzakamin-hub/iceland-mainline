# iceland-device

Fedora settings package for the OnePlus Pad 4 (PLAN v4 Phase 4b). Configuration and scripts only: no firmware, no
binaries. `./build-rpm.sh OUT` builds `iceland-device-*.noarch.rpm` (rpmbuild; tested with rpm 4.18).

| File | Installed as | Why |
|---|---|---|
| `80-iceland-kernel.conf` | `/usr/share/dnf5/libdnf.conf.d/` | dnf never installs Fedora's kernels (no Pad 4 support), a rescue initramfs, modules for other kernels (akmods / dkms), fwupd's EFI parts or other boot loaders; iceland-device, GRUB and shim cannot be removed; kernel-iceland keeps three versions |
| `50-iceland-fedora-hold.repo` | `/usr/share/dnf5/repos.override.d/` | Fedora's updates do not replace GRUB, shim, firmware, the sensor programs or libcamera (ours come from the local repository after a RAM rehearsal). Decision (generator `iceland-device-apps.py`: `HOLD_BOOT_FIRMWARE`); on a tablet an empty file of the same name in `/etc/dnf/repos.override.d/` masks it |
| `51-iceland-fedora-44-pin.repo` | `/usr/share/dnf5/repos.override.d/` | Fedora's repositories stay on release 44 until a new release has passed the RAM rehearsal (GNOME Software upgrades through dnf5daemon, which the polkit rule cannot stop). Decision (`PIN_RELEASE`); an empty file of the same name in `/etc/dnf/repos.override.d/` masks it |
| `sleep-iceland.conf` | `/usr/lib/systemd/sleep.conf.d/60-iceland.conf` | s2idle, the SoC's only sleep state |
| `logind-iceland.conf` | `/usr/lib/systemd/logind.conf.d/60-iceland.conf` | the cover: suspend on battery (opening it wakes), with a charger in lock the session and turn the screen off but stay awake (stock keeps its kernel awake while charging), nothing with an external display |
| `journald-iceland.conf` | `/usr/lib/systemd/journald.conf.d/60-iceland.conf` | cap the journal at 200 MB |
| `49-iceland-no-system-upgrade.rules` | `/usr/share/polkit-1/rules.d/` | block Fedora version upgrades until tested |
| `iceland-bdaddr(.service)` | `/usr/libexec/iceland/`, systemd unit | apply the tablet's own BT address from `/etc/iceland/bdaddr` (written at install time, never shipped) |
| `iceland-cmdline` | `/usr/libexec/iceland/` | removes `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` from every boot entry and `/etc/kernel/cmdline`: the installed system boots as every rehearsal did (R1d-r2g), with unused clocks, power domains and regulators switched off |
| `90-iceland-dracut.conf` | `/usr/lib/dracut/dracut.conf.d/` | display/touch/GPU drivers + firmware in the initramfs |
| `60-iceland-wifi-powersave.conf` | `/usr/lib/NetworkManager/conf.d/` | Wi-Fi power saving |
| `iceland-battery-guard(.service)` | `/usr/libexec/iceland/`, systemd unit | stock charging limits as a second safety layer (see the file header for each stock value); the charge limit (follows the kernel's thresholds = GNOME's "Preserve Battery Health"); keeps the tablet awake while a charger is in; a journal line per charger; takes the smaller charge-current cap of `iceland-thermal` |
| `battery-guard.conf` | `/etc/iceland/` (config, kept on updates) | the guard's settings, one line each (table below) |
| `iceland-thermal(.service)` | `/usr/libexec/iceland/`, systemd unit | stock's skin temperature policy: a shell temperature estimate, 20 gears, CPU / GPU / brightness / charging limits per gear (stock tables, sources in the file header). Only ever lowers limits; the kernel's thermal zones stay underneath. The fitted model (`/etc/iceland/thermal-model.json`) is private and never shipped: without it the battery temperature + 2 C stands in |
| `thermal.conf` | `/etc/iceland/` (config, kept on updates) | the thermal policy's settings, one line each (table below) |
| `machine-info` | `/usr/share/iceland/machine-info`; missing keys added to `/etc/machine-info` | GNOME's About page and `hostnamectl` show "OnePlus Pad 4" (hostnamed prefers this file over the firmware's DMI strings) |
| `81-iceland-ssc.rules` | `/usr/lib/udev/rules.d/` | the sensors behind the ADSP for iio-sensor-proxy: accelerometer + proximity enabled, the mount matrix (stock: Android frame, natural portrait, panel native at ROTATION_90), hexagonrpcd and iio-sensor-proxy started when `/dev/fastrpc-adsp` appears |
| `hexagonrpcd-adsp-sensorspd-iceland.conf` | `/usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d/iceland.conf` | hexagonrpcd (sensors PD) with the tablet's own DSP file tree (`/usr/share/qcom/kaanapali/OnePlus/iceland`, extracted at install time, never shipped) |
| `iio-sensor-proxy-iceland.conf`, `iceland-ssc-wait` | `/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland.conf`, `/usr/libexec/iceland/` | iio-sensor-proxy after hexagonrpcd and only once the accelerometer delivers a sample (it looks for its sensors once) |
| `sc1320cs.yaml`, `sc820cs.yaml` | `/usr/share/libcamera/ipa/simple/` | libcamera software-ISP tuning of the rear / front camera sensor: the black level of the stock camera characteristics (64 / 65 of 1023) and stock's colour-correction matrices (5 / 6 colour temperatures; private repository only) |
| `51-iceland-camera.conf` | `/usr/share/wireplumber/wireplumber.conf.d/` | hides the raw video nodes of the camera subsystem (driver `qcom-camss`) from the desktop's device list; the two libcamera sources stay |
| `iceland-camera-focus(.service)`, `camera-focus.conf` | `/usr/libexec/iceland/`, systemd unit, `/etc/iceland/` | the rear camera's lens at a fixed position while it streams (libcamera's simple pipeline has no autofocus); default 450 = stock's start position |
| `71-iceland-dma-heap.rules` | `/usr/lib/udev/rules.d/` | the CMA dma-heaps (32 MiB) for root only: libcamera's software ISP in the desktop session then allocates its frames from the system heap; four 1080p frames do not fit into CMA (GNOME Camera failed with "Format negotiation failed") |
| `61-iceland-battery.hwdb` | `/usr/lib/udev/hwdb.d/` | `CHARGE_LIMIT=80,85` for the battery: the thresholds UPower writes when GNOME's "Preserve Battery Health" is selected (UPower's default would be 75 / 80) |
| `upower-iceland.conf` | `/usr/lib/systemd/system/upower.service.d/iceland.conf` | UPower starts after udev's first device scan: it reads the charge-limit thresholds only once |
| `iceland-ssc-resume.service` | systemd unit | hexagonrpcd's unit stops for a suspend; this starts it again after the resume |
| `iceland-npu`, `iceland-npu-off.service` | `/usr/bin/`, systemd unit | `iceland-npu on|off|status` for the CDSP (NPU). The kernel starts the CDSP at boot and it idles in its own sleep; a stopped CDSP leaves its CX / DDR votes behind and the SoC no longer reaches CX collapse in suspend until it runs again (deep-sleep runs 66 / 67), so the boot-time stop is opt-in: the unit acts only when `/etc/iceland/npu-off-at-boot` exists |
| `59-iceland-storage-ro.rules`, `iceland-storage-ro` | `/usr/lib/udev/rules.d/`, `/usr/libexec/iceland/` | every partition of the internal storage read-only (kernel flag), hidden from the desktop; userdata (the Fedora disk) is the only exception |
| `60-block-scheduler.rules`, `61-iceland-ufs-scheduler.rules`, `iceland-ufs-scheduler` | `/etc/udev/rules.d/`, `/usr/lib/udev/rules.d/`, `/usr/libexec/iceland/` | Fedora's bfq scheduler for the internal UFS LUNs, set one LUN at a time: they share one blk-mq tag set and the kernel refuses parallel changes (-EBUSY); the /etc copy is Fedora's rule without the UFS LUNs |
| `iceland-carrier`, `module-setup.sh` (dracut module `90iceland`) | `/usr/lib/dracut/modules.d/90iceland/` | the initramfs finds the Fedora disk inside userdata (label `fedora`), sets the other partitions read-only before anything mounts, opens the disk as a loop device; rollback and rehearsal only when the boot entry asks |
| `91-iceland-install.conf` | `/usr/lib/dracut/dracut.conf.d/` | adds the module above (and loop, nbd) to every initramfs |
| `iceland-snapshot`, `iceland-snapshot.actions`, `snapshot.conf` | `/usr/libexec/iceland/`, `/etc/dnf/libdnf5-plugins/actions.d/`, `/etc/iceland/` | a read-only btrfs snapshot of the root before every package transaction (3 kept), each with a "Roll back to ..." boot entry |
| `96-iceland-trial.install`, `iceland-trial`, `iceland-trial-early.service`, `iceland-boot-confirm.service` | `/usr/lib/kernel/install.d/`, `/usr/libexec/iceland/`, systemd units | a new kernel-iceland boots once as a trial (GRUB `next_entry`); it becomes the default only when the desktop is reached |
| `iceland-grub-setup` | `/usr/libexec/iceland/` | GRUB loads each kernel's own device tree, shows its menu 3 s, passes `$iceland_args` |
| `iceland-device.conf` (protected) | `/etc/dnf/protected.d/` | dnf never removes iceland-device or the running kernel-iceland |
| `iceland-fwupd-guard` | `/usr/libexec/iceland/` | also disables fwupd's storage-firmware plug-ins (scsi, ufs) |
| (%posttrans) | `/etc/sysconfig/kernel` | `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=yes` |
| (%triggerin fwupd) | `/etc/fwupd/fwupd.conf` | `DisabledPlugins=` the plug-ins that could write boot code, EFI variables, the storage's own firmware or GPIOs (uefi_capsule, uefi_dbx, uefi_db, uefi_kek, uefi_pk, uefi_mok, uefi_sbat, uefi_recovery, uefi_esrt, android_boot, scsi, emmc, mtd, nvme, gpio, vbe, bootupd) |

## Settings (one line each; these are decisions the owner can change)

`/etc/iceland/battery-guard.conf` (read every few seconds, no restart):

| Setting | Shipped | Meaning |
|---|---|---|
| `LIMIT_SOURCE` | `kernel` | the charge limit comes from the kernel's `charge_control_*_threshold` when the kernel has them (GNOME Settings > Power > Battery Charging decides; 80 / 85 % from `61-iceland-battery.hwdb`). `conf` = always the two numbers below, whatever GNOME's switch says (the behaviour before 0.17) |
| `CHARGE_LIMIT`, `CHARGE_RESUME` | `85`, `80` | the limit on a kernel without its own (or with `LIMIT_SOURCE=conf`); `CHARGE_LIMIT=100` = off |
| `KEEP_AWAKE` | `1` | no suspend by idle, power key or lid while a charger is in, as on stock (the guard keeps watching; the screen still blanks; `systemctl suspend -i` still suspends). `0` = the tablet may sleep on a charger and charging is then left to the charger firmware alone |
| `BLOCK_LID_SWITCH` | `auto` | the cover with a charger in (wf/wake decision E.2, its recommendation): `auto` = the guard blocks sleep only while logind merely locks a closing cover with a charger in (the logind drop-in below): the cover locks the session and the screen goes dark, the tablet stays awake, and it suspends when the charger is pulled with the cover closed. If logind would sleep on a closing cover, or its setting can't be read, the lid switch is blocked as well. `yes` = the lid switch is always blocked on a charger: closing the cover does nothing (the screen stays on) |
| `THERMAL_CAP` | `1` | the guard takes the charge-current cap of `iceland-thermal` when it is lower than its own. `0` = its own limits only |

"Preserve Battery Health" starts switched on: the install scriptlet writes UPower's switch file
(`/var/lib/upower/charging-threshold-status`) once if it does not exist; after that the switch in GNOME Settings
owns it. (Generator `pkg-017.py`: `SEED_LIMIT_ON`.)

`/usr/lib/systemd/logind.conf.d/60-iceland.conf` (the cover; a file in `/etc/systemd/logind.conf.d/` overrides a
line): `HandleLidSwitch=suspend` (on battery), `HandleLidSwitchExternalPower=lock` (with a charger in: the
session locks, the tablet stays awake), `HandleLidSwitchDocked=ignore` (external display). The other wake decisions
of wf/wake (volume keys from sleep, a charger plug waking the tablet) are kernel settings, not in this package.

`/etc/iceland/thermal.conf` (read every period, no restart):

| Setting | Shipped | Meaning |
|---|---|---|
| `ENABLE` | `1` | `0` = the policy is off and its limits are handed back (the kernel's thermal zones stay) |
| `OFFSET_BALANCED` | `-4` | gears added in GNOME's Balanced mode. `-4` (stock's high-performance offset): nothing changes at idle, first CPU cap at 40 C shell temperature. `0` (stock's normal mode): CPUs capped at 2.36 / 1.86 GHz from 33 C, which the tablet reaches at idle; it belongs with the kernel's skin loop at stock's 60 / 61 C trips (today 48 / 51 C) |
| `OFFSET_POWERSAVE`, `OFFSET_PERFORMANCE` | `1`, `-4` | stock's power-save and high-performance offsets |
| `POLICY_PERFORMANCE` | `global` | `benchmark` = the table stock gives its benchmark apps |
| `CPU`, `GPU`, `BRIGHTNESS`, `CHARGE` | `1` | which limits are applied |
| `CHARGE_MA_HIGH` | `3000` | battery-current cap for stock's charge cool-down levels 4 and above; levels 1-3 are stock's 1200 / 1500 / 2000 mA |
| `CHARGE_SHIFT` | `0` | `0` = the charging cool-down never takes a negative mode offset (the careful side); `1` = it shifts with the mode as on stock |
| `PERIOD` | `5` | seconds between samples (stock's estimate is fitted for 5 s) |

## Tests (PC, no tablet)

```
python3 tests/test_units.py files iceland-device.spec
python3 tests/test_spec.py files iceland-device.spec
python3 tests/test_power_profiles.py files
python3 tests/test_refresh.py files/iceland-refresh
python3 tests/test_npu.py files iceland-device.spec
python3 tests/test_battery_guard.py files/iceland-battery-guard
python3 tests/test_guard_kernel_limit.py files/iceland-battery-guard
python3 tests/test_guard_awake.py files/iceland-battery-guard
python3 tests/test_guard_input_suspend.py files/iceland-battery-guard
python3 tests/test_charge_alert.py files/iceland-charge-alert files/iceland-battery-guard
python3 tests/test_thermal.py files/iceland-thermal files/thermal.conf
python3 tests/test_logind.py files iceland-device.spec
python3 tests/test_install_parts.py files
python3 tests/test_pipewire_req.py iceland-device.spec
python3 tests/test_sensor_service.py files
python3 tests/test_cmdline.py files
python3 tests/test_ufs_scheduler.py files iceland-device.spec
python3 tests/test_camera_tuning.py files
python3 tests/test_preset.py files iceland-device.spec
python3 tests/test_selinux.py files
python3 tests/test_modprobe.py files
python3 tests/test_clock.py files
python3 tests/test_guard_bypass.py files/iceland-battery-guard
python3 tests/test_bypassd.py files/iceland-bypassd files/iceland-battery-guard
python3 tests/test_guard_bypass_safety.py files/iceland-battery-guard
python3 tests/test_guard_bypass_cut.py files/iceland-battery-guard
python3 tests/test_readfail.py files/iceland-battery-guard files/iceland-bypassd files/iceland-thermal
python3 tests/test_mic_processing.py files/60-iceland-mic-processing.conf iceland-device.spec ../../audio/ucm/OnePlus-Pad4/HiFi.conf
```

Still to add as the hardware work lands: ALSA UCM with volume caps (no speaker playback before TFA9865 protection),
60 Hz on battery, charge limit, lid/keyboard wake tweaks.
