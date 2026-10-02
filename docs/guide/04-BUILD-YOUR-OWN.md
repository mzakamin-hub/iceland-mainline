# 04 - Build your own kernel and RAM-boot it on your OnePlus Pad 4

A step-by-step guide for a Linux user with their own Pad 4. State: 2 Oct 2026 (queue 0001-0166).

The project itself works from Windows 11 with WSL (Ubuntu 24.04) for building and PowerShell for the tablet runs.
**Steps marked "untested here" were not run that way by the project.** The underlying commands are the same, but
nobody has walked this exact path on a plain Linux PC yet.

> **WARNING - read before anything else**
> - Nothing in this guide writes to your tablet's storage. A RAM boot (`fastboot boot`) loads an image into memory;
>   a reboot returns you to Android.
> - To RAM-boot at all, the boot loader must be **unlocked**. Unlocking **erases all data** on the tablet and is
>   your decision, at your own risk (section 1.3).
> - Never type `fastboot flash`, `erase`, `format`, `-w`, `set_active` or `flashing lock` while following this
>   guide. None of them is needed here.
> - Firmware from your tablet is proprietary. Keep it on your own machine; never upload or share images that
>   contain it.
> - The Pad 4 has no public emergency-download loader. If the boot loader or firmware partitions were ever damaged,
>   there would be no way back at home. This guide never touches them.

## 0. What you get, and what is proven

| Stage | Proven by the project | Section |
|---|---|---|
| Your own kernel from our queue, built reproducibly (tree hashes checked) | yes (every test kernel since 28 Sep) | 2-3 |
| U-Boot (RAM-boot "diag L" build) | yes (diagnostic runs 3-4, every kit) | 4 |
| A minimal Linux RAM boot: USB network, kernel log over HTTP, display on the boot framebuffer | yes (Linux tests 2-7, 28 Sep) | 6-7 |
| The full kit: native display, sound, Wi-Fi, sensors, a Fedora 44 GNOME root in RAM | yes, with the project's Windows tooling | 8 |
| The device package and the sensor packages as RPMs | yes (built in RAM sessions on the tablet) | 9 |
| Installing Fedora to the tablet | **no** (planned; see `03-BOOT-AND-PARTITIONS.md`, `07-INSTALL-REVIEW.md`) | - |

## 1. Prerequisites

### 1.1 On the PC (any recent x86_64 Linux)

| Need | Packages (Debian / Ubuntu names; Fedora has equivalents) | Why |
|---|---|---|
| Git, make, a C toolchain | `git make bc bison flex libssl-dev libelf-dev cpio zstd xz-utils python3` | kernel build |
| LLVM / clang with lld | `clang lld llvm` | the queue's `scripts/build.sh` builds with `LLVM=1`. The project uses Android's clang r596125 (LLVM 22); a distribution LLVM 18 or newer is expected to work (untested here) |
| Device-tree tools | `device-tree-compiler` (`dtc`, `fdtget`, `fdtput`) | the RAM-kit builder edits the device tree |
| An aarch64 GCC for U-Boot | `gcc-aarch64-linux-gnu` | `iceland-u-boot` builds with `CROSS_COMPILE=aarch64-linux-gnu-` |
| Android tools | `android-sdk-platform-tools` (`adb`, `fastboot`) | RAM boot, reading from Android |
| Busybox package tools | `dpkg-deb` (in `dpkg`) | the kit builder unpacks a pinned static busybox |
| Space | about 10 GB | kernel tree + build |

Fastboot and adb on Linux need no driver. You may need a udev rule for your user. The tablet's ABL and our U-Boot
both use vendor id 18d1, product d00d.

### 1.2 The tablet

- OnePlus Pad 4 (OPD2514) on stock OxygenOS **11.A.38** or a ROM built on its firmware. The project's tablet runs
  LineageOS 24.0 on that firmware.
- **Never** downgrade the firmware: anti-rollback.
- Battery above 50 %. A USB-C cable to a USB port **directly** on the PC. The project uses a USB 2 link; the tablet
  draws more than a PC port gives during a run, so about 1 % of battery goes per 10-minute test.

### 1.3 Unlocking the boot loader (only if not done yet)

