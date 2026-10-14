# 01 - Overview: mainline Linux and Fedora on the OnePlus Pad 4

State: 14 Oct 2026. Fedora 44 GNOME is installed on the tablet since 13 Oct 2026 and the owner uses it. The kernel is
Linux 7.3-rc7 with the Pad 4 queue at head q89g (kernel package `kernel-iceland 7.3.0~rc7.iceland.00426`). The final
golden image of the install was B149 (committed 13 Oct 2026, 15:45); the feature matrix is page v62 (104 rows).

Status (14 Oct 2026): this overview was first written on 2-3 Oct, before the install. The sections below are updated
to the installed state; the survey dates in the other guide files are kept where they describe that earlier work.
Sources for the current state: the feature matrix (`docs/features/features-data.py`, published as `docs/FEATURES.md`
and `docs/features/feature-matrix.html`), `docs/INSTALL-GUIDE.md` (the B149 edition), `docs/KNOWLEDGE.md`.
"Proven" below means a test run showed it; the test runs themselves are not published.

## 1. What the project is

The project brings an upstream Linux kernel and a normal desktop distribution to the **OnePlus Pad 4** tablet:

| Item | Value |
|---|---|
| Device | OnePlus Pad 4, model OPD2514, board codename **iceland** |
| SoC | Qualcomm Snapdragon **SM8850P**: "Kaanapali" in mainline Linux, "canoe" in Android and ABL |
| Kernel | Linux **7.3-rc7** + 132 SM8850 base patches (the OnePlus 15 "infiniti" port, same SoC) + **294 Pad 4 patches** (`iceland-linux` branch `iceland-7.3-rc7-q89g`, tag `q89g`; `patches/0002-iceland/`). The kernel package is `kernel-iceland 7.3.0~rc7.iceland.00426` |
| Boot loader for Linux | **U-Boot** v2026.10-rc5 + patches (`iceland-u-boot`). Since 13 Oct the install build v3 (footered) sits in `boot_b`; the tablet's own boot loader (ABL) starts it |
| Distribution | **Fedora 44 Workstation (GNOME 50)**, aarch64. The owner chose it on 28 Sep 2026. Installed on 13 Oct 2026 |
| Device package | `iceland-device` 0.28-7 in the installed image (B149); 0.28-8 was installed as one file by hand on 14 Oct and is not yet in an image. It carries the install parts, the battery guard (with the charger input cut), the thermal policy, the speaker and microphone defaults, the camera tuning and the update rules |
| Firmware package | `iceland-firmware` 11.A.38-3: the generic firmware files of the Pad 4 (each with its sha256 in a manifest). The unit's own data is never packaged |
| How it is tested | Every test before the install ran from RAM (`fastboot boot`), and nothing was written to the tablet by the project's tools. The install was done by the owner: two writes on 13 Oct 2026 (see `03-BOOT-AND-PARTITIONS.md` and `07-INSTALL-REVIEW.md`) |

The project's repositories are public as of 13-14 Oct 2026 (the history was cleaned of test material first):

| Repo | Content |
|---|---|
| `iceland-linux` | the kernel patch queue (branch and tag `q89g`), `kernel.pin`, the config fragments, `scripts/prepare.sh` and `build.sh`, the Fedora kernel package spec |
| `iceland-mainline` | the guide, plans, knowledge base, feature matrix, device package, sensor packages, install tooling and the firmware manifest (names and hashes only) |
| `iceland-u-boot` | the U-Boot patch queue, `uboot.pin`, build scripts, the install build's record files |
| `iceland-firmware` | the generic firmware package (spec, manifest with sha256 and sources, notices); releases 11.A.38-2 and 11.A.38-3 |

The former RAM-test kits and their logs were removed from the repositories on 13-14 Oct; this guide does not link them.

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

The feature matrix has **104 rows: 83 working, 13 in progress, 5 not started, 3 not planned** (page v62, 14 Oct).
The area totals below are the matrix's own counts (working / in progress / not started / not planned).

