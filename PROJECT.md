# OnePlus Pad 4 mainline Linux - project index

**Device:** OnePlus Pad 4, codename `iceland`, model OPD2514, SoC Qualcomm SM8850P (`kaanapali`/`canoe`), A/B partitions,
unlocked boot loader. The stock firmware the project is based on is 11.A.38.

**Goal:** Fedora 44 Workstation (GNOME) on the Pad 4, booted ABL -> U-Boot -> EFI -> GRUB -> our kernel. **Reached on
13 Oct 2026**: Fedora 44 GNOME is installed and boots on the tablet. Other distributions are optional later targets.

Start with [README.md](README.md) for the status and the install guide ([docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md)).
The dated history is in [CHANGELOG.md](CHANGELOG.md), the release notes in [docs/RELEASE-NOTES.md](docs/RELEASE-NOTES.md),
and the guide set in [docs/guide/](docs/guide/).

## Current state (15 Oct 2026)

What works on the installed tablet (the full list, feature by feature: [docs/FEATURES.md](docs/FEATURES.md), 84
working features):

| Stage | State |
|---|---|
| Boot loader: RAM boot of test images (`fastboot boot`) | works; used for every test kit and rehearsal |
| U-Boot on the tablet: display, USB fastboot, UFS, EFI, power-on boot menu | works; the install build v4 is the boot path in `boot_b` |
| Linux 7.3-rc7 through U-Boot EFI (kernel q89k, `7.3.0-rc7-iceland-00436`) | works; the default kernel, updated with dnf |
| Display: native 3392 x 2400, dual DSI with DSC, 30 to 144 Hz, backlight with automatic brightness | works |
| Touch, pen, auto-rotate (tablet mode), lid and power keys | works |
| Wi-Fi 2.4 GHz (WCN7860, ath12k), Bluetooth with pairing | works |
| Battery and USB-C over pmic-glink; charge limits; bypass charging; battery safety guard | works |
| GPU (Adreno 840, Mesa 26.2.4); hardware video decode and encode | works |
| Audio: six speakers with the protection chain, microphones with echo cancellation | works |
| Sleep (s2idle) and resume; deep sleep overnight | works on the installed system |
| Sensors and gyroscope (through the ADSP sensor hub; iio-sensor-proxy 3.9-11.iceland1) | works |
| Cameras: both sensors stream through libcamera; GNOME Camera | works |
| Install on the tablet: Fedora 44 GNOME in `userdata`, U-Boot in `boot_b` | works ([docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md)) |
| Packages: `iceland-device` 0.28-16, `iceland-firmware` 11.A.38-3, `kernel-iceland` 00436 | installed |

## Our repositories (public, GitHub user `mzakamin-hub`)

| Repo | Contents | Licence |
|---|---|---|
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this repo) | status, install guide and design, device facts, the list of working features, `iceland-device` package, firmware manifest and packaging text, sensor and audio notes | GPL-2.0-or-later (scripts) |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | kernel patch queue: Linux v7.3-rc7 + `0001-infiniti` + `0002-iceland`; configs; prepare and build scripts. Current branch `iceland-7.3-rc7-next` (kernel q89k, `7.3.0-rc7-iceland-00436`) | GPL-2.0 |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | U-Boot patch queue: v2026.10-rc5 + infiniti-mainline (14 patches) + Pad 4 board (0002-iceland, 0001-0012); build scripts; install build record (v4 in `boot_b`) | GPL-2.0+ |
| [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) | generic stock 11.A.38 firmware as an RPM (tags 11.A.38-2, 11.A.38-3), manifest, notices | vendor notices kept in the repo |
| `android_device_oneplus_iceland` | Android device tree for the Pad 4 | see the repo |
| [proprietary_vendor_oneplus_iceland](https://github.com/mzakamin-hub/proprietary_vendor_oneplus_iceland) | LineageOS 24.0 vendor tree for the Pad 4 (stock proprietary files and `radio/` images); public since 14 Oct, no unit-specific data | `lineage-24.0` |

The repositories hold sources, scripts and the generic firmware package. The unit's own data is never published: the
partition backups and carves, calibration and key material, the serial, the MAC and Bluetooth addresses, network names,
and the test material. Every binary records its source commits in its build information.

### Where to find things

| What | Where |
|---|---|
| Status and install | [README.md](README.md), [docs/INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md), [docs/INSTALL-PLAN.md](docs/INSTALL-PLAN.md) |
| Release notes (current versions, changes, known limits) | [docs/RELEASE-NOTES.md](docs/RELEASE-NOTES.md) |
| History by date | [CHANGELOG.md](CHANGELOG.md) |
| What works (feature list) | [docs/FEATURES.md](docs/FEATURES.md) |
| Kernel and U-Boot state | [docs/MAINLINE-STATE.md](docs/MAINLINE-STATE.md) |
| Device facts: memory map, reserved memory, I2C / SPI map, stock and live DTs | [docs/device-facts/](docs/device-facts/) |
| Firmware manifest (names, stock source, sha256) | [firmware/manifest.tsv](firmware/manifest.tsv) |
| Generic firmware package (sha256 per file, notices) | [packaging/iceland-firmware/](packaging/iceland-firmware/) |
| Device settings package (`iceland-device`) | [packaging/iceland-device/](packaging/iceland-device/) |
| Sensor programs (hexagonrpc, libssc, iio-sensor-proxy) | [packaging/sensors/](packaging/sensors/), [docs/sensors/](docs/sensors/) |
| Gunyah virtual machines (side package: VM-manager modules, test VMMs, a test guest kernel, smoke test) | [packaging/gunyah/](packaging/gunyah/) |
| Audio topology and UCM | [audio/](audio/) |
| Fedora image build (RAM-boot scripts) | [phase4/](phase4/) |
| Dual-boot helper (untested) | [tools/dualboot/](tools/dualboot/) |
| Kernel pin, patches, configs, port log | iceland-linux: `kernel.pin`, `patches/`, `configs/`, `docs/` |
| U-Boot pin, patches, install build record | iceland-u-boot: `uboot.pin`, `patches/`, `tools/install/` |

Test logs, test kits, the test tools, the rehearsal logs and the project's working records (work log, plans, session
notes) are not published. Where a document refers to them, it says so in plain text.