> **WARNING - erases everything, your decision.** Unlocking wipes all data and apps and puts the tablet in the
> "unlocked" (orange) verified-boot state. It does not write any boot image. The OnePlus procedure:
> - Settings > About > tap the build number 7 times, then Developer options > OEM unlocking ON;
> - `adb reboot bootloader`;
> - `fastboot flashing unlock`, then confirm on the tablet.
>
> The project did this once with `C:\OnePlusPad4\scripts\01-Unlock-Bootloader.ps1` (it records ABL's state first).
> **Never relock** while anything non-stock is on the tablet.

### 1.4 Back up first (read-only, strongly recommended)

The project's first step was a full, checksummed copy of all 151 partitions except `userdata`. It holds the
calibration and identity of that one tablet; no download replaces it.
- It needs root over adb. The project got it from a temporary DSU system image, without flashing anything.
- Each partition was read with `dd` from `/dev/block/by-name/<name>` and hashed on both sides.
- Keep it on two disks, and never share it.

A RAM boot does not need the backup, but any later step on the install path does (INSTALL-GUIDE Part A).

## 2. Get the trees

The three repositories are **private** today (GitHub user `mzakamin-hub`). Ask the owner for access. Nothing is
published without the owner's OK.

```sh
mkdir -p ~/pad4 && cd ~/pad4
git clone https://github.com/mzakamin-hub/iceland-linux        # kernel patch queue
git clone https://github.com/mzakamin-hub/iceland-u-boot       # U-Boot patch queue
git clone https://github.com/mzakamin-hub/iceland-mainline     # tools, packaging, docs
```

## 3. Prepare and build the kernel

### 3.1 `prepare.sh` and `kernel.pin`

```sh
cd ~/pad4/iceland-linux
scripts/prepare.sh ./src
```

What it does (read `scripts/prepare.sh`; it changes nothing outside `./src`):
1. Shallow-clones `torvalds/linux` at **v7.3-rc4**. It checks that the commit equals `UPSTREAM_COMMIT` in
   `kernel.pin` (93f51579e7df...).
2. Applies `patches/0001-infiniti/*.patch` (138 commits of the OnePlus 15 port of the same SoC) with `git am`, so
   every patch keeps its author, date and message. It checks that the tree hash equals `TREE_AFTER_0001_infiniti`.
3. Applies `patches/0002-iceland/*.patch` (the Pad 4 series, 0001-0166) and checks `TREE_AFTER_0002_iceland`.
4. Prints `source ready: ./src (<commit>)`. A tree-hash mismatch stops it: your tree would not be the tested one.

If the GitHub clone stalls (it did twice for the project), clone `v7.3-rc4` by hand into `./src` and run the script
again. It reuses an existing `./src/.git`.

### 3.2 The configuration

`scripts/build.sh` assembles the config. It does not use your distribution's config:

| Layer | File | Role |
|---|---|---|
| 1 | `arch/arm64/configs/defconfig` | upstream arm64 defaults |
| 2 | `arch/arm64/configs/sm8850.config` (added by queue patch 0003) | the SoC and board drivers; drift is only reported |
| 3 | `configs/distro-neutral.config` | **merged and checked strictly**: built-in root path (UFS, ext4 / btrfs / xfs / vfat, dm-crypt), the early framebuffer, EFI stub, systemd / container features, SELinux **and** AppArmor built in (`CONFIG_LSM` starts SELinux by default), compressed firmware (xz / zstd), `DMABUF_DEBUG=n` (else hardware-decoded video shows green), `GPIO_SHARED_PROXY=y` (else the backlight never probes), the Pad 4 drivers (pen charger, pogo keyboard, telemetry), `FW_DEVLINK_SYNC_STATE_TIMEOUT=y` |
| 4 | `configs/required.config` | must be present in the final `.config` (checked, not merged) |

Each line of `distro-neutral.config` carries a comment with the reason and the run that proved it. Read them before
you change anything. `configs/debug-hang.config` is a debugging extra, not for normal builds.

### 3.3 Build

```sh
cd ~/pad4/iceland-linux
scripts/build.sh ./src ./out           # LLVM=1; JOBS=N to limit parallelism
ls out/dist/
# Image  Image.gz  kaanapali-oneplus-iceland.dtb  config-<release>  modules-<release>.tar.zst  BUILD_INFO  SHA256SUMS
```

- The release string looks like `7.3.0-rc4-iceland-NNNNN-g<hash>`.
- A config check failure means a fragment line was dropped silently (an unmet dependency): fix that, do not set
  `ALLOW_CONFIG_DRIFT=1` without reading the message.
- Build time depends on your CPU (a full build with modules).
- The project's own test builds use `~/mainline/build/build-q2.sh` / `build-q56.sh`. They are the same make
  invocation on a local branch, plus the workflow candidates. Not needed for your build.

## 4. Build U-Boot (the RAM-boot "diag L" image)

```sh
cd ~/pad4/iceland-u-boot
scripts/prepare.sh ./src               # u-boot v2026.10-rc5 + 14 infiniti + 3 Pad 4 patches, tree hashes checked
tools/diag/build-diag.sh ./src ./out   # CROSS_COMPILE=aarch64-linux-gnu- by default
ls out/dist/                           # diag-C-fastboot.img  diag-D-normal.img  diag-E-info.img  diag-L-efi.img  SHA256SUMS
```

- **Use `diag-L-efi.img`.** It shows its log on the screen, waits in its own fastboot, and starts what you send it
  through the kernel's EFI stub.
- It is built **without fastboot flashing**: it cannot write the tablet's storage.
- Its USB product id is ABL's (0xd00d). U-Boot's fastboot reports `product: oneplus-iceland`, ABL's reports
  `canoe`. That is how you tell them apart.
- Do not RAM-boot `diag-D-normal.img` unless you know why. Its normal boot command maps `userdata` (read-only) to look
  for an installed system. It is harmless on Android's encrypted data, but it is not needed for a test.

## 5. Firmware from your own tablet (read-only)

The kernel boots and shows a console without any firmware. The panel's own driver, touch, GPU, video, sound,
Wi-Fi, Bluetooth and the sensors need the tablet's firmware (table in `02-HARDWARE.md` section 7). Three ways to
get it, all read-only:

**A. From a running, rooted Android over adb** (untested here as a recipe; the project used the backup and a
FAT reader). Pull the stock paths listed in `iceland-mainline/firmware/manifest.tsv`, column `stock_path`:

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
  (linux-msm, public tool).
- Strip the touch image's 80-byte header with `iceland-mainline/firmware/convert-nt36536.py`.
- Rename as in the manifest. Use the directory `qcom/kaanapali/iceland/` (the names the device tree asks for); the
  manifest's `OnePlus/` sub-folder is stale.
- Take `qcom/gen80200_{sqe.fw,gmu.bin,aqe.fw}` from upstream **linux-firmware**.

**B. The project's on-device extractor** (`~/mainline/build/wf/install/cand/fwx/iceland-fw-extract` +
`fw-list.tsv`).
- It runs as root in a RAM session on the tablet. It sets every source partition read-only before opening it, reads
  FAT and ext4 itself and the EROFS images inside `super` through a read-only loop.
