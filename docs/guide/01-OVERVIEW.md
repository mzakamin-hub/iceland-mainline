# 01 - Overview: mainline Linux and Fedora on the OnePlus Pad 4

State: 15 Oct 2026. Fedora 44 GNOME installs on the tablet and boots from its own storage. The kernel is Linux
7.3-rc7 with the Pad 4 patch queue, packaged as `kernel-iceland`; the working features are listed in
`docs/FEATURES.md`. The install is described in `docs/INSTALL-GUIDE.md`.

"Proven" below means a test run on the tablet showed it; the test runs themselves are not published.

## 1. What the project is

The project brings an upstream Linux kernel and a normal desktop distribution to the **OnePlus Pad 4** tablet:

| Item | Value |
|---|---|
| Device | OnePlus Pad 4, model OPD2514, board codename **iceland** |
| SoC | Qualcomm Snapdragon **SM8850P**: "Kaanapali" in mainline Linux, "canoe" in Android and ABL |
| Kernel | Linux **7.3-rc7** + 132 SM8850 base patches (the OnePlus 15 "infiniti" port, same SoC) + **294 Pad 4 patches** (`iceland-linux` branch `iceland-7.3-rc7-q89g`, tag `q89g`; `patches/0002-iceland/`). The kernel package is `kernel-iceland 7.3.0~rc7.iceland.00426` |
| Boot loader for Linux | **U-Boot** v2026.10-rc5 + patches (`iceland-u-boot`). The install build (with an AVB footer) sits in `boot_b`; the tablet's own boot loader (ABL) starts it |
| Distribution | **Fedora 44 Workstation (GNOME 50)**, aarch64 |
| Device package | `iceland-device` (current release in the README). It carries the install parts, the battery guard (with the charger input cut), the thermal policy, the speaker and microphone defaults, the camera tuning and the update rules |
| Firmware package | `iceland-firmware` 11.A.38-3: the generic firmware files of the Pad 4 (each with its sha256 in a manifest). The unit's own data is never packaged |
| How it is tested | Every change is tested from RAM first (`fastboot boot`); the project's tools write nothing to the tablet. The install consists of two partition writes made by the user (see `03-BOOT-AND-PARTITIONS.md` and `docs/INSTALL-GUIDE.md`) |

The project's repositories are public as of 13-14 Oct 2026 (the history was cleaned of test material first):

| Repo | Content |
|---|---|
| `iceland-linux` | the kernel patch queue (branch and tag `q89g`), `kernel.pin`, the config fragments, `scripts/prepare.sh` and `build.sh`, the Fedora kernel package spec |
| `iceland-mainline` | the guide, the install guide and design, the feature list, the device package, the sensor packages and the firmware manifest (names and hashes only) |
| `iceland-u-boot` | the U-Boot patch queue, `uboot.pin`, build scripts, the install build's record files |
| `iceland-firmware` | the generic firmware package (spec, manifest with sha256 and sources, notices); releases 11.A.38-2 and 11.A.38-3 |

The RAM-test kits, their logs and the project's working records are not published.

### The software stack in one picture

```
GNOME 50.5 (Wayland, mutter) - GNOME Camera (Snapshot), GNOME Web, Firefox, Settings (power modes, charge limit)
PipeWire + WirePlumber | libcamera 0.7.1-2 (simple pipeline, GPU soft ISP, our fixes)
iio-sensor-proxy 3.9 (patched) <- libssc <- hexagonrpcd   | UPower (charge thresholds) | tuned-ppd (power modes)
Mesa 26.2.4: freedreno (OpenGL / ES), turnip (Vulkan)      | GStreamer v4l2 (Iris video; one colorimetry patch)
iceland-device: udev rules, ALSA UCM + AudioReach topology, battery guard, thermal policy, systemd drop-ins, update rules
Fedora 44 user space (systemd, dnf5, SELinux targeted); GRUB and shim from Fedora, held
Linux 7.3-rc7 + infiniti (132) + Pad 4 queue (294): DRM/MSM, ath12k, qcom_battmgr, remoteproc, Iris, CAMSS, ...
U-Boot v2026.10-rc5 (EFI) <- ABL <- XBL / firmware (stock, untouched)
Tablet firmware (GPU zap, video, ADSP / CDSP, Wi-Fi, BT, touch, sensor-hub files): from the tablet and the generic set
```

## 2. What works today

The working features, area by area (the full list is `docs/FEATURES.md`):

