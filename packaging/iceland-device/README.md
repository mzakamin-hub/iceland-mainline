# iceland-device

Fedora settings package for the OnePlus Pad 4. Configuration and scripts only: no firmware, no binaries. It is part of
the install image and is updated with dnf on the installed tablet. 0.28-8 makes the slot marking work on the installed
layout; 0.28-9 adds the brightness, USB runtime PM, unused-services and memory settings. `build-rpm.sh OUT` builds `iceland-device-*.noarch.rpm` (rpmbuild; tested with rpm 4.18).

| File | Installed as | Why |
|---|---|---|
| `80-iceland-kernel.conf` | `/usr/share/dnf5/libdnf.conf.d/` | dnf never installs Fedora's kernels (no Pad 4 support), a rescue initramfs, modules for other kernels (akmods / dkms), fwupd's EFI parts or other boot loaders; iceland-device, GRUB and shim cannot be removed; kernel-iceland keeps three versions; an upgrade that cannot be resolved with the holds is skipped, the rest updates (`best=False`, `skip_broken=True`; also for GNOME Software through dnf5daemon) |
| `50-iceland-fedora-hold.repo` | `/usr/share/dnf5/repos.override.d/` | the MINIMAL hold (0.28-4): Fedora's updates do not replace the sensor programs or alsa-ucm (the UCM data our sound profile includes; ours come from the local repository after a RAM rehearsal); GRUB, shim, firmware and libcamera update from Fedora, and a same-named Fedora package can never replace ours (`kernel-iceland*`, `iceland-*`: only `iceland-local` supplies them). Decision (generator `iceland-device-apps.py`: `HOLD_BOOT_FIRMWARE`); on a tablet an empty file of the same name in `/etc/dnf/repos.override.d/` masks it |
| `51-iceland-fedora-44-pin.repo` | `/usr/share/dnf5/repos.override.d/` | Fedora's repositories stay on release 44 until a new release has passed the RAM rehearsal (GNOME Software upgrades through dnf5daemon, which the polkit rule cannot stop). Decision (`PIN_RELEASE`); an empty file of the same name in `/etc/dnf/repos.override.d/` masks it |
| `sleep-iceland.conf` | `/usr/lib/systemd/sleep.conf.d/60-iceland.conf` | s2idle, the SoC's only sleep state |
| `logind-iceland.conf` | `/usr/lib/systemd/logind.conf.d/60-iceland.conf` | the cover: suspend on battery (opening it wakes), with a charger in lock the session and turn the screen off but stay awake (stock keeps its kernel awake while charging), nothing with an external display |
| `journald-iceland.conf` | `/usr/lib/systemd/journald.conf.d/60-iceland.conf` | cap the journal at 200 MB |
| `49-iceland-no-system-upgrade.rules` | `/usr/share/polkit-1/rules.d/` | block Fedora version upgrades until tested |
| `iceland-bdaddr(.service)` | `/usr/libexec/iceland/`, systemd unit | apply the tablet's own BT address from `/etc/iceland/bdaddr` (written at install time, never shipped) |
| `iceland-cmdline` | `/usr/libexec/iceland/` | removes `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` from every boot entry and `/etc/kernel/cmdline` (the installed system boots as every rehearsal did, R1d-r2g, with unused clocks, power domains and regulators switched off); since 0.28-15 it also puts the idle-power options there, switched in `/etc/iceland/boot.conf`: `IDLE_GOV=teo` -> `cpuidle.governor=teo` (`menu` removes it), `RCU_LAZY=1` -> `rcu_nocbs=all rcutree.enable_rcu_lazy=1` (`0` removes them); run it after a change, it acts at the next boot |
| `90-iceland-dracut.conf` | `/usr/lib/dracut/dracut.conf.d/` | display/touch/GPU drivers + firmware in the initramfs |
| `60-iceland-wifi-powersave.conf` | `/usr/lib/NetworkManager/conf.d/` | Wi-Fi power saving |
| `iceland-battery-guard(.service)` | `/usr/libexec/iceland/`, systemd unit | stock charging limits as a second safety layer (see the file header for each stock value); the charge limit (follows the kernel's thresholds = GNOME's "Preserve Battery Health"); keeps the tablet awake while a charger is in; a journal line per charger; takes the smaller charge-current cap of `iceland-thermal` |
| `battery-guard.conf` | `/etc/iceland/` (config, kept on updates) | the guard's settings, one line each (table below) |
| `iceland-thermal(.service)` | `/usr/libexec/iceland/`, systemd unit | stock's skin temperature policy: a shell temperature estimate, 20 gears, CPU / GPU / brightness / charging limits per gear (stock tables, sources in the file header). Only ever lowers limits; the kernel's thermal zones stay underneath. The stock shell-temperature model is `/etc/iceland/thermal-model.json`, owned by `iceland-firmware` (since 0.28-4; generic, decoded from stock's configuration); without it the battery temperature + 2 C stands in |
| `thermal.conf` | `/etc/iceland/` (config, kept on updates) | the thermal policy's settings, one line each (table below) |
| `machine-info` | `/usr/share/iceland/machine-info`; missing keys added to `/etc/machine-info` | GNOME's About page and `hostnamectl` show "OnePlus Pad 4" (hostnamed prefers this file over the firmware's DMI strings) |
| `81-iceland-ssc.rules` | `/usr/lib/udev/rules.d/` | the sensors behind the ADSP for iio-sensor-proxy: accelerometer + proximity enabled, the mount matrix (stock: Android frame, natural portrait, panel native at ROTATION_90), hexagonrpcd and iio-sensor-proxy started when `/dev/fastrpc-adsp` appears |
| `hexagonrpcd-adsp-sensorspd-iceland.conf` | `/usr/lib/systemd/system/hexagonrpcd-adsp-sensorspd.service.d/iceland.conf` | hexagonrpcd (sensors PD) with the tablet's own DSP file tree (`/usr/share/qcom/kaanapali/OnePlus/iceland`, extracted at install time, never shipped) |
| `iio-sensor-proxy-iceland.conf`, `iceland-ssc-wait` | `/usr/lib/systemd/system/iio-sensor-proxy.service.d/iceland.conf`, `/usr/libexec/iceland/` | iio-sensor-proxy after hexagonrpcd and only once the accelerometer delivers a sample (it looks for its sensors once) |
| `sc1320cs.yaml`, `sc820cs.yaml` | `/usr/share/libcamera/ipa/simple/` | libcamera software-ISP tuning of the rear / front camera sensor: the black level of the stock camera characteristics (64 / 65 of 1023) and stock's colour-correction matrices (5 / 6 colour temperatures; private repository only) |
| `51-iceland-camera.conf` | `/usr/share/wireplumber/wireplumber.conf.d/` | hides the raw video nodes of the camera subsystem (driver `qcom-camss`) from the desktop's device list; the two libcamera sources stay |
| `71-iceland-dma-heap.rules` | `/usr/lib/udev/rules.d/` | the CMA dma-heaps (32 MiB) for root only: libcamera's software ISP in the desktop session then allocates its frames from the system heap; four 1080p frames do not fit into CMA (GNOME Camera failed with "Format negotiation failed") |
| `61-iceland-battery.hwdb` | `/usr/lib/udev/hwdb.d/` | `CHARGE_LIMIT=80,85` for the battery: the thresholds UPower writes when GNOME's "Preserve Battery Health" is selected (UPower's default would be 75 / 80) |
| `upower-iceland.conf` | `/usr/lib/systemd/system/upower.service.d/iceland.conf` | UPower starts after udev's first device scan: it reads the charge-limit thresholds only once |
| `iceland-ssc-resume.service` | systemd unit | hexagonrpcd's unit stops for a suspend; this starts it again after the resume, and iio-sensor-proxy when the sleep hook stopped it (outside the suspend transaction) |
| `iceland-npu`, `iceland-npu-off.service` | `/usr/bin/`, systemd unit | `iceland-npu on|off|status` for the CDSP (NPU). The kernel starts the CDSP at boot and it idles in its own sleep; a stopped CDSP leaves its CX / DDR votes behind and the SoC no longer reaches CX collapse in suspend until it runs again (deep-sleep runs 66 / 67), so the boot-time stop is opt-in: the unit acts only when `/etc/iceland/npu-off-at-boot` exists |
| `iceland-update-check` | `/usr/bin/` | read-only: the upgrades dnf / GNOME Software would apply now, those the hold file keeps back and (as root) those the resolver skips (`dnf5 check-upgrade`, with the three Fedora repositories' excludes disabled, and `dnf5 upgrade --assumeno`) |
| `59-iceland-storage-ro.rules`, `iceland-storage-ro` | `/usr/lib/udev/rules.d/`, `/usr/libexec/iceland/` | every partition of the internal storage read-only (kernel flag), hidden from the desktop; userdata (the Fedora disk) is the only exception |
| `iceland-carrier`, `module-setup.sh` (dracut module `90iceland`) | `/usr/lib/dracut/modules.d/90iceland/` | the initramfs finds the Fedora disk inside userdata (label `fedora`), sets the other partitions read-only before anything mounts, opens the disk as a loop device; rollback and rehearsal only when the boot entry asks |
| `91-iceland-install.conf` | `/usr/lib/dracut/dracut.conf.d/` | adds the module above (and loop, nbd) to every initramfs |
| `iceland-snapshot`, `iceland-snapshot.actions`, `snapshot.conf` | `/usr/libexec/iceland/`, `/etc/dnf/libdnf5-plugins/actions.d/`, `/etc/iceland/` | a read-only btrfs snapshot of the root before every package transaction (3 kept), each with a "Roll back to ..." boot entry |
| `96-iceland-trial.install`, `iceland-trial`, `iceland-trial-early.service`, `iceland-boot-confirm.service` | `/usr/lib/kernel/install.d/`, `/usr/libexec/iceland/`, systemd units | a new kernel-iceland boots once as a trial (GRUB `next_entry`); it becomes the default only when the desktop is reached |
| `97-iceland-cmdline.install` | `/usr/lib/kernel/install.d/` | runs `iceland-cmdline` after a new kernel-iceland's boot entry is written, so a new kernel gets the managed options whichever source kernel-install took them from |
| `iceland-grub-setup` | `/usr/libexec/iceland/` | GRUB loads each kernel's own device tree, shows its menu 3 s, passes `$iceland_args` |
| `iceland-device.conf` (protected) | `/etc/dnf/protected.d/` | dnf never removes iceland-device or the running kernel-iceland |
| `iceland-fwupd-guard` | `/usr/libexec/iceland/` | also disables fwupd's storage-firmware plug-ins (scsi, ufs) |
| (%posttrans) | `/etc/sysconfig/kernel` | `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=yes` |
| `iceland-slot-mark(.service)` | `/usr/libexec/iceland/`, systemd unit | once the desktop is up (+30 s), runs Fedora's `qbootctl -m` to mark the A/B slot good, only when it is not marked yet. It skips in test kits and rehearsals, with `/etc/iceland/slot-mark-off`, and when the root is not on the tablet's storage. Since 0.28-8 it accepts the installed layout (root on a loop device backed by `userdata`) and makes the boot LUN writable for that one call only |
| `iceland-backlight-default(.service)`, `70-iceland-backlight-default.rules` | `/usr/libexec/iceland/`, systemd unit, `/usr/lib/udev/rules.d/` | (0.28-9) the first boot starts at stock's default brightness, 1417 of 4095 (stock: 102 / 255 of its manual range 3542), instead of whatever the backlight holds (the installed tablet was at 4095 on first use). Only when systemd-backlight has no saved state, once per system, never raised; later changes are the user's. Off switch: `/etc/iceland/backlight-default-off` |
| `iceland-usb-pm`, `72-iceland-usb-pm.rules` | `/usr/libexec/iceland/`, `/usr/lib/udev/rules.d/` | (0.28-9) the USB-C controller may runtime-suspend when nothing uses it (the dwc3 core forbids it at every probe). Never in a rehearsal, a RAM kit, a boot whose root is not on the tablet's storage or while a USB gadget is bound. Host mode is unchanged. Off switch: `/etc/iceland/usb-pm-off` or `iceland.nousbpm` |
| `50-iceland-unused.preset`, `50-iceland-abrt.preset` | `/usr/lib/systemd/system-preset/` | (0.28-9) ModemManager (no modem), mdmonitor, mdmonitor-takeover, raid-check.timer (no md RAID), smartd (no SMART on UFS) off; ABRT's five units off in their own file (the owner's decision; systemd-coredump stays). Applied once per system to units still enabled |
| `60-iceland-vm.conf`, `iceland-thp.conf` | `/usr/lib/sysctl.d/`, `/usr/lib/tmpfiles.d/` | (0.28-9) no proactive memory compaction (stock writes 0 at boot; kcompactd took 4.7 % CPU) and transparent huge pages only for programs that ask (`madvise`; stock: `never`) |
| `iceland-firmware-fetch`, `firmware-pins.tsv` | `/usr/bin/`, `/usr/share/iceland/` | fetches a newer `iceland-firmware` release from its GitHub release, checked against the sha256 pins (11.A.38-2, 11.A.38-3); a mismatch is refused and the file deleted; without a network the installed package is kept |
| `iceland-repo-sync`, `iceland-local.repo` | `/usr/bin/`, `/etc/yum.repos.d/` | the local repository from which `kernel-iceland*` and `iceland-*` are updated; the PC fills it |
| `iceland-clock(.service, .timer)` | `/usr/libexec/iceland/`, systemd units | the RTC of this board reads 1970 at power-on; the clock starts from a saved time stamp and NTP corrects it once there is a network |
| `60-iceland-mic-processing.conf`, `61-iceland-mic-gain.conf`, `63-iceland-mic-raw.conf` | PipeWire and WirePlumber drop-ins | microphones: the echo canceller (hidden `iceland_mic_aec`), then a +14 dB limiter with a -1 dBFS ceiling, recording "Internal microphones (voice processing)" (the default); the unprocessed source "Internal microphones (raw)". The decimators TX_DEC0 / TX_DEC1 stay at stock's 84. Off switch: `iceland.mic-processing = false` |
| `62-iceland-speakers.conf`, `62-iceland-speaker-raw.conf`, `iceland-speaker-default(.service)` | PipeWire and WirePlumber drop-ins; user unit | speakers: a protection chain (150 Hz high-pass, compressor with +9 dB make-up, limiter at 0 dB in / -1 dBFS out) in front of "Speakers"; the raw sink is "Speakers (raw, unprotected)". The user unit makes the protected output the default unless the account chose another, and waits for WirePlumber's default metadata. Off switch: `iceland.speaker-protection = false` |
| `iceland-refresh` (user service), `refresh.conf` | `/usr/libexec/iceland/`, `/etc/iceland/` | switches the panel between 60 Hz on battery and 120 Hz on a charger (the defaults; `/etc/iceland/refresh.conf`). The seamless idle refresh is not switched on |
| `iceland-bypassd`, `iceland-bypass.service`, `org.iceland.Bypass*`, the Quick Settings extension | `/usr/libexec/iceland/`, system and session units, `/usr/share/gnome-shell/extensions/` | bypass charging: the "Bypass Charging" toggle in GNOME's Quick Settings. The toggle only asks `iceland-battery-guard` for it; the guard keeps every charging limit |
| `iceland-regdomain` | `/etc/sysconfig/regdomain` | the Wi-Fi regulatory domain (US, the firmware's) |
| (%triggerin fwupd) | `/etc/fwupd/fwupd.conf` | `DisabledPlugins=` the plug-ins that could write boot code, EFI variables, the storage's own firmware or GPIOs (uefi_capsule, uefi_dbx, uefi_db, uefi_kek, uefi_pk, uefi_mok, uefi_sbat, uefi_recovery, uefi_esrt, android_boot, scsi, emmc, mtd, nvme, gpio, vbe, bootupd) |

## Settings (one line each; these are decisions you can change)

`/etc/iceland/battery-guard.conf` (read every few seconds, no restart):

| Setting | Shipped | Meaning |
|---|---|---|
| `LIMIT_SOURCE` | `kernel` | the charge limit comes from the kernel's `charge_control_*_threshold` when the kernel has them (GNOME Settings > Power > Battery Charging decides; 80 / 85 % from `61-iceland-battery.hwdb`). `conf` = always the two numbers below, whatever GNOME's switch says (the behaviour before 0.17) |
| `CHARGE_LIMIT`, `CHARGE_RESUME` | `85`, `80` | the limit on a kernel without its own (or with `LIMIT_SOURCE=conf`); `CHARGE_LIMIT=100` = off |
| `KEEP_AWAKE` | `1` | no suspend by idle, power key or lid while a charger is in, as on stock (the guard keeps watching; the screen still blanks; `systemctl suspend -i` still suspends). `0` = the tablet may sleep on a charger and charging is then left to the charger firmware alone |
| `BLOCK_LID_SWITCH` | `auto` | the cover with a charger in (the wake decision of the PC session, its recommendation): `auto` = the guard blocks sleep only while logind merely locks a closing cover with a charger in (the logind drop-in below): the cover locks the session and the screen goes dark, the tablet stays awake, and it suspends when the charger is pulled with the cover closed. If logind would sleep on a closing cover, or its setting can't be read, the lid switch is blocked as well. `yes` = the lid switch is always blocked on a charger: closing the cover does nothing (the screen stays on) |
| `POWER_KEY_BLANK` | `1` | the power key with a charger in (sleep blocked): a short press locks the session and blanks the screen, as stock turns the screen off while charging. `0` = the guard does nothing with the key on a charger |
| `POWER_KEY_SUSPEND` | `1` | the power key without a charger: a short press suspends (as GNOME's `suspend` did); while another program blocks sleep: lock and blank. `0` = the guard does nothing without a charger. The guard is the key's only handler: GNOME's `power-button-action` is `'nothing'` by the package's default (`zz_iceland-device.gschema.override`); another action picked in Settings > Power makes GNOME act on the key as well (the guard's journal line says so). A press while the screen is off, or right after a wake-up, only wakes the screen |
| `THERMAL_CAP` | `1` | the guard takes the charge-current cap of `iceland-thermal` when it is lower than its own. `0` = its own limits only |

"Preserve Battery Health" starts switched on: the install scriptlet writes UPower's switch file
(`/var/lib/upower/charging-threshold-status`) once if it does not exist; after that the switch in GNOME Settings
owns it. (Generator `pkg-017.py`: `SEED_LIMIT_ON`.)

`/usr/lib/systemd/logind.conf.d/60-iceland.conf` (the cover; a file in `/etc/systemd/logind.conf.d/` overrides a
line): `HandleLidSwitch=suspend` (on battery), `HandleLidSwitchExternalPower=lock` (with a charger in: the
session locks, the tablet stays awake), `HandleLidSwitchDocked=ignore` (external display). The other wake decisions
of the wake decisions (volume keys from sleep, a charger plug waking the tablet) are kernel settings, not in this package.

`/etc/iceland/thermal.conf` (read every period, no restart):

| Setting | Shipped | Meaning |
|---|---|---|
| `ENABLE` | `1` | `0` = the policy is off and its limits are handed back (the kernel's thermal zones stay) |
| `OFFSET_BALANCED` | `-4` | gears added in GNOME's Balanced mode. `-4` (stock's high-performance offset): nothing changes at idle, first CPU cap at 40 C shell temperature. `0` (stock's normal mode): CPUs capped at 2.36 / 1.86 GHz from 33 C, which the tablet reaches at idle; it belongs with the kernel's skin loop at stock's 60 / 61 C trips (today 48 / 51 C) |
| `OFFSET_POWERSAVE`, `OFFSET_PERFORMANCE` | `1`, `-4` | stock's power-save and high-performance offsets |
| `POLICY_PERFORMANCE` | `global` | `benchmark` = the table stock gives its benchmark apps |
| `CPU`, `GPU`, `CHARGE` | `1` | which limits are applied |
| `BRIGHTNESS` | `1` | the brightness cap per gear (0.28-6): the gear goes to the backlight driver's cooling device `ktz8869-backlight` (`cur_state`, one state per gear); the kernel lowers the panel while GNOME's brightness stays the user's. No such device (older kernel) = no cap. `0` = no cap (a state of the service is handed back). The backlight itself is never written |
| `CHARGE_MA_HIGH` | `3000` | battery-current cap for stock's charge cool-down levels 4 and above; levels 1-3 are stock's 1200 / 1500 / 2000 mA |
| `CHARGE_SHIFT` | `0` | `0` = the charging cool-down never takes a negative mode offset (the careful side); `1` = it shifts with the mode as on stock |
| `PERIOD` | `5` | seconds between samples (stock's estimate is fitted for 5 s) |
| `SCREEN_OFF` | `1` | (0.28-8) stock's screen-off table: while the panel is off, the CPU and GPU caps follow stock's screen-off entries. `0` = the 0.28-7 behaviour |
| `BOOST`, `BOOST_HOLD_MS` | `1`, `1000` | (0.28-8) stock's input boost: on touch, pen, touchpad, mouse or keyboard input the CPU maxima rise to the gear's boost ceiling, never above the power mode's maximum, for `BOOST_HOLD_MS` after the last event. `0` = no boost |

## Tests

The package's unit tests (about 40 scripts: the guards, the thermal policy, the speaker and microphone levels, the
slot marking, the update policy and the stock-value checks) ran on the PC before each build. They are not published
in this repository; the test material was removed from the public repositories on 13 and 14 Oct 2026.