- It writes `/usr/lib/firmware/updates/...`, the sensor-hub tree `/usr/share/qcom/kaanapali/OnePlus/iceland/` and a
  record of what came from where, with hashes.
- Checked on the owner's backup: 23 of 23 items. It is the planned install's extractor; it is not yet in a public
  repository.

**C. From the stock OTA package** of the same version (11.A.38). You download it yourself; the partition images
are inside its payload. Never use firmware from another version.

Keep the result in one folder laid out like `/lib/firmware` (for example `~/pad4/fw/`). This is the `FWDIR` of the
next section. **It is private:** never commit it, never upload a kit that contains it.

## 6. Build a RAM-boot Linux image

`iceland-mainline/tools/linux-ram/build.sh` makes an Android boot image (header v2) with:
- your kernel;
- a debug copy of your device tree: USB forced to peripheral mode, and the GPU, remote processors, PCIe, pmic_glink
  and native display switched off unless you ask for them;
- a small busybox initramfs whose `/init` brings up a USB network and serves read-only report pages.

```sh
cd ~/pad4
git clone https://github.com/LineageOS/android_system_tools_mkbootimg mkbootimg
git -C mkbootimg checkout 808ecd09666ffe0ff5800f02af693abce56eb395      # the pin in iceland-u-boot/uboot.pin
# smallest first boot: no firmware, boot framebuffer only
iceland-mainline/tools/linux-ram/build.sh iceland-linux/out/dist iceland-linux/out ./mkbootimg ./img-first
ls img-first/      # linux-iceland-debug.img  iceland-debug.dtb  BUILD_INFO  SHA256SUMS
```