### Pinned sources

| Component | Pin |
|---|---|
| Linux | [torvalds/linux](https://github.com/torvalds/linux) `v7.3-rc7` (`UPSTREAM_COMMIT` 24a19b953e2a; the queue's `kernel.pin` is authoritative) |
| infiniti kernel base | [infiniti-mainline/linux](https://github.com/infiniti-mainline/linux), the commit in iceland-linux `kernel.pin` |
| Pad 4 kernel series | ported from [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) `iceland-7.2` (bc3e5fc8, authors kept) plus our commits |
| U-Boot | [u-boot/u-boot](https://github.com/u-boot/u-boot) `v2026.10-rc5` (`UPSTREAM_COMMIT` a06e89ab05ea) |
| infiniti U-Boot | [infiniti-mainline/u-boot](https://github.com/infiniti-mainline/u-boot), the commit in iceland-u-boot `uboot.pin` |
| U-Boot install build v3 | commit aac9e744ec6f (`BUILD_INFO-v3`) |
| mkbootimg | [LineageOS/android_system_tools_mkbootimg](https://github.com/LineageOS/android_system_tools_mkbootimg) 808ecd09 |
| Fedora | release 44 (aarch64 Workstation image, then the stable refreshes); GNOME Shell 50.5 |
| Mesa, libcamera, qbootctl | Mesa 26.2.4; libcamera 0.7.1-2 (Fedora stable); qbootctl 0.2.2-2 (Fedora) |
| hexagonrpc, libssc, iio-sensor-proxy | hexagonrpc 0.5.0 snapshot, libssc 0.4.4 snapshot (both held from Fedora); iio-sensor-proxy 3.9 with the sensor-hub patches |

## Reference projects (read, not vendored)

| Project | Used for |
|---|---|
| [map220v/sm8850-mainline](https://github.com/map220v/sm8850-mainline) (`iceland-7.2`) | the Pad 4 device tree and drivers: dual DSI with the NT36536 panel, KTZ8869 backlight, Novatek touch, TFA9865 audio, OPLUS battmgr |
| [infiniti-mainline/linux](https://github.com/infiniti-mainline/linux) | OnePlus 15 (same SoC) kernel: SoC fixes, carve-outs, remoteproc, Iris, CAMSS, DP, ADC5 Gen4 |
| [infiniti-mainline/u-boot](https://github.com/infiniti-mainline/u-boot) | Kaanapali U-Boot: clocks, eUSB2, PMIC, ABL memory-map fixup, fastboot |
| [infiniti-mainline/firmware-oneplus-infiniti](https://github.com/infiniti-mainline/firmware-oneplus-infiniti) | firmware packaging layout |
| [infiniti-mainline/audioreach-topology](https://github.com/infiniti-mainline/audioreach-topology) | the template for the Pad 4 audio topology |
| [SuperTurtleDev/iceland-mainline-kernel-firmware](https://github.com/SuperTurtleDev/iceland-mainline-kernel-firmware) | comparison of the generic firmware files (iceland-firmware keeps the comparison column) |
| tb323fu-linux (Joonhoe Kim) | kernel patches carried in the queue (provenance in iceland-linux); the PipeWire speaker-protection filter (MIT) |
| postmarketOS device notes and [wiki.nura.eco](https://wiki.nura.eco) (OnePlus 15, SM8850) | packaging and known issues of the same SoC |
| [troikoss/gts9wifi-fedora](https://github.com/troikoss/gts9wifi-fedora) | porting method, Fedora packaging, hardware traps |
| [aaronsb/sm-x800-linux](https://github.com/aaronsb/sm-x800-linux) | device-facts layout, firmware manifest format, distro-neutral split |
| [Project-Silicium/Mu-Silicium](https://github.com/Project-Silicium/Mu-Silicium) | SM8850 memory and configuration maps for cross-checks |
| [PrestarLin/oneplus15-mainline](https://github.com/PrestarLin/oneplus15-mainline) | CI pattern, config checks, build information |
| [LeeSiWal/y700-linux](https://github.com/LeeSiWal/y700-linux) | Lenovo Y700 gen 4 (same SoC, a tablet): address cross-checks, thermal and sensor traps |
| [skb8/linux-sm8750](https://github.com/skb8/linux-sm8750) | SM8750 notes |

## Standing rules

- Installing, flashing, unlocking and slot changes are made by hand, after the PC checks; the project's tools never
  write to a device. Test kits only RAM-boot (`fastboot boot`).
- Proprietary firmware is not committed. The one exception is the generic firmware package (`iceland-firmware`), which
  holds the generic ADSP, CDSP, SOCCP, GPU, Wi-Fi / Bluetooth, touch, camera / sensor
  and VPU files there, each with its source and sha256 and the vendor notices. Unit-specific data is never published.
- Repositories are public. Nothing is sent upstream and no maintainer is contacted without the owner's agreement.
- Commits carry the author's name and a `Signed-off-by` line. Commits made by other people keep their authorship.
- Privacy: no serial number, MAC or Bluetooth address, network name, IP address, account name of the owner, local path or
  e-mail address appears in a published file.
