# 04 - Build your own kernel, U-Boot and packages for the OnePlus Pad 4

State: 14 Oct 2026. The kernel is Linux 7.3-rc7 with the queue head `q89g` (branch `iceland-7.3-rc7-q89g`, tag `q89g`).
U-Boot is `v2026.10-rc5` with the install build v3. The packages are `iceland-device` 0.28-8 and `iceland-firmware`
11.A.38-3. Fedora 44 GNOME has been installed on the owner's tablet since 13 Oct 2026 (`INSTALL-GUIDE.md`).

The project develops on Windows 11 with WSL (Ubuntu 24.04). **Steps marked "untested here" were not run that way by
the project.** The scripts named in this guide are the ones in the public repositories. The project's test tooling
(the RAM-kit builder, the runners and their logs) is not published, and this guide does not depend on it.

> **WARNING - read before anything else**
> - The builds in this guide touch only your PC. The one tablet step is a RAM boot (`fastboot boot`), which loads an
>   image into memory; a reboot returns the tablet to its installed boot.
> - To RAM-boot at all, the boot loader must be **unlocked**. Unlocking **erases all data** on the tablet and is
>   your decision, at your own risk (section 1.3).
> - Never type `fastboot flash`, `erase`, `format`, `-w`, `set_active` or `flashing lock` while following this
>   guide. None of them is needed here. Writing a partition is the install, a separate documented decision
>   (`INSTALL-GUIDE.md`).
> - Firmware from your tablet is proprietary. Keep your own extraction on your own machine. The generic firmware is
>   published (section 5); unit-specific data never is.
> - The Pad 4 has no public emergency-download loader. If the boot loader or firmware partitions were ever damaged,
>   there would be no way back at home. This guide never touches them.

## 0. What you get, and what is proven