Useful environment knobs (read the script for all of them):

| Variable | Effect |
|---|---|
| `FWDIR=~/pad4/fw` | puts your firmware folder into the initramfs (**the image becomes private**) |
| `MODDIR=<modules_install dir>`, `MODLIST=<file>` | carries modules and a load list |
| `NATIVE_DISPLAY=1` | keeps the display subsystem and backlight (needs the panel driver and firmware for touch) |
| `WIFI=1` | keeps PCIe for the Wi-Fi chip |
| `ENABLE="/soc@0/remoteproc@6800000 /pmic-glink"` | keeps nodes of the disabled list (ADSP, battery / USB-C) |
| `ADSP_MDT=1` | the ADSP loads the split `.mdt` firmware instead of `.mbn` |
| `PMSG_ANDROID=1` | the kernel log goes to a pmsg zone that Android shows after a reset |
| `ROOTFS_CPIO=<file>` | appends a root file system (the Fedora-in-RAM kits, section 8) |
| `CMDLINE_EXTRA="..."` | adds kernel arguments |

The kernel command line always has `clk_ignore_unused pd_ignore_unused regulator_ignore_unused`. The boot screen runs
on the firmware's framebuffer until the display driver takes over, and these keep its clocks and rails.

## 7. RAM-boot it (nothing is written)

The project runs this with `tools/linux-ram/run-linux.ps1` on Windows. The same steps by hand on Linux (untested
here):

```sh
adb reboot bootloader                      # or: power off, hold Volume Down + Power, connect USB
fastboot getvar product                    # must say: canoe   (read only)
fastboot boot ~/pad4/iceland-u-boot/out/dist/diag-L-efi.img
# about 5-10 s: U-Boot's text appears on the screen, then U-Boot's own fastboot
fastboot getvar product                    # now: oneplus-iceland (U-Boot)
fastboot boot ~/pad4/img-first/linux-iceland-debug.img
```

What you should see:
- The kernel log scrolls on the screen (`earlycon=efifb`).
- After about 30-40 s, a USB network device appears on the PC. The tablet is `172.16.42.1`; its busybox DHCP server
  gives the PC `172.16.42.2`.

Read the report pages, which are read-only:

```sh
curl http://172.16.42.1/cgi-bin/info
curl http://172.16.42.1/cgi-bin/dmesg > dmesg.txt
curl http://172.16.42.1/cgi-bin/deferred      # drivers waiting for something
curl http://172.16.42.1/cgi-bin/unbound       # devices without a driver
# also: timeline genpd interconnect regulators clocks gpio pinctrl drm thermal power buses irq pstore kmsg
```

Back to Android: `curl http://172.16.42.1/cgi-bin/reboot`, or hold Power about 15 s. The kit also reboots by itself
after its timer (`AUTOREBOOT_AT`).

**If the screen turns white or black after the text:** that is the display hand-over problem the project solved in
queue 0022 / 0026-0027 (`docs/tests/README.md`, Linux tests 3-7). Make sure your device tree is from the full queue.

**If nothing happens after `fastboot boot` of U-Boot:** ABL drops a device tree appended after a gzip'd kernel. Only
images built by `build-diag.sh` / `build.sh` (kernel = gzip of U-Boot with its tree inside) work.

## 8. The full kit: Fedora 44 + GNOME in RAM (the project's method)

The project's daily kits add, on top of section 6:
- the tablet's firmware;
- the full module tree;
- a Fedora 44 root file system in RAM (`phase4/make-rootfs.sh`, from the official Container Base image, grown by dnf
  through a small proxy on the PC: `tools/relay/usb-proxy.py`);
- systemd as PID 1 (`ROOTFS_MODE=pid1`);
- ssh with the PC's key;
- a GNOME autologin session.

