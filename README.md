# iceland-mainline

Mainline Linux for the OnePlus Pad 4 (`iceland`, model OPD2514, Qualcomm SM8850P). The tablet runs **Fedora 44 with
GNOME** on a mainline kernel. The tablet's own boot loader (ABL) stays in place. Our U-Boot, in the `boot_b` partition,
shows a short boot menu and starts Fedora from a disk image in `userdata`. The menu can also start **BlissROM**, an
Android custom ROM, on the same tablet (dual boot).

This repository is the hub: the install guides, the list of working features, the device package (`iceland-device`)
and the tools. The kernel, U-Boot, the firmware and the Android trees have their own repositories, listed in
[Repositories](#repositories).

> **The install erases Android's data and changes two partitions.** Read [Before you start](#before-you-start) and
> the backup part of [Manual install](#manual-install) first.

## Boot chain

```
power on
  |
ABL             the tablet's own boot loader (OnePlus, closed). The project never writes it.
  |             On an unlocked tablet it shows an orange warning and goes on.
  v
boot_b          U-Boot, the project's install build. Boot menu, 5 s timeout:
  |
  +-- Fedora (default)
  |     starts the `fedora` partition if there is one, else the disk image in `userdata`
  |     -> shim -> GRUB -> kernel-iceland + initramfs -> Fedora 44 on the btrfs root
  |
  +-- BlissROM (dual boot only: it is shown only when it is safe, see DUAL-BOOT.md)
  |     Android's kernel from `boot_a`, with the ramdisk and device tree that ABL prepared
  |
  +-- Boot loader (fastboot)
        back to ABL's fastboot, where the writes are made
```

Storage on the tablet's main storage unit (LUN 0) after the dual-boot split:

```
LUN 0  +-----------------------------+--------------------------------+-----------+
       | fedora (new)                | userdata (smaller)             | 1 MiB     |
       | Fedora disk image           | BlissROM's encrypted data      | unused,   |
       | (ESP, /boot, btrfs root)    |                                | kept free |
       +-----------------------------+--------------------------------+-----------+
```

Without the split, `userdata` holds the whole Fedora disk image and Android no longer starts. The split is part C of
the manual install. Before it, the menu shows Fedora and the boot loader only.

## What works

This is a summary of [docs/FEATURES.md](docs/FEATURES.md), which has the details and what was measured. Features that
are still being worked on are not listed. Anything that is not in the list is not claimed to work.

| Area | What works |
|---|---|
| Display and input | The panel at its native 3392 x 2400 over dual DSI with DSC; refresh 30 to 144 Hz; backlight with GNOME's slider and automatic brightness (off by default); touch; pen; lid; power and volume keys; auto-rotate in tablet mode. |
| Graphics | The Adreno 840 GPU: OpenGL 4.6 and OpenGL ES 3.2 (Mesa), Vulkan 1.4 through turnip. Hardware video decode (H.264, HEVC, VP9, AV1) and encode (H.264, HEVC). |
| Audio | The sound card from the audio DSP; all six speakers in stereo behind a speaker-protection filter; both microphones, with echo cancellation on the default input. |
| Connectivity | Wi-Fi on 2.4 GHz and 5 GHz (6 GHz is not tested yet); Bluetooth with pairing in GNOME; USB device mode and a USB network link. |
| Power and charging | Battery level, health and time estimate in GNOME; the charge limit at 80 / 85 % ("Preserve Battery Health"); bypass charging; the battery safety guard at stock's limits; low-battery current limits. |
| Thermal | CPU, GPU and skin-temperature limits from stock's values. |
| Sleep | Suspend (s2idle) and resume; the power key and the alarm wake the tablet; Wi-Fi comes back after a wake. Overnight drain of about 0.35 % per hour, measured on one tablet. |
| Sensors and camera | Accelerometer, compass, light, proximity and gyroscope through the sensor hub; the 13 MP rear and 8 MP front cameras stream through libcamera; GNOME Camera works with both; the rear flash works as a torch. |
| System and boot | Boot from U-Boot through EFI into Fedora 44; kernel updates with dnf (a new kernel boots once as a trial); the dual-boot menu (Fedora / BlissROM v20.1). |

Known limits, from the guides: the tablet does not fast-charge (SuperVOOC is not supported). Without the dual boot,
Android does not start after the Fedora install. The display's idle refresh mode is off; do not add
`msm.dpu_idle_refresh_ms` to the kernel command line ([INSTALL-GUIDE section 7](docs/INSTALL-GUIDE.md#7-after-the-install)).

## Before you start

**The starting state.** The install was carried out on one tablet. It started from LineageOS 24.0 on slot b (slot a
without an Android system), with stock 11.A.38 firmware on both slots. Rooted debugging and USB debugging were on.
A different starting state (stock OxygenOS, slot a active, another firmware release) has not been tried, so it is
untested. ([INSTALL-GUIDE.md](docs/INSTALL-GUIDE.md), "Read this first".)

**The tablet.**

- An **unlocked** boot loader. Unlocking erases the tablet; its steps are in [guide 04, section 1.3](docs/guide/04-BUILD-YOUR-OWN.md).
  The orange warning at boot is expected.
- Stock firmware **11.A.38 on both slots**. Never flash or boot an older firmware: it breaks anti-rollback.
- Battery above 60 % for every write.
- About 13 GB are written. Android's data is lost with the first write.

**The PC.** Android platform tools (`adb`, `fastboot`), the USB cable you have used with this tablet, mains power, and
no sleep during the install. About 30 GB free for the backup and the files.

**The install files.** No install image is published. The image must contain the items of
[INSTALL-GUIDE section 2](docs/INSTALL-GUIDE.md#2-what-you-need), among them files taken from the tablet itself (the
guide names the sensor calibration registry and the Bluetooth address). Its unpacked size must equal your `userdata`
exactly. The U-Boot file for `boot_b` needs an AVB footer made for your tablet's current `boot_b`. Check every file's
SHA-256 before you write it.

The Windows installer ([tools/installer](tools/installer/README-INSTALLER.md)) cannot install yet: it refuses both
writes until a generic install image exists. Its read-only backup part works.

**What is never written, and why.** The Fedora install (Parts A and B) writes two partitions only (`userdata` and
`boot_b`). The optional dual boot (Parts C and D) also changes LUN 0's partition table, writes slot b's Android boot
partitions, `boot_a` and `super`, and erases `userdata` and `metadata`, exactly as its steps list. Every group
below except "Android system" and "Partition table" is never written in any part:

| Group | Partitions (examples) | Why, in plain words |
|---|---|---|
| Boot firmware | `xbl*`, `abl*`, `tz*`, `hyp*`, `aop*`, `uefi*`, `soccp*`, `engineering_cdt*` and the others of the boot chain | They start fastboot. No public emergency loader exists for this tablet, so a broken chain cannot be repaired at home. |
| Radio and DSP firmware | `modem*`, `bluetooth*`, `dsp*` | Signed and version-locked. Fedora only reads them. |
| Per-device data | `persist`, `cdt`, `ddr`, `dinfo`, `ocdt` | Calibration and identity of one tablet. They exist nowhere but in its backup. |
| Security state | `devinfo`, `keystore`, `frp`, `secdata`, `uefivarstore` | One wrong byte can lock the boot loader or the secure world. |
| Android system | `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `misc` | Fedora does not need them. Leaving them alone keeps the way back short. |
| Partition table | the GPT of every unit | The Fedora install does not repartition. Part C changes LUN 0's table for the dual boot. |
| UFS storage firmware | the storage chip's own firmware | A wrong update is the one software path to a dead tablet that does not go through a partition. |

**The rules of the procedure** ([INSTALL-GUIDE section 3](docs/INSTALL-GUIDE.md#3-the-rules-for-the-whole-procedure)):

1. The install types only `fastboot flash userdata ...` and `fastboot flash boot_b ...`. The guide's rule list says
   never `fastboot -w`, `flashall`, `update`, `set_active`, `erase`, `format` or `flashing lock`. Parts C and E show
   where other guide steps use `erase` or `-w`; read those notes before you type the commands.
2. Writes are made only in the tablet's own boot loader: `fastboot getvar product` must answer `canoe`.
3. If a screen, a message or a number differs from the guide, stop. Do not retry a write with other arguments.

## Manual install

The commands below are copied from the guides, and each part names its guide section. For the reasons behind a step,
read [INSTALL-PLAN.md](docs/INSTALL-PLAN.md). Battery above 60 % for every write.

- **Part A**: backups and reads only.
- **Part B**: Fedora and U-Boot, the two writes of the install (`userdata`, then `boot_b`).
- **Part C**: the dual-boot split (optional): Fedora's partition table, then LUN 0's table.
- **Part D**: BlissROM (optional): Android's partitions, `super`, `userdata` and `metadata`.
- **Part E**: using the tablet, updates and the way back.

### Part A - backups (read only)

1. **A full backup** of every partition except `userdata` ([INSTALL-GUIDE section 4, step 1](docs/INSTALL-GUIDE.md#4-before-the-first-write-read-only)).
   The guide gives no script. The project read each partition from `/dev/block/by-name/<name>` with `dd` and hashed
   both copies ([guide 04, section 1.4](docs/guide/04-BUILD-YOUR-OWN.md)). Keep two copies on two disks. Never upload them.
2. **The stock 11.A.38 images** with their checksums, for the way back (step 2).
3. **Your own files.** Copy them off the tablet. Android's `/data/vendor` can be copied with `adb root` (step 3).
4. **The current `boot_b`**, saved from the running Android system with `adb root`, read only. Keep it as
   `boot_b-saved.img`; the undo in Part B uses that name. Take it from the system that runs today, not from an older
   backup. Check that `misc` does not hold `boot-recovery` or `boot-fastboot` (step 4).
5. **The slot flags and the rescue keys.** Switch the tablet off, hold **Volume Down + Power** until the boot loader's
   fastboot screen shows, connect USB, and read (these commands only read; step 5):

```bash
fastboot getvar product                # canoe
fastboot getvar unlocked               # yes
fastboot getvar current-slot           # b
fastboot getvar slot-successful:b
fastboot getvar slot-unbootable:b
fastboot getvar slot-retry-count:b
fastboot getvar partition-size:boot_b  # 0x6000000
fastboot getvar partition-size:userdata
fastboot reboot
```

**Dual boot only, after Part B:** the dual-boot backup, read only, on the installed Fedora. Copy the folder to the PC and
check it there ([DUAL-BOOT.md, Backups first](docs/DUAL-BOOT.md#backups-first)):

```bash
sudo bash tools/dualboot/dualboot-backup.sh    # default output /var/tmp/dualboot-backup-<date-time>
sha256sum -c SHA256SUMS                         # on the PC, in the copied folder
```

The dual-boot backup holds the tablet's partition GUIDs and tables. Keep it private.

### Part B - Fedora and U-Boot

The file names below are the guide's. The v7 release names the images `u-boot-iceland-v7.img` (plain) and
`u-boot-iceland-v7-footered.img`. Check each file's SHA-256 against the release's `SHA256SUMS` before a write.

1. **RAM test of U-Boot, before any write** (step 6). `fastboot boot` loads the image into RAM only. Nothing is written
   and the slot flags do not change. U-Boot finds no Fedora and waits in its own fastboot.

```bash
fastboot boot u-boot-iceland-usb.img       # the plain install build; RAM only
fastboot getvar product                    # now: oneplus-iceland (U-Boot)
```

   Return with **Volume Down + Power** or `fastboot reboot`.

2. **Write 1: the Fedora image into `userdata`** (section 5). ABL accepts a sparse image in pieces of up to 805 MB; the
   PC's fastboot reports each piece. Expect several minutes. Do not touch the cable.

```bash
adb reboot bootloader
fastboot getvar product                    # canoe
fastboot getvar current-slot               # b
fastboot getvar partition-size:userdata    # must equal the image's unpacked size
fastboot flash userdata fedora-iceland.sparse.img
```

   Until write 2, Android starts and says its data may be corrupt. **Never confirm the factory reset**. Choose
   "Try again" or power off.

3. **Proof, still tethered.** Run the plain build again (`fastboot boot u-boot-iceland-usb.img`). Fedora's first-boot
   setup starts: language, keyboard, Wi-Fi, privacy, and your user account. The image has none. Repeat the tethered
   boot until Fedora reaches the desktop reliably.

4. **Write 2: U-Boot into `boot_b`.** Only after Fedora started tethered. Switch the tablet off, hold
   **Volume Down + Power**, connect USB (install guide, section 6):

```bash
fastboot getvar product                    # canoe (the tablet's own boot loader)
fastboot getvar current-slot               # b
fastboot flash boot_b u-boot-iceland-footered.img
fastboot getvar slot-successful:b          # read the flags before the reboot
fastboot getvar slot-retry-count:b
fastboot reboot
```

   Flashing `boot_b` clears slot b's *successful* flag and sets its retry count to the maximum. Each normal power-on
   then uses one try until the running system marks the slot good (`iceland-slot-mark`, iceland-device 0.28-8 or newer).

5. **Proof.** Unplug the PC. Switch the tablet off and on a few times: the menu appears and Fedora reaches the
   desktop. In Fedora, `journalctl -u iceland-slot-mark` shows the marking, and `qbootctl` lists slot b as active,
   successful and bootable. Then read the flags again (Volume Down + Power, then the `getvar` lines of Part A, step 5):
   `current-slot` is `b`, `slot-unbootable:b` is `no` and `slot-successful:b` is `yes`.

   **Undo:** if the retry count falls from boot to boot and slot b is not marked, stop booting and restore the copy:

```bash
fastboot flash boot_b boot_b-saved.img      # the file of Part A, step 4
```

   Android then starts without its data. Fedora stays in `userdata` and can still be started tethered.

### Part C - dual boot: split LUN 0 (optional)

This part adds BlissROM's space and follows [DUAL-BOOT.md](docs/DUAL-BOOT.md), steps W0a to A. The scripts refuse to
run in the wrong state. Most steps have a check and an undo. Who runs what:

- **On the installed Fedora, as root:** W0a, W0b, W1, W2 and W2b.
- **In a Linux started from RAM** (`fastboot boot`, no partition of LUN 0 mounted): W3. The guide names its needs:
  `dd`, `cmp`, `sha256sum` and `blockdev`. No such image is published, and the guide gives no tested recipe for one.
- **In the boot loader's fastboot, from the PC:** W4, W5b, W5k, W5c, W6, M and A.

Compute the numbers from your own backup, not from the examples, with `tools/dualboot/gpt-plan.py` (it never writes to a
device). The scripts refuse a disk of another size. Change their constants (`F`, `NI`, `P3START` in `dualboot-w2.sh`,
the `--blocks` default in `w3-gpt.sh`) as the guide says.

| Step | Where | What | Undo |
|---|---|---|---|
| W0a | Fedora | Install iceland-device [0.28-25](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-25) or newer. Check: the package's `--check` rows pass. | Install the previous package again with `sudo rpm -Uvh --oldpackage ...`. |
| W0b | Fedora | `sudo systemctl mask systemd-repart.service` (repart would grow Fedora's disk back over the new end). Check: `systemctl is-enabled systemd-repart` = `masked`. | `sudo systemctl unmask systemd-repart.service` |
| W1 | Fedora | `sudo btrfs filesystem resize 120g /`, then `sudo btrfs scrub start -B /`. Check: no errors. | `sudo btrfs filesystem resize max /` |
| W2 | Fedora | Fedora's own partition table for the smaller disk: `gpt-plan.py shrink HEAD TAIL <DISK_BLOCKS> <NEW_BLOCKS> plan/ --trust-primary`, then `sudo bash dualboot-w2.sh --dry-run`, then `sudo bash dualboot-w2.sh --write --confirm CODE` (the dry run prints CODE). Check: two reboots, Fedora starts normally, and `sfdisk -d` on the loop disk shows p3 ending at `NEW_BLOCKS - 6` (32,730,382 in the tested example). | `sudo bash dualboot-w2.sh --restore --confirm CODE` |
| W2b | Fedora | Only with iceland-device 0.28-24 (not needed with 0.28-25), right before W3: `sudo grub2-editenv - list`. If there is no `iceland_args` line, `sudo grub2-editenv - set iceland_args=iceland.carrier=fedora`; otherwise add ` iceland.carrier=fedora` to its value. Check: `grub2-editenv - list` shows it. | `sudo grub2-editenv - unset iceland_args` (or the old value). Without W3, Fedora waits for a `fedora` partition: at the GRUB menu press `e`, remove `$iceland_args` from the `linux` line for that start, then unset it. |
| W3 | Linux in RAM | LUN 0's table: `gpt-plan.py split HEAD TAIL <LUN0_BLOCKS> <USERDATA_START> plan/ --userdata-last <USERDATA_LAST>`, then `w3-gpt.sh --dry-run`, then `w3-gpt.sh --write --confirm CODE`. Check: `RESULT PASS`; then `fastboot getvar partition-size:userdata` and `partition-size:fedora` show the new sizes, and Fedora starts from the `fedora` partition. | `w3-gpt.sh --restore --confirm CODE`, from the same RAM system. |
| W5b | Boot loader fastboot | `fastboot flash vendor_boot_b vendor_boot.img`, then `init_boot_b`, `dtbo_b`, `vbmeta_system_b`, `vbmeta_vendor_b` and `vbmeta_b` with their images. Check: slot b's flags are unchanged; U-Boot and Fedora still start. | Flash the backup's `parts/<name>.img` back. |
| W5k | Boot loader fastboot | `fastboot flash boot_a boot.img` (BlissROM's kernel image only). Check: slot b stays current. | Flash the backup's `parts/boot_a.img` back. |
| W5c | PC, then boot loader fastboot | `mk-super.py SUPER_HEAD IMG_DIR super-bliss.img`, then `check-super.py super-bliss.img IMG_DIR` (last line `SUPER-CHECK: 0 failure(s)`), then `fastboot flash super super-bliss.img`. | Not needed for Fedora. |
| W4 | Boot loader fastboot | `fastboot erase userdata`, then `fastboot erase metadata`. Only after W3's sizes are confirmed. | None: this erases Android's data. |
| M | Boot loader fastboot | RAM test, writes nothing: `fastboot boot u-boot-iceland-v7.img`, then choose BlissROM. | - |
| W6 | Boot loader fastboot | `fastboot flash boot_b u-boot-iceland-v7-footered.img` (U-Boot updated in place). Check: the menu shows Fedora, BlissROM and the boot loader. | Flash the backup's `parts/boot_b.img` back. |
| A | Boot loader fastboot | After one start of each system: power on with Volume Down held, then `fastboot getvar current-slot` (`b`) and `fastboot getvar slot-successful:b` (`yes`). Reads only. | - |

> **Note on W4.** The install guide's rules forbid `erase`. This step uses it for Android's data, as the dual-boot
> guide says. Run it only after W3 and the sizes are checked.

**Example, not a target:** the tested tablet had 256 GB of storage. Its split gave `fedora` about 124.9 GiB and
`userdata` about 96.0 GiB, with 1 MiB kept unused at the end of LUN 0. Yours will differ.

### Part D - BlissROM (optional, after Part C)

Use BlissROM v20.1 for `iceland` (the OTA zip) and a `payload.bin` extractor. The tested images are listed in
[DUAL-BOOT.md](docs/DUAL-BOOT.md). Each one goes to a fixed place. The OTA's firmware images are not flashed.

| Image | Goes to |
|---|---|
| `boot.img` | `boot_a`, the kernel only. Never into `boot_b` (that would replace U-Boot) or `recovery_b`. |
| `vendor_boot.img`, `init_boot.img`, `dtbo.img`, `vbmeta.img`, `vbmeta_system.img`, `vbmeta_vendor.img` | the `_b` partitions of the same names (W5b). |
| `system.img`, `system_ext.img`, `product.img`, `odm.img`, `vendor.img`, `system_dlkm.img`, `vendor_dlkm.img` | the `super` image of slot b, built by `mk-super.py` and checked by `check-super.py` (W5c). |

Why not `boot_b` or `recovery_b`: ABL starts `recovery_b` only when it has no kernel, and then with `boot_b`'s kernel
(U-Boot), so a kernel in `recovery_b` cannot start Android. `boot_a`, on the unused slot a, holds the kernel instead.

Keep in mind ([DUAL-BOOT.md, Keep in mind](docs/DUAL-BOOT.md#keep-in-mind)):

- Turn off BlissROM's automatic updates, and install nothing from its updater. The updater switches to slot a, which
  skips U-Boot.
- Never flash a BlissROM image into `boot_b`. Never use Settings > "Erase all data" in BlissROM.
- Never `fastboot set_active a`. Let each start finish, so that slot b is marked good.

### Part E - using the tablet, updates, the way back

- **The menu.** It appears at power-on. Volume Up and Volume Down move the highlight, Power selects. Fedora starts after
  5 s if nothing is chosen. The install guide (section 1) names only Volume Down for moving; the dual-boot guide names
  both keys.
- **The boot loader's fastboot.** Hold **Volume Down + Power** (about 15 s) until its fastboot screen shows, or hold
  Volume Down at power-on, or choose "Boot loader (fastboot)" in the menu. Holding Power alone restarts the tablet, and
  that counts as another try of slot b.
- **From Fedora, `systemctl reboot bootloader` does not reach the boot loader.** It lands in Fedora. This is unsolved.
- **Updates.** Use GNOME Software or `dnf upgrade`, as on any Fedora. Updates can only change files inside the Fedora
  disk (in `userdata`, or in `fedora` after the split). A read-only snapshot is taken before each change, with a
  rollback entry in GRUB's menu. Kernels from this project come from the tablet's own repository; a new kernel boots
  once as a trial. Fedora holds back the sensor programs and `alsa-ucm` ([INSTALL-GUIDE section 7](docs/INSTALL-GUIDE.md#7-after-the-install)).
- **Never from inside Fedora:** no partitioning tool on the internal storage, no `dd` to `/dev/sd*`, no firmware or
  boot loader tool. The device package makes the other partitions read-only.
- **Going back.** [INSTALL-GUIDE section 8](docs/INSTALL-GUIDE.md#8-back-to-stock-oxygenos) gives the table. To undo only
  write 2, flash the saved `boot_b` back (Part B, step 5). The full return to stock is written as a script and
  dry-run, and was never executed. Its table says to erase `userdata` and `metadata` with `fastboot -w`, which the
  install's rule list forbids; read section 8 before you type it. A way back to LineageOS after the install is not written down.
- **If something differs.** Stop and write nothing more. [INSTALL-GUIDE section 9](docs/INSTALL-GUIDE.md#9-if-something-is-not-as-described)
  lists what each symptom means and what to do.

## Downloads

Everything below is a published release with a `SHA256SUMS` file. Check your downloads with `sha256sum -c SHA256SUMS`.

| What | Version | Release page | Files |
|---|---|---|---|
| Kernel (`kernel-iceland`, Fedora 44 aarch64) | q89w, kernel `7.3.0-rc7-iceland-00519` (the current queue q90i, `7.3.0-next-20261020-iceland-00463`, is published as source: [tag q90i](https://github.com/mzakamin-hub/iceland-linux/tree/q90i)) | [iceland-linux q89w](https://github.com/mzakamin-hub/iceland-linux/releases/tag/q89w) | RPM, source RPM, build config, `SHA256SUMS` |
| U-Boot, install build | v7 (2026-10-17) | [iceland-u-boot v7-2026-10-17](https://github.com/mzakamin-hub/iceland-u-boot/releases/tag/v7-2026-10-17) | plain image (RAM test), footered image (`boot_b`), `SHA256SUMS` |
| `iceland-device` (the tablet's settings) | 0.28-29 (0.28-32 is published as source: [packaging/iceland-device](packaging/iceland-device/)) | [iceland-device-0.28-29](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-29) | noarch RPM, source RPMs, `SHA256SUMS` |
| `iceland-firmware` (generic firmware) | 11.A.38-6 | [iceland-firmware 11.A.38-6](https://github.com/mzakamin-hub/iceland-firmware/releases/tag/11.A.38-6) | noarch RPM, source RPM, `SHA256SUMS` |
| Windows installer (blocked for writes) | in iceland-device 0.28-16 | [iceland-device-0.28-16](https://github.com/mzakamin-hub/iceland-mainline/releases/tag/iceland-device-0.28-16) | `Install-Pad4Linux.ps1`, `README-INSTALLER.md`, `SHA256SUMS` |

The Fedora disk image and the install image are **not** published. [Guide 04](docs/guide/04-BUILD-YOUR-OWN.md) covers
building the kernel, U-Boot and the packages, and [INSTALL-GUIDE section 2](docs/INSTALL-GUIDE.md#2-what-you-need) says
what the disk image must contain. The guides give no complete recipe for the disk image. Older releases are on each
repository's releases page.

## Repositories

All repositories are public under the GitHub user `mzakamin-hub`. The guide set is indexed in
[docs/guide/INDEX.md](docs/guide/INDEX.md).

| Repository | Default branch | What it holds |
|---|---|---|
| [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline) (this one) | `main` | The guides, the feature list, the device package (`packaging/iceland-device`), the dual-boot tools (`tools/dualboot`) and the installer (`tools/installer`). |
| [iceland-linux](https://github.com/mzakamin-hub/iceland-linux) | `main`; current work on `iceland-7.3-rc7-next` | The kernel: a patch queue on Linux v7.3-rc7, the build scripts and the `kernel-iceland` package. |
| [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) | `main` | U-Boot v2026.10-rc5 for the tablet, with the install build and its boot menu, and the build scripts. |
| [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware) | `main` | The generic firmware of stock 11.A.38 as one RPM, with its manifest, the exclusion list and the vendor notices. |
| [android_device_oneplus_iceland](https://github.com/mzakamin-hub/android_device_oneplus_iceland) | `lineage-24.0` | The LineageOS 24.0 device tree for the tablet (the Android side). |
| [proprietary_vendor_oneplus_iceland](https://github.com/mzakamin-hub/proprietary_vendor_oneplus_iceland) | `lineage-24.0` | The LineageOS 24.0 vendor tree: the proprietary files and the radio images (Git LFS). |

## Glossary

| Term | Meaning |
|---|---|
| **ABL** | Android Boot Loader: the tablet's own boot loader, from OnePlus and Qualcomm. It is closed and the project never writes it. Its fastboot is the rescue path. |
| **fastboot** | The PC tool and the boot loader's USB mode for writing and booting images. `fastboot boot` runs an image from RAM. `fastboot flash` writes a partition. |
| **slot (A/B)** | Each boot partition exists twice, `_a` and `_b`. The boot loader starts the active slot and keeps a successful flag, an unbootable flag and a retry count for each. |
| **boot_b** | The boot partition of slot b. The install writes U-Boot there. |
| **U-Boot** | The open-source boot loader. The project's build in `boot_b` shows the menu and starts Fedora or BlissROM. |
| **sparse image** | An Android image format that stores only the used blocks. `fastboot flash` takes it directly and sends it in pieces. |
| **super** | Android's container for its dynamic system partitions (`system`, `vendor`, `product` and others). The dual boot writes BlissROM's seven of them into it. |
| **LUN** | One of the tablet's six UFS storage units, `sda` to `sdf`. Each uses 4096-byte blocks. LUN 0 holds the split of Part C. |
| **GPT** | The GUID partition table at the start and end of a LUN. The dual boot changes LUN 0's table. |
| **RAM boot** | Starting an image with `fastboot boot`. Nothing is written, and a reboot returns the tablet to its installed boot. |

## Getting help

Open an issue in the repository the problem concerns: `iceland-mainline` for the install and the guides, `iceland-linux`
for the kernel, `iceland-u-boot` and `iceland-firmware`. Never post serial numbers, MAC or Bluetooth addresses, Wi-Fi
network names, backups or other files from your tablet.