| Stage | Proven by the project | Section |
|---|---|---|
| Your own kernel from our queue, built reproducibly (tree hashes checked by `prepare.sh`) | yes (q89g is the head since 13 Oct; every test kernel since 28 Sep) | 3 |
| The kernel package `kernel-iceland` (Fedora rpm) | yes (installed on the owner's tablet) | 3.4 |
| U-Boot install build v3 (RAM boots on 10 Oct; written to `boot_b` on 13 Oct) | yes | 4 |
| The device, firmware and sensor packages (rpm) | yes (installed on the owner's tablet; the sensor packages were built on the tablet in a RAM session) | 7 |
| A Linux and Fedora RAM test kit | the kit builder and its runner are not published | 6 |
| Installing Fedora to the tablet | yes, by the owner, 13 Oct 2026 (`INSTALL-GUIDE.md`); this guide does not repeat it | - |

## 1. Prerequisites

### 1.1 On the PC (any recent x86_64 Linux)

| Need | Packages (Debian / Ubuntu names; Fedora has equivalents) | Why |
|---|---|---|
| Git, make, a C toolchain | `git make bc bison flex libssl-dev libelf-dev cpio zstd xz-utils python3` | kernel build |
| LLVM / clang with lld | `clang lld llvm` | `scripts/build.sh` builds with `LLVM=1`. The project's clang version is not recorded in the public repository (unverified for the current build); a distribution LLVM 18 or newer is expected to work (untested here) |
| An aarch64 GCC | `gcc-aarch64-linux-gnu` | `iceland-u-boot` builds with `CROSS_COMPILE=aarch64-linux-gnu-` |
| Network access during the U-Boot build | - | `iceland-u-boot/scripts/build.sh` clones the pinned `mkbootimg` (commit `808ecd09`) |
| RPM tools (section 3.4 and 7 only) | `rpm-build`, `zstd`, `tar`, `git`, on Fedora 44 | the packaging scripts set the `.fc44` dist tag and build aarch64 packages |
| Android tools (optional) | `android-sdk-platform-tools` (`adb`, `fastboot`) | the RAM test of U-Boot (section 4) and reading from Android |
| Space | about 10 GB | kernel tree and build |

Fastboot and adb on Linux need no driver. You may need a udev rule for your user. The tablet's ABL and our U-Boot
both use USB vendor id 18d1, product d00d.

### 1.2 The tablet

- OnePlus Pad 4 (OPD2514). For a RAM test it runs stock OxygenOS **11.A.38** or a ROM built on its firmware.
- **Never** downgrade the firmware: anti-rollback.
- Keep the battery above 50 % for bring-up work. Use a USB-C cable to a USB port **directly** on the PC. A PC port gives
  less current than a wall charger, so long sessions drain the tablet.

### 1.3 Unlocking the boot loader (only if not done yet)

> **WARNING - erases everything, your decision.** Unlocking wipes all data and apps and puts the tablet in the
> "unlocked" (orange) verified-boot state. It does not write any boot image. The OnePlus procedure:
> - Settings > About > tap the build number 7 times, then Developer options > OEM unlocking ON;
> - `adb reboot bootloader`;
> - `fastboot flashing unlock`, then confirm on the tablet.
>
> The project used its own unlock script (not published). **Never relock** while anything non-stock is on the tablet.

### 1.4 Back up first (read-only, strongly recommended)

The project's first step was a full, checksummed copy of all 151 partitions except `userdata`. It holds the calibration
and identity of one tablet; no download replaces it.
- It needs root over adb. The project got it from a temporary system image, without flashing anything.
- Each partition was read with `dd` from `/dev/block/by-name/<name>` and hashed on both sides.
- Keep it on two disks, and never share it.

Any later step on the install path needs it (`INSTALL-GUIDE.md`, Part A).

## 2. Get the trees

All four repositories are public on GitHub under `mzakamin-hub`.

```sh
mkdir -p ~/pad4 && cd ~/pad4
git clone https://github.com/mzakamin-hub/iceland-linux         # kernel patch queue
git -C iceland-linux checkout q89g                              # the tag (branch iceland-7.3-rc7-q89g)
git clone https://github.com/mzakamin-hub/iceland-u-boot        # U-Boot patch queue
git clone https://github.com/mzakamin-hub/iceland-mainline      # packaging, phase4 scripts, firmware notes, docs
git clone https://github.com/mzakamin-hub/iceland-firmware      # generic firmware package (optional, section 5)
git -C iceland-firmware checkout 11.A.38-3                      # the current firmware release
```

The `main` branch of `iceland-linux` still holds the older rc4 queue. Build from the `q89g` tag, not from `main`.

## 3. Prepare and build the kernel

### 3.1 `prepare.sh` and `kernel.pin`

```sh
cd ~/pad4/iceland-linux
scripts/prepare.sh ./src
```

What it does (read `scripts/prepare.sh`; it changes nothing outside `./src`):
1. Shallow-clones `torvalds/linux` at tag **v7.3-rc7** if `./src` has no git tree. It checks that the commit equals
   `UPSTREAM_COMMIT` in `kernel.pin` (`24a19b953e2a...`).
2. Applies `patches/0001-infiniti/*.patch` (132 commits: the OnePlus 15 port of the same SoC) with `git am`, so every
   patch keeps its author, date and message. It checks the tree hash against `TREE_AFTER_0001_infiniti`.
3. Applies `patches/0002-iceland/*.patch` (294 Pad 4 patches; the numbers have gaps, the newest is 0306) and checks
   `TREE_AFTER_0002_iceland`.
4. Prints `source ready: ./src (<commit>)`. A tree-hash mismatch stops it: your tree would not be the tested one.

If the GitHub clone stalls, clone `v7.3-rc7` by hand into `./src` and run the script again. It reuses an existing
`./src/.git`.

### 3.2 The configuration

`scripts/build.sh` assembles the config. It does not use your distribution's config:

| Layer | File | Role |
|---|---|---|
| 1 | `arch/arm64/configs/defconfig` | upstream arm64 defaults |
| 2 | `arch/arm64/configs/sm8850.config` (from the source tree) | the SoC and board drivers; drift from it is only reported |
| 3 | `configs/distro-neutral.config` | **merged and checked strictly**: built-in root path (UFS, ext4 / btrfs / xfs / vfat, dm-crypt), the early framebuffer, EFI stub, systemd / container features, SELinux **and** AppArmor built in (`CONFIG_LSM` starts SELinux by default), compressed firmware (xz / zstd), `DMABUF_DEBUG=n` (else hardware-decoded video shows green), `GPIO_SHARED_PROXY=y` (else the backlight never probes), the Pad 4 drivers, `FW_DEVLINK_SYNC_STATE_TIMEOUT=y` |
| 4 | `configs/required.config` | must be present in the final `.config` (checked, not merged) |

Each line of `distro-neutral.config` carries a comment with the reason and the test that proved it. Read them before you
change anything. The debugging fragment used in the project's test runs is not published and is not needed.

### 3.3 Build

```sh
cd ~/pad4/iceland-linux
scripts/build.sh ./src ./out           # LLVM=1; JOBS=N to limit parallelism
ls out/dist/
# Image  Image.gz  kaanapali-oneplus-iceland.dtb  config-<release>  modules-<release>.tar.zst  BUILD_INFO  SHA256SUMS
```

- The release string of q89g is `7.3.0-rc7-iceland-00426-g520e85da9244`.
- A config check failure means a fragment line was dropped silently (an unmet dependency). Fix that; do not set
  `ALLOW_CONFIG_DRIFT=1` without reading the message.
- Build time depends on your CPU (a full build with modules).

### 3.4 Package the kernel as `kernel-iceland` (Fedora)

```sh
cd ~/pad4/iceland-linux
git checkout q89g                                        # the source rpm carries the queue at HEAD
packaging/fedora/build-rpm.sh ./out ./rpms [RELEASE]     # RELEASE defaults to 1
```

- `build-rpm.sh BUILD_OUT_DIR RPM_OUT_DIR [RELEASE]` reads `out/dist`, `out/System.map` and `out/.config`. It makes a
  binary rpm for aarch64 and a source rpm that carries the whole queue at HEAD, so check out the tag first.
- The rpm version replaces the `-` of the release string, because rpm versions cannot hold `-`. The rule is in
  `packaging/fedora/README.md`.
- `kernel-iceland` is installonly and keeps three versions. Its `%posttrans` runs `kernel-install`, which writes the
  boot entry. The plug-in `90-iceland-dtb.install` copies the device tree to the ESP, where U-Boot loads it.
- It needs rpmbuild on Fedora (untested here on other distributions).

## 4. Build U-Boot (the install build v3)

```sh
cd ~/pad4/iceland-u-boot
scripts/prepare.sh ./src        # v2026.10-rc5 + 14 infiniti patches + 10 Pad 4 patches; tree hashes checked
scripts/build.sh ./src ./out    # CROSS_COMPILE=aarch64-linux-gnu- by default; JOBS=N
ls out/dist/                    # u-boot-iceland-v4.img  u-boot-iceland-v2.img  u-boot.bin.gz  u-boot.dtb  BUILD_INFO  SHA256SUMS
```

- The Pad 4 series is `patches/0002-iceland`: 0001-0003 are the board (`iceland_defconfig`, `iceland.env`), and
  0004-0010 are the install build: blkmap mapping of `userdata`, EFI disk rules (every block device except the blkmap
  disk is read-only for EFI programs), the install environment, a fastboot idle timeout, no reset or power-off by itself,
  USB brought up without ABL, and `fastboot reboot-bootloader`.
- `u-boot-iceland-v4.img` is the header-v4 image (U-Boot with its device tree in the kernel slot), the form ABL starts.
  `u-boot-iceland-v2.img` is an alternative.
- The record of the tested build is `tools/install/BUILD_INFO-v3.txt` in `iceland-u-boot`: U-Boot commit
  `aac9e744ec6f`, mkbootimg `808ecd09`, boot header `os_version 17.0.0`, patch level `2026-09`. Its raw image
  `u-boot-iceland-usb.img` (540,672 bytes) has sha256 prefix `979b4076`. The image written to `boot_b` on 13 Oct is
  that build with an AVB hash footer made for that day's `boot_b`; the footer step is part of the install record.
  Whether a fresh build reproduces the record's hash is **unverified**: U-Boot embeds its build time, so the hash
  changes with each build.
- The boot header values in `uboot.pin` must match the boot image of the slot you write (anti-rollback).

RAM test (nothing is written):

```sh
adb reboot bootloader                      # or: power off, hold Volume Down + Power, connect USB
fastboot getvar product                    # read only: ABL reports canoe
fastboot boot ~/pad4/iceland-u-boot/out/dist/u-boot-iceland-v4.img
# after a few seconds U-Boot's text appears and U-Boot's own fastboot takes over
fastboot getvar product                    # now: oneplus-iceland (U-Boot)
```

The project's RAM boots of this build ran on 10 Oct 2026: fastboot came up after 2-7 s, the boot manager failed cleanly
and the slot flags were unchanged. A RAM boot of an image built here is untested here. If U-Boot's text does not
appear, leave the tablet alone: a reboot returns it to its installed boot.

## 5. Firmware: the generic set and your own tablet

The panel, touch, GPU, video, sound, Wi-Fi, Bluetooth and the sensors need firmware (`02-HARDWARE.md` section 7). It comes
in two kinds:

- **Generic** firmware (ADSP, CDSP, SOCCP, GPU, Wi-Fi / Bluetooth, touch, camera and VPU files) is the same on every
  Pad 4 with stock 11.A.38. The project publishes it in the `iceland-firmware` repository (release 11.A.38-3, with the
  GitHub releases 11.A.38-2 and 11.A.38-3). `MANIFEST.tsv` gives each file's stock source and sha256; `NOTICE.md` has
  the vendor notices. Before you use a copy from anywhere, compare its sha256 with your own extraction.
- **Unit-specific** data (the partition backups, persist, modem and EFS data, calibration and key material, the serial,
  the MAC and Bluetooth addresses) is never published. It comes only from your own tablet. `EXCLUDED.tsv` lists what the
  package leaves out.

Three read-only ways to get the files from your own tablet:

**A. From a running, rooted Android over adb** (untested here as a recipe). The stock paths are listed in
`iceland-mainline/firmware/manifest.tsv`, column `stock_path`:

```sh
adb root                                  # needs a userdebug ROM with "Rooted debugging" (LineageOS) - read only
mkdir -p fw-stock && cd fw-stock
adb pull /vendor/firmware_mnt/image/ modem_image/      # modem partition: ADSP/CDSP .mdt + .bNN, Wi-Fi peach/
adb pull /vendor/bt_firmware/image/ bt_image/          # Bluetooth brhbt*
adb pull /vendor/firmware/gen80200_zap.mbn .
adb pull /vendor/firmware/vpu40_2v.mbn .
adb pull /odm/etc/wifi/peach/ odm_wifi/
adb pull /odm/firmware/tp/25926/FW_NT36536_HUAXING.img .
adb unroot
```

Then convert them to the Linux names:
- Squash each split image (`adsp.mdt` + `adsp.bNN`, the same for `cdsp`) into one `.mbn` with `pil-squasher`
  (linux-msm, a public tool).
- Strip the touch image's 80-byte header with `iceland-mainline/firmware/convert-nt36536.py`.
- Rename as in the manifest. Use the directory `qcom/kaanapali/iceland/` (the names the device tree asks for).
- Take `qcom/gen80200_{sqe.fw,gmu.bin,aqe.fw}` from upstream **linux-firmware**.

**B. The project's on-device extractor** (`iceland-fw-extract`) is not published. It runs as root in a RAM session on
the tablet, sets every source partition read-only before opening it, and writes the firmware tree with a record of
what came from where.

**C. From the stock OTA package** of the same version (11.A.38). You download it yourself; the partition images are
inside its payload. Never use firmware from another version.

Keep your own extraction in one folder laid out like `/lib/firmware`. **It is private:** never commit it, and never
upload an image that contains it.

## 6. A RAM-boot Linux image (not published)

The project built its RAM test kits (a debug device tree, a busybox initramfs with a USB network and read-only report
pages, and optionally a Fedora root, section 7.2) with a kit builder that was project test tooling. That builder, its shim and its
runner are **not** in the public repositories (removed 13-14 Oct 2026 with the test tooling). The public scripts stop at
the kernel and U-Boot: `scripts/build.sh` gives you `out/dist/Image.gz` and the device tree for any boot image.

If you build your own RAM-boot image, the format the project used is Android header v2 (kernel, ramdisk, device tree),
made with the pinned `mkbootimg` (commit `808ecd09`). On the installed system the kernel command line must not carry
`clk_ignore_unused pd_ignore_unused regulator_ignore_unused`: the install decision of 3 Oct 2026 removed them
(finding F24). This guide gives no tested recipe for your own image; test it yourself.

## 7. Packages and the phase-4 Fedora root

### 7.1 The device, firmware and sensor packages

| Package | Where | Build | Notes |
|---|---|---|---|
| `iceland-device` 0.28-8 (noarch) | `iceland-mainline/packaging/iceland-device/` | `packaging/iceland-device/build-rpm.sh OUT_DIR` on Fedora (needs rpmbuild and git). It fetches the pinned `audioreach-topology` (commit `993a17d`) from GitHub, and the spec builds the AudioReach topology with `m4` and `alsatplg` | configuration and scripts only, no firmware. The reason for each setting is in the README and the spec's `%changelog` |
| `iceland-firmware` 11.A.38-3 (noarch) | `iceland-firmware` repository (`iceland-firmware.spec`, `MANIFEST.tsv`, `root/`) | archive the tree as `iceland-firmware-11.A.38/` (the spec's `Source0`), then `rpmbuild -ba iceland-firmware.spec` (untested here) | the generic firmware of section 5, plus the decoded generic thermal model. It needs the `fastrpc` group, which the sensor packages provide |
| `hexagonrpc`, `libssc` (+ `-devel`), `iio-sensor-proxy` 3.9 (patched) | `iceland-mainline/packaging/sensors/` (specs, `build-rpm.sh`) | `packaging/sensors/build-rpm.sh TOP OUT_DIR` on **Fedora 44 aarch64**. `TOP` holds `SPECS/` and `SOURCES/`. The script builds `hexagonrpc`, then `libssc` (installed), then `iio-sensor-proxy` | pins: `hexagonrpc` `598b591`, `libssc` `54dd13e`, `iio-sensor-proxy` 3.9; the patches are in `iceland-mainline/docs/sensors/patches/`. The script named in the sensors README that assembles `TOP` (`mk-sensor-pkg.sh`) is not in the public repository, so `TOP` is prepared by hand (unverified) |

The sensor programs need the tablet's own sensor-hub file tree at `/usr/share/qcom/kaanapali/OnePlus/iceland`. The
firmware package supplies the public part; the unit-specific registry comes from your own tablet (section 5).

### 7.2 The phase-4 Fedora root (`iceland-mainline/phase4/`)

- `fetch-fedora.sh [base|workstation|all] [OUT_DIR]` downloads the Fedora 44 aarch64 images and verifies them against
  Fedora's CHECKSUM files. `base` is the Container Base image (systemd, no GNOME; the RAM root). `workstation` is the
  Workstation raw disk image (the install image). The GPG check runs when Fedora's key is placed in `OUT_DIR/fedora.gpg`.
- `make-rootfs.sh OCI_TAR_XZ OUT_DIR MODSTAGE KVER FWDIR MODLIST BUSYBOX LINUX_RAM_DIR` unpacks the base (or a rootfs
  tarball from an earlier boot) under fakeroot, adds report pages, a telnet shell, your firmware and a module subset,
  and writes `rootfs.cpio.gz`. Its last argument is the kit builder's directory (section 6), which is not published.
  As published, the script cannot run from the repository alone (unverified how to supply that directory).
- `rootfs-post-wayland.sh` is a test script for a Wayland compositor on the Adreno GPU (seatd, cage, glmark2). Nothing
  needs it to build.
- `phase4/README.md` lists the GNOME package set and these lessons:
  - Never `switch_root` away from the busybox shim (its safety jobs die and the tablet resets). Use systemd as PID 1
    in a chroot of the rootfs.
  - Install `systemd-pam` and `dbus-daemon` before GDM in a root grown from the Container Base image.
  - Re-trigger udev for driverless devices ("coldplug"); otherwise the sound card can wait for ever for the DP audio codec.

## 8. Testing and getting logs

- The project's test suite, its RAM-kit runners and the run logs are not published (removed 13-14 Oct 2026). The
  rehearsal logs stay private: they carry network names and unit data. This guide therefore has no test script to run.
- The feature matrix in `iceland-mainline/docs/features/` (`features-data.py`, `build.py`) records how each feature was
  proven; its working rows are published as `docs/FEATURES.md`.
- **Live kernel log.** Read `dmesg` (or the journal on an installed system) for the run.
- **After a reset.** pstore does not survive a hard reset (PS_HOLD). Read the reset reason from Android's
  `/proc/bootloader_log` (root), or keep a kit's kernel log in a pmsg zone (the kit builder is not published).
- **Rules that come from accidents** (`06-PROCESS-HISTORY.md` section 4):
  - never read every `/sys/kernel/debug/regmap/*/registers`;
  - never read TLMM pad registers through `/dev/mem`;
  - never poke driver-owned registers from user space.
  Each of these has reset the tablet.

## 9. What is not covered, and the risks

- **The install** is not part of this guide. The owner installed Fedora 44 on 13 Oct 2026; the steps and the record are
  in `INSTALL-GUIDE.md`. The install image itself is not published. `07-INSTALL-REVIEW.md` is the review of 2 Oct, from
  before the install.
- **Cameras.** The camera sensor drivers (SC1320CS, SC820CS) are in the kernel queue. Their tuning files (`sc1320cs.yaml`,
  `sc820cs.yaml`) are in the `iceland-device` package. Without the tuning there are no cameras, on any distribution. The
  feature matrix gives the state of each camera row, including the camera into the hardware encoder (not negotiating yet).
- **Accessories** (wall chargers, the pen, the keyboard cover, a DisplayPort monitor, USB host devices) are not all
  tested. Read the feature matrix row before you rely on one.
- **Risk summary.**
  - A RAM boot cannot damage the tablet's storage: `fastboot boot` writes nothing.
  - The remaining risks are a hang or reset (hold Power about 15 s), and battery drain during long sessions on a PC port.
  - Unlocking (1.3) and any write to a partition are destructive, and both are the owner's decision.