Large roots are fetched at boot over the USB network from an HTTP server on the PC (`ROOTFS_URL`). How it fits
together:
- `iceland-mainline/phase4/README.md`;
- `~/mainline/build/make-kit26.sh` (the kit builder: kernel `BIN_TAG`, `USB_QOS`, `KIT_LABEL`, `KIT_DESC` without
  quotes);
- `~/mainline/build/an/genwf.py` (the generator of a run's tablet script and PC probe);
- `docs/memory/iceland-autonomous-kit-runs.md`.

Lessons that matter if you rebuild it:
- Never `switch_root` away from the busybox shim: its safety jobs die and the tablet resets. Use `pid1` mode.
- A root in RAM moves the kernel firmware loader's root along with PID 1. The shim binds `/lib/firmware` into the
  root first.
- Install `systemd-pam` and `dbus-daemon` before GDM in a root grown from the Container Base image.
- Re-trigger udev for driverless devices ("coldplug"); otherwise the sound card can wait for ever for the DP audio
  codec.

## 9. The device package and the sensor packages

| Package | Where | Build | Notes |
|---|---|---|---|
| `kernel-iceland` | `iceland-linux/packaging/fedora/` (spec, `build-rpm.sh`, `90-iceland-dtb.install`) | `build-rpm.sh BUILD_OUT RPM_OUT [RELEASE]` on a machine with rpmbuild | installs side by side (installonly). The install workflow's newer spec and plug-ins (`wf/install/cand/kernel-iceland/`) are not merged yet |
| `iceland-device` (noarch) | `iceland-mainline/packaging/iceland-device/` | `./build-rpm.sh OUT` on Fedora (needs `m4`, `alsa-utils`, `alsa-topology-utils`; it builds the AudioReach topology) | configuration and scripts only, no firmware. Every setting and its reason is in its README. Version 0.17 is committed; 0.18 adds the install parts |
| `hexagonrpc`, `libssc`, `iio-sensor-proxy` 3.9 (patched) | `iceland-mainline/packaging/sensors/` | `mk-sensor-pkg.sh` makes the sources; `build-rpm.sh` on **Fedora 44 aarch64** (the project builds them on the tablet in a RAM session, 10 s); `libssc` before `iio-sensor-proxy` | the sensor hub's file tree from your tablet is needed at run time |

In a RAM session the project builds and installs them with its `pkg2` part, then starts the sensor hub (`rotpkg
start`). The camera and sensor tests only mean something after that.

## 10. Testing and getting logs

- **Live kernel log.** The shim streams kmsg to the PC (`kmsgall` page). The project saves the streams per run. A
  repeating heartbeat line in the stream means the tablet froze.
- **After a reset.** pstore does not survive (PS_HOLD hard reset). Use `PMSG_ANDROID=1`, then read
  `/sys/fs/pstore/pmsg-ramoops-0` in Android. Or read the reset reason from Android's `/proc/bootloader_log` (root).
- **The project's tests.** Each topic has a `tablet.sh` with one function `wf_<name>` that writes one summary line.
  They are in `~/mainline/build/wf/<name>/` (for example `wf/hwinv/tablet.sh`: a read-only inventory of unbound,
  deferred and failed devices). The log sets of every run are in `iceland-mainline/docs/tests/area-combo-NN/`.
- **Rules that come from accidents** (`06-PROCESS-HISTORY.md` section 4):
  - never read every `/sys/kernel/debug/regmap/*/registers`;
  - never read TLMM pad registers through `/dev/mem`;
  - never poke driver-owned registers from user space.
  Each of these has reset the tablet.

## 11. What is not covered, and the risks

- **No install.** Writing `userdata` or a boot partition is not part of this guide. The project's install plan is
  not executed yet and has open review findings (`07-INSTALL-REVIEW.md`).
- **The private camera sensor driver** (SC1320CS / SC820CS) is not in the queue. Without it the cameras do not work.
  Everything else in the queue is GPL source.
- **Wall chargers, the pen, the keyboard cover, a monitor** have not all been tested with real accessories. Read
  the feature matrix row before relying on one.
- **Risk summary.**
  - A RAM boot cannot damage the tablet's storage: nothing in these images can write it.
  - The remaining risks are a hang or reset (hold Power 15 s), and battery drain during long sessions on a PC port.
  - Unlocking (1.3) is the only destructive step, and it is yours.
