# iceland-mainline

Mainline Linux for the OnePlus Pad 4 (`iceland`, model OPD2514, Qualcomm SM8850P "Kaanapali"). This repository is the
project's front page and reference set: the status, the install guide, the device facts, the Fedora packaging of the
tablet's settings, the firmware manifest and the audio and sensor notes. The kernel, the U-Boot port and the generic
firmware package live in their own repositories (see [Repositories](#repositories)).

## Status (15 Oct 2026)

- **Fedora 44 with GNOME is installed on the tablet** (13 Oct 2026: Fedora in `userdata`, U-Boot in `boot_b`). The
  tablet boots Fedora on its own, and the owner runs that system.
- **Current versions on the tablet:**
  - Kernel `7.3.0-rc7-iceland-00436` (q89k): Linux v7.3-rc7 plus the Pad 4 patch queue, from the iceland-linux branch
    `iceland-7.3-rc7-next`, packaged as `kernel-iceland`.
  - `iceland-device` 0.28-16 (the tablet's settings) and `iio-sensor-proxy` 3.9-11.iceland1.
  - `iceland-firmware` 11.A.38-3 (generic stock firmware, sha256-pinned) and Fedora's libcamera 0.7.1-2.
  - U-Boot install build v4 in `boot_b`, footered for AVB, with a power-on boot menu on the keys.
- **What works:** [docs/FEATURES.md](docs/FEATURES.md) lists the 84 features that work today.

### What works

Boot through U-Boot and EFI with Fedora's shim and GRUB and our kernel, with kernel updates through dnf. Display at the
panel's native 3392 x 2400 with dual DSI and DSC, refresh 30 to 144 Hz, backlight with automatic brightness, touch, pen,
lid and power keys, auto-rotate in tablet mode. The Adreno 840 GPU (OpenGL 4.6, Vulkan 1.4 through turnip, Mesa
26.2.4). Hardware video decode (H.264, HEVC, VP9, AV1) and hardware encode of H.264 and HEVC, also for GNOME's screen
recording. All six speakers through PipeWire with a protection chain, and the microphones with echo cancellation.
Wi-Fi 2.4 GHz, Bluetooth with pairing in GNOME, USB device mode. Battery reporting and time estimate, charge limits of
80 / 85 % through GNOME, bypass charging, the battery safety guard and low-battery limiting. Thermal control with
stock's limits and skin-temperature policy. Suspend (s2idle) and resume, with deep sleep overnight at about 0.35 % per
hour. Accelerometer, compass, light and proximity sensors, and the gyroscope. Both cameras stream through libcamera,
and GNOME Camera works with both.

Each item, with what was measured, is in [docs/FEATURES.md](docs/FEATURES.md).

## How it boots

1. The stock boot loader (ABL, closed) starts `boot_b`, checks its AVB footer and counts the tries of slot b.
2. `boot_b` holds our U-Boot v4 install build. It shows a short boot menu (Fedora by default, or the boot loader's
   fastboot), finds no `fedora` partition, runs the EFI boot manager on the disk image in `userdata`, and falls back
   to USB fastboot if that finds nothing. It never resets or powers off by itself.
3. `userdata` holds the whole Fedora disk image. Its EFI programs are Fedora's shim and GRUB.
4. GRUB loads `kernel-iceland` with the Pad 4 device tree and the initramfs.
5. The root is btrfs on a loop device backed by `userdata`. Every other internal partition is read-only to the running
   system. Slot b is marked successful with Fedora's `qbootctl -m`.

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
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this one) | Status, install guide, device facts, the Fedora packaging of the tablet's settings (`iceland-device`), the firmware manifest, the sensor and audio notes, the list of working features. |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | The kernel: the patch queue on Linux v7.3-rc7 (current branch `iceland-7.3-rc7-next`, kernel q89k `7.3.0-rc7-iceland-00436`), the configs and the build scripts. |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | The U-Boot port on v2026.10-rc5: the infiniti-mainline base, the Pad 4 board patches, the install build (v4) and its build scripts. |
| [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) | The generic stock 11.A.38 firmware as an RPM (tags 11.A.38-2 and 11.A.38-3), with a manifest of sha256 sums and the vendor notices. Unit-specific data is never in it. |
| [android_device_oneplus_iceland](https://github.com/mzakamin-hub/android_device_oneplus_iceland) | The LineageOS 24.0 device tree for the Pad 4 (branch `lineage-24.0`), from the Android test phase before the install. |
| [proprietary_vendor_oneplus_iceland](https://github.com/mzakamin-hub/proprietary_vendor_oneplus_iceland) | The LineageOS 24.0 vendor tree for the Pad 4: the stock proprietary files and `radio/` firmware images that go with the device tree. Made public on 14 Oct 2026; it holds no unit-specific data. |

## Documents

- [PROJECT.md](PROJECT.md): the project index, the pinned sources, the reference projects and the standing rules.
- [CHANGELOG.md](CHANGELOG.md): the dated history, newest first.
- [docs/RELEASE-NOTES.md](docs/RELEASE-NOTES.md): the release notes: the RC1 record of 3 Oct and the final build of 14 Oct.
- [docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md) and [docs/INSTALL-PLAN.md](docs/INSTALL-PLAN.md): the install.
- [docs/DUALBOOT-PLAN.md](docs/DUALBOOT-PLAN.md): the dual-boot plan.
- [docs/PLAN.md](docs/PLAN.md) and [docs/KNOWLEDGE.md](docs/KNOWLEDGE.md): the port plan and the knowledge base.
- [docs/FEATURES.md](docs/FEATURES.md): what works, feature by feature.
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
