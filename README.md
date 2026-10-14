# iceland-mainline

Mainline Linux for the OnePlus Pad 4 (`iceland`, model OPD2514, Qualcomm SM8850P "Kaanapali"). This repository is the
project's front page and reference set: the status, the install guide, the device facts, the Fedora packaging of the
tablet's settings, the firmware manifest and the audio and sensor notes. The kernel, the U-Boot port and the generic
firmware package live in their own repositories (see [Repositories](#repositories)).

## Status (14 Oct 2026)

- **Fedora 44 with GNOME is installed on the tablet.** The install was done by the owner on 13 Oct 2026 (Fedora in
  `userdata`, U-Boot in `boot_b`). The tablet boots Fedora on its own, and the owner now runs that system.
- **Install image:** golden build B149, accepted by the final rehearsal r158 (0 failures in the regression set).
  - Kernel `7.3.0-rc7-iceland-00426` (queue head q89g): Linux v7.3-rc7 plus 426 patches, 132 from
    infiniti-mainline and 294 for the Pad 4.
  - `iceland-device` 0.28-7 in the image. Version 0.28-8 (14 Oct) fixes the slot marking and adds the screen-off
    thermal table and the input boost ceiling; it is not yet in an image.
  - `iceland-firmware` 11.A.38-3 (generic stock firmware, sha256-pinned) and Fedora's libcamera 0.7.1-2.
  - U-Boot install build v3 in `boot_b`, footered for AVB.
- **Feature matrix** ([docs/FEATURES.md](docs/FEATURES.md), page v62, 14 Oct): 104 rows; 83 working, 13 partly
  working, 5 to do, 3 out of scope.

### What works

Boot through U-Boot and EFI with Fedora's shim and GRUB and our kernel. Display at the panel's native 3392 x 2400 with
dual DSI and DSC, refresh 30 to 144 Hz, touch, pen, lid and power keys, auto-rotate. The Adreno 840 GPU (GL 4.6, Vulkan
1.4 through turnip, Mesa 26.2.4). Hardware video decode (H.264, HEVC, VP9, AV1) and hardware encode of H.264 and HEVC.
Speakers through PipeWire with a protection chain, and the microphones. Wi-Fi 2.4 GHz, Bluetooth, USB device mode.
Battery reporting, charge limits of 80 / 85 % through GNOME, bypass charging, the battery safety guard and low-battery
limiting. Thermal control with stock's skin-temperature policy. Suspend (s2idle) and resume, with the sensors back after
a resume. Accelerometer, compass, light and proximity sensors, and the gyroscope. Both cameras stream through libcamera,
and the rear focus is held at stock's start position.

### What does not work yet

- DisplayPort over USB-C: the monitor is detected but shows no picture (open).
- The camera does not negotiate with the hardware H.264 encoder (open; a new test).
- Chromium and Electron GPU acceleration: an unofficial Electron app fell back to software rendering (open).
- A 5 GHz connection is not confirmed; USB host mode with accessories is not tested.
- The idle refresh is off (it measured 74.8 Hz instead of 60 Hz).
- No autofocus; no fast charging (SuperVOOC / PPS); the speaker amplifiers' DSP protection is closed firmware.
- Dual boot with Android is not started (decision: Fedora only).

The full list, with the evidence for each item, is in [docs/FEATURES.md](docs/FEATURES.md) and
[docs/RELEASE-NOTES.md](docs/RELEASE-NOTES.md).

## How it boots

1. The stock boot loader (ABL, closed) starts `boot_b`, checks its AVB footer and counts the tries of slot b.
2. `boot_b` holds our U-Boot v3 install build. It finds no `fedora` partition, runs the EFI boot manager on the disk
   image in `userdata`, and falls back to USB fastboot if that finds nothing. It never resets or powers off by itself.
3. `userdata` holds the whole Fedora disk image. Its EFI programs are Fedora's shim and GRUB.
4. GRUB loads `kernel-iceland` with the Pad 4 device tree and the initramfs.
5. The root is btrfs on a loop device backed by `userdata`. Every other internal partition is read-only to the running
   system. The boot counter should be marked good by `iceland-slot-mark` (Fedora's `qbootctl -m`). On the installed
   system that marking did not run; the owner marked slot b by hand on 14 Oct, and 0.28-8 fixes the marking.

The install replaced Android's data (LineageOS, from the earlier test phase), and Android no longer starts. The way
back to stock is described in the install guide.

## Install

The procedure, its checks and the way back are in [docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md). Its status note at
the top records what was done on 13 Oct 2026. Installing needs an unlocked boot loader and two partition writes, and
each write is made by hand after its own checks. Nothing in this repository writes to a device.

## Repositories

All repositories are public under the GitHub user `mzakamin-hub`.

| Repository | What it holds |
|---|---|
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this one) | Status, install guide, device facts, the Fedora packaging of the tablet's settings (`iceland-device`), the firmware manifest, the sensor and audio notes, the feature matrix. |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | The kernel: the patch queue on Linux v7.3-rc7 (branch `iceland-7.3-rc7-q89g`, tag `q89g`), the configs and the build scripts. Its default branch `main` is the same queue. |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | The U-Boot port on v2026.10-rc5: the infiniti-mainline base, the Pad 4 board patches, the install build (v3) and its build scripts. |
| [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) | The generic stock 11.A.38 firmware as an RPM (tags 11.A.38-2 and 11.A.38-3), with a manifest of sha256 sums and the vendor notices. Unit-specific data is never in it. |
| [android_device_oneplus_iceland](https://github.com/mzakamin-hub/android_device_oneplus_iceland) | The LineageOS 24.0 device tree for the Pad 4 (branch `lineage-24.0`), from the Android test phase before the install. |
| [proprietary_vendor_oneplus_iceland](https://github.com/mzakamin-hub/proprietary_vendor_oneplus_iceland) | The LineageOS 24.0 vendor tree for the Pad 4: the stock proprietary files and `radio/` firmware images that go with the device tree. Made public on 14 Oct 2026; it holds no unit-specific data. |

## Documents

- [PROJECT.md](PROJECT.md): the project index, the pinned sources, the reference projects and the standing rules.
- [CHANGELOG.md](CHANGELOG.md): the dated history, newest first.
- [docs/RELEASE-NOTES.md](docs/RELEASE-NOTES.md): the release notes: the RC1 record of 3 Oct and the final build of 14 Oct.
- [docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md) and [docs/INSTALL-PLAN.md](docs/INSTALL-PLAN.md): the install.
- [docs/DUALBOOT-PLAN.md](docs/DUALBOOT-PLAN.md): the dual-boot plan (not started).
- [docs/PLAN.md](docs/PLAN.md), [docs/KNOWLEDGE.md](docs/KNOWLEDGE.md) and [docs/TODO.md](docs/TODO.md): the port plan,
  the knowledge base and the to-do list.
- [docs/FEATURES.md](docs/FEATURES.md): the feature matrix.
- [docs/MAINLINE-STATE.md](docs/MAINLINE-STATE.md) and [docs/PROJECT-STATE.md](docs/PROJECT-STATE.md): the state of the
  kernel and U-Boot work, and the project snapshot.
- [docs/device-facts/](docs/device-facts/) and [docs/guide/](docs/guide/): the device facts and the guide set.
- [firmware/README.md](firmware/README.md), [packaging/](packaging/), [phase4/README.md](phase4/README.md) and
  [tools/dualboot/README.md](tools/dualboot/README.md): the firmware manifest, the packages, the Fedora image build and
  the dual-boot tool.

## Credits

- **infiniti-mainline** (OnePlus 15, the same SoC): the base of the kernel patch series (0001-infiniti) and of the U-Boot
  port, and the firmware packaging layout.
- **map220v** (`sm8850-mainline`): the Pad 4 device tree and drivers that the Pad 4 series was ported from, with the
  authors kept.
- **SuperTurtleDev**: the firmware repository for the Pad 4, used to compare firmware files.
- **tb323fu-linux** (Joonhoe Kim): patches carried in the kernel queue (their provenance is recorded in iceland-linux),
  and the PipeWire speaker-protection filter, adapted under the MIT licence.
- Other references read for this port: troikoss (gts9wifi-fedora), aaronsb (sm-x800-linux), Project-Silicium
  (Mu-Silicium), PrestarLin (oneplus15-mainline), LeeSiWal (y700-linux), skb8 (linux-sm8750), and the postmarketOS and
  Nura notes on the OnePlus 15.
- The upstream projects this work depends on: Linux, U-Boot, Mesa, GNOME, PipeWire, WirePlumber, libcamera, hexagonrpc
  and libssc (linux-msm and Dylan Van Assche), iio-sensor-proxy, LineageOS (mkbootimg) and Fedora.