| Area | Working / part / todo / out | Highlights (14 Oct) |
|---|---|---|
| Boot and platform | 18 / 2 / 2 / 0 | The install boots from `boot_b` on its own (U-Boot v3 into the EFI boot manager, then Fedora). Fedora through EFI. UFS 2.3 GB/s direct read. Watchdog fed by systemd. Part: slot marking (see section 3) and the SCMI cold-soak check |
| Display and input | 10 / 2 / 0 / 1 | Native 3392x2400 at 30-144 Hz with live switching. Backlight through the kernel's cooling device. Touch ok. Lid and power keys ok. Auto-rotate ok. Part: the pogo keyboard (needs the cover) and smooth drags under load. Out: Night Light (the display path has no gamma stage) |
| Graphics and compute | 7 / 0 / 0 / 0 | Adreno 840: OpenGL ES 3.2 / OpenGL 4.6 and Vulkan 1.4 on Mesa 26.2.4; GNOME is drawn by the GPU. Hardware decode H.264, HEVC (to 4K), VP9, AV1, bit-exact against the reference MD5s. Hardware encode H.264 and HEVC; screen recording on the encoder. Open: camera into the encoder does not negotiate; Chromium and Electron GPU acceleration |
| Audio | 7 / 1 / 2 / 0 | Six speakers at stock values, with a protection chain in PipeWire (+9 dB make-up, the owner's choice). Two microphones (stock's TX_DEC value, with a processed +14 dB chain). Part: the speaker level against Android (the listening check is the owner's). Todo: NXP amplifier protection (closed firmware), headset over USB-C |
| Connectivity | 6 / 2 / 1 / 0 | Wi-Fi 2.4 GHz connected; installed-system speed test about 390 Mbit/s down, 157 up to a nearby server. Bluetooth ok. USB device mode ok. Part: 5 GHz (networks found; a connection with the band recorded is open). Todo: USB host / OTG |
| Power and charging | 8 / 2 / 0 / 1 | Battery reporting and time estimate ok; charge limit 80 / 85 % ("Preserve Battery Health") ok; battery safety guard with stock's limits ok; bypass charging (Quick Settings toggle) ok. Part: charging with the wall chargers (proven on a PC port at 500 mA); pen charging (driver proven without a pen). Out: SuperVOOC / PPS fast charging |
| Thermal | 7 / 0 / 0 / 0 | Stock's skin loop (60 / 61 C) and its 20-gear policy in `iceland-thermal`; the trips of the SoC and the PMIC at stock values. The screen-off table and the boost ceiling are in 0.28-8 (not yet in an image) |
| Sleep and power saving | 7 / 2 / 0 / 0 | s2idle suspend and resume ok (RAM-kit tests and the installed system's suspend). Wi-Fi back about 2 s after wake. Part: wake by cover, keyboard or charger (cover wake from sleep open); overnight drain not measured on the installed system |
| Sensors and camera | 5 / 1 / 0 / 1 | Accelerometer, compass, light and proximity through the sensor hub. Both cameras stream through libcamera (SC1320CS 13 MP rear, SC820CS 8 MP front). Focus fixed at the stock start position (no autofocus). Part: the camera focus row. Out: haptics, modem, NFC, fingerprint (not on this tablet) |
| Software and packaging | 8 / 1 / 0 / 0 | Kernel, device, firmware and update / hold / rollback path proven on B149 and on the installed system. Stock-values audit (nothing above stock). Part: the full GNOME application set (33 of 33 open a window; a by-finger check is the owner's) |

**Measured battery life** (before the install, area-combo-69; battery 53.8-56.7 Wh; screen at 50 %): idle with the screen
on at 60 Hz 3.37 W (about 16-17 h); light use 3.85 W (about 14-15 h); 1080p hardware-decoded video 3.58 W (about 15-16 h);
all cores busy 8.1 W falling to 7.7 W (about 7 h); screen off but awake 0.64 W (about 3.5 days). 120 Hz costs
0.7 W more than 60 Hz. On the installed system, a 60 s read-only power report on 14 Oct (screen on, 120 Hz, one app open)
gave an average of 2.08 W. The first evening (13 Oct) read about 10.7 W, which the owner's first-day load explains.
Standby asleep overnight is not measured yet: it needs one night unplugged with the owner.

## 3. What is not done, and what is not possible

| Item | State (14 Oct) | Why / what is missing |
|---|---|---|
| Fedora installed on the tablet | **done, 13 Oct 2026** | The owner's two writes: `userdata` (write 1, 18:31) and `boot_b` (write 2, 20:47). Fedora booted from `boot_b` at 20:48. Details in `03-BOOT-AND-PARTITIONS.md` section 8 and `07-INSTALL-REVIEW.md` section 8 |
| Slot marking of the installed system | open, fix committed | The boot counter did not mark the installed slot: `iceland-slot-mark` skipped every boot on the loop root, and the retry count fell to 3. The owner marked slot b by hand on 14 Oct. The fix is iceland-device 0.28-8 (committed; not yet in an image or a rehearsal) |
| Dual boot with Android | not started | Owner decision (2 Oct, kept): Fedora only. A dual-boot plan exists as a draft (`docs/DUALBOOT-PLAN.md`); no partition has been changed for it |
| Speaker protection | not started | NXP's TFA protection runs in a closed protocol. The speaker chain in PipeWire (high-pass, compressor, limiter) is the protection in place |
| Headset over USB-C | not started | USB headsets use the normal USB audio driver. Analog headsets need the codec's audio-accessory mode, which is not done |
| USB host / OTG | not started (untested) | The roles switch by themselves (dual-role controller). The owner's keyboard, stick and hub checks are open |
| DisplayPort over USB-C | open (14 Oct) | HPD and EDID work, and GNOME enables DP-1 at 3840x2160, but no picture reaches a portable 4K monitor. Investigation open (see `02-HARDWARE.md` section 3) |
| Wi-Fi 5 GHz connect, 6 GHz | in progress | 5 GHz networks are found; a connection with the band recorded is the owner's check. The country stays the firmware's US |
| PCIe link at suspend | explained, kept as upstream | "Timeout waiting for L2 entry" at every suspend: ath12k resets the Wi-Fi chip before the sleep. It costs about 10 ms; skipping the reset made the next wake fail, so the reset stays |
| Pogo keyboard, pen charging, wake by cover / charger | queued, needs the owner | drivers proven without the accessory; the owner's hand checks remain |
| Deep sleep (AOSS sleep) | in progress | CX collapse is reached. The deepest SoC state is out of reach on mainline: the secure processor has no mainline driver |
| Idle refresh | off by default | 64 mW saved at 60 Hz, but 120 -> 60 Hz switching measured 74.8 Hz; a debug round is needed first |
| Camera into the hardware encoder | open | the camera stream does not negotiate a format with the encoder (VE-CAM). Screen recording on the encoder works |
| Chromium / Electron GPU acceleration | open | an unofficial Electron app's GPU process crash-looped on the installed system and fell back to software rendering. Firefox decodes in software (Fedora's FFmpeg has no V4L2 path) |
| Autofocus | open | the focus motor works, but libcamera's simple pipeline has no autofocus; the lens is held at stock's start position |
| Fast charging (SuperVOOC / PPS) | not planned | OnePlus-proprietary charge pumps and protocol |
| Haptics, modem, NFC, fingerprint, SD card | not on this tablet | the parts are absent (hardware inventory, not published) |

## 4. Safety principles (non-negotiable)

These are the owner's rules. Every procedure in these documents follows them.

1. **RAM boot only until the owner's install.** Tests used `fastboot boot` (the image lives in RAM). Nothing was flashed,
   erased, formatted, wiped, unlocked or relocked by the project's tools, and no slot was switched. Since the install
   (13 Oct 2026) the tablet runs from its own storage; the only storage writes were the owner's two writes below.
2. **No write without the owner's explicit OK, one write at a time.** The install wrote exactly two partitions, `userdata`
   and `boot_b`, each run by the owner after the owner had seen the partition, file, size and SHA-256 and confirmed the
   write. Each write has its own undo and its recorded checksum. Project scripts never contain `fastboot flash`, `erase`,
   `format`, `set_active`, `-w` or `flashing`. The only exception is the owner's own return-to-stock script, which the
   owner runs and confirms (never run so far).
3. **Never write the boot firmware or the per-device data.** The tablet cannot be unbricked at home: there is no
   public emergency-download loader for it. As long as XBL / ABL and their partitions are untouched, fastboot
   (Volume Down + Power) always answers.
4. **Charging safety first.** Every current, voltage, power and temperature limit is stock's value or lower. Values
   come from the Pad 4's own stock sources (device tree, firmware logs, LineageOS logs), never from another device.
5. **Tests are automated and short** (at most about 10 minutes on the tablet). Anything that needs the owner's hands
   or eyes is deferred and listed.
6. **"Hold the tablet" stops every tablet action at once.** And since 2 Oct: **ask the owner to connect the tablet
   and wait for the owner's go before any tablet run.** The tablet is unplugged while it recharges, so no chain may
   sit waiting for adb.
7. **Privacy.**
   - Proprietary firmware, stock tuning and calibration files, the owner's backups and camera traces are never
     committed or published. The generic firmware files (ADSP, CDSP, SoCCP, GPU, Wi-Fi / BT, touch, camera, VPU) are
     published in the firmware package with their sha256 (owner's decision, 11 Oct 2026). The camera sensor driver is in
     the kernel queue, and the camera tuning files are kept out of the public repositories.
   - The serial number, MAC / Bluetooth addresses and network names are masked everywhere.
   - The repositories are public; a file is published only after the privacy guards have checked it.
8. **Firmware is never distributed from the unit.** The generic firmware is published as above; each user extracts the
   unit-specific files from their own tablet, read-only.

## 5. Reading order

| You want to ... | Read |
|---|---|
| understand the hardware as Linux sees it | `02-HARDWARE.md` |
| understand how the tablet boots and what the install changed | `03-BOOT-AND-PARTITIONS.md` |
| build your own kernel and RAM-boot it | `04-BUILD-YOUR-OWN.md` |
| use another distribution (Debian, Arch, postmarketOS-style) | `05-PORTING-TO-OTHER-DISTROS.md` |
| know how the project got here, and its lessons | `06-PROCESS-HISTORY.md` |
| review the install and what it showed | `07-INSTALL-REVIEW.md`, then `docs/INSTALL-PLAN.md` and `docs/INSTALL-GUIDE.md` |
| look up a term | `GLOSSARY.md` |
| find a file | `INDEX.md` |