| Area | What works |
|---|---|
| Boot and platform | The install boots from `boot_b` on its own (U-Boot's install build into the EFI boot manager, then Fedora). Fedora through EFI. UFS 2.3 GB/s direct read. Watchdog fed by systemd |
| Display and input | Native 3392x2400 at 30-144 Hz with live switching. Backlight through the kernel's cooling device. Touch ok. Lid and power keys ok. Auto-rotate ok |
| Graphics and compute | Adreno 840: OpenGL ES 3.2 / OpenGL 4.6 and Vulkan 1.4 on Mesa 26.2.4; GNOME is drawn by the GPU. Hardware decode H.264, HEVC (to 4K), VP9, AV1, bit-exact against the reference MD5s. Hardware encode H.264 and HEVC; screen recording on the encoder |
| Audio | Six speakers at stock values, with a protection chain in PipeWire (+9 dB make-up). Two microphones (stock's TX_DEC value, with a processed +14 dB chain) |
| Connectivity | Wi-Fi 2.4 GHz connected; installed-system speed test about 390 Mbit/s down, 157 up to a nearby server. Bluetooth ok. USB device mode ok |
| Power and charging | Battery reporting and time estimate ok; charge limit 80 / 85 % ("Preserve Battery Health") ok; battery safety guard with stock's limits ok; bypass charging (Quick Settings toggle) ok |
| Thermal | Stock's skin loop (60 / 61 C) and its 20-gear policy in `iceland-thermal`; the trips of the SoC and the PMIC at stock values |
| Sleep and power saving | s2idle suspend and resume ok (RAM-kit tests and the installed system's suspend). Wi-Fi back about 2 s after wake |
| Sensors and camera | Accelerometer, compass, light and proximity through the sensor hub. Both cameras stream through libcamera (SC1320CS 13 MP rear, SC820CS 8 MP front), focus at the stock start position |
| Software and packaging | Kernel, device, firmware and update / hold / rollback path proven on the install image and on the installed system. Stock-values audit (nothing above stock) |

**Measured battery life** (before the install, area-combo-69; battery 53.8-56.7 Wh; screen at 50 %): idle with the screen
on at 60 Hz 3.37 W (about 16-17 h); light use 3.85 W (about 14-15 h); 1080p hardware-decoded video 3.58 W (about 15-16 h);
all cores busy 8.1 W falling to 7.7 W (about 7 h); screen off but awake 0.64 W (about 3.5 days). 120 Hz costs
0.7 W more than 60 Hz. On the installed system, a 60 s read-only power report (screen on, 120 Hz, one app open) gave an
average of 2.08 W.

## 3. Safety principles (non-negotiable)

Every procedure in these documents follows them.

1. **Test from RAM first.** Tests use `fastboot boot` (the image lives in RAM). The project's tools never flash,
   erase, format, wipe, unlock or relock anything, and never switch slots.
2. **Two writes, each with its own undo.** The install writes exactly two partitions, `userdata` and `boot_b`, one at
   a time, each with a recorded checksum that is checked again right before the write. Project scripts never contain
   `fastboot flash`, `erase`, `format`, `set_active`, `-w` or `flashing`; only the return to stock uses some of them.
3. **Never write the boot firmware or the per-device data.** The tablet cannot be unbricked at home: there is no
   public emergency-download loader for it. As long as XBL / ABL and their partitions are untouched, fastboot
   (Volume Down + Power) always answers.
4. **Charging safety first.** Every current, voltage, power and temperature limit is stock's value or lower. Values
   come from the Pad 4's own stock sources (device tree, firmware logs, LineageOS logs), never from another device.
5. **Tests are automated and short** (at most about 10 minutes on the tablet).
6. **A stop word stops every tablet action at once**, and no test waits on a tablet that is not connected.
7. **Privacy.**
   - Unit-specific data (calibration files, partition backups, camera traces) and the stock tuning files are never
     committed or published. The generic firmware files (ADSP, CDSP, SoCCP, GPU, Wi-Fi / BT, touch, camera, VPU) are
     published in the firmware package with their sha256. The camera sensor driver is in
     the kernel queue, and the camera tuning files are kept out of the public repositories.
   - The serial number, MAC / Bluetooth addresses and network names are masked everywhere.
   - The repositories are public; a file is published only after the privacy guards have checked it.
8. **Firmware is never distributed from the unit.** The generic firmware is published as above; each user extracts the
   unit-specific files from their own tablet, read-only.

## 4. Reading order

| You want to ... | Read |
|---|---|
| understand the hardware as Linux sees it | `02-HARDWARE.md` |
| understand how the tablet boots and what the install changed | `03-BOOT-AND-PARTITIONS.md` |
| build your own kernel and RAM-boot it | `04-BUILD-YOUR-OWN.md` |
| use another distribution (Debian, Arch, postmarketOS-style) | `05-PORTING-TO-OTHER-DISTROS.md` |
| install Fedora, and know its risks | `docs/INSTALL-GUIDE.md`, `docs/INSTALL-PLAN.md` and `07-INSTALL-REVIEW.md` |
| look up a term | `GLOSSARY.md` |
| find a file | `INDEX.md` |
