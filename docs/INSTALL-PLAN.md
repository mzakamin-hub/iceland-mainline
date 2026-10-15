# OnePlus Pad 4: the design of the Fedora 44 GNOME install

This document explains why the install looks the way it does: which partitions are written and why only those, how
the image is laid out, how verified boot and the slot counter are handled, what keeps the installed system from
reaching the rest of the storage, how updates and rollbacks work, and the ways back. The steps are in
[INSTALL-GUIDE.md](INSTALL-GUIDE.md).

## 0. The idea in five lines

1. The whole Fedora system lives in ONE partition, `userdata`. A second small write puts U-Boot where the tablet's own
   boot loader starts it. Nothing else on the storage is written.
2. The tablet's boot loader (ABL, with fastboot) and all firmware stay as OnePlus shipped them. As long as they are
   untouched, fastboot always answers (Volume Down + Power) and can put everything back.
3. The image is tested from RAM first, through the same chain, before it is written; the file that was tested is the file
   that is written.
4. The way back to stock OxygenOS 11.A.38 stays open at every stage, with a backup of the tablet and the stock images.
5. On the installed system Fedora's updates can only change files inside `userdata`. The kernel and the few
   tablet-specific packages come from the project's own repository; boot code and firmware never update by themselves.

## 1. Before anything is written

| Check | Why |
|---|---|
| A full, checksummed backup of all partitions except `userdata`, and a second copy on another disk | it holds the per-device calibration and identity, which no download replaces |
| The stock 11.A.38 images with checksums | the way back |
| A copy of Android's own data (`/data/vendor`, your files) | the first write erases it |
| The current `boot_b`, saved from the running system | the undo of the second write, and the input of its AVB footer |
| The slot flags of both slots, read in ABL's fastboot | the second write changes them (section 5) |
| Fastboot reached with Volume Down + Power from a cold start | the rescue path that must work without Fedora and without U-Boot |
| The image booted from RAM through the installed chain, with its acceptance checks passed | the image is proven before it is written |
| An update and a rollback tested on that image | the update path is proven before it is needed |
| Charging, low-battery and thermal protection at stock's limits | the reason an installed tablet may be left alone on a charger |

## 2. Partitions: what may be written, what never

The storage has 6 units (LUNs) with 151 partitions, and **every unit has 4096-byte logical blocks**; this matters for
the image (section 3).

### May be written

| Partition | Size | What goes there | Undo |
|---|---|---|---|
| `userdata` (unit sda, the last and largest partition) | 237,159,641,088 bytes (`0x3737D0F000`) | the Fedora disk image, 4 KiB-native, as an Android sparse image | `fastboot -w` as part of the return to stock, or write the image again |
| ONE boot partition of the active slot: `boot_b` | 96 MiB | the U-Boot **install** build with an AVB footer made for the current `boot_b` | write back the `boot_b` saved from the running system |

`metadata` (64 MiB, Android's encryption keys for `userdata`) is touched only on the way back to Android, by
`fastboot -w`.

There are three U-Boot builds of the same tree: the RAM-boot build used for tests (it only waits for fastboot), the
**install** build that goes into `boot_b` (it finds the disk inside `userdata`, lets EFI programs write only that disk,
never resets or powers off by itself, and shows the power-on boot menu), and a **rehearsal** build: the install build's
code without any SCSI / UFS support, so it cannot see the storage at all. The image is tested with the rehearsal build;
the install build's own storage path is first seen when it is RAM-booted on the tablet and after the first write.

### Never written

| Group | Partitions | Why |
|---|---|---|
| Boot firmware | `xbl*`, `xbl_config*`, `uefi*`, `abl*`, `tz*`, `hyp*`, `aop*`, `devcfg*`, `qupfw*`, `shrm*`, `cpucp*`, `tme_*`, `multiimg*`, `featenabler*`, `imagefv*`, `uefisecapp*`, `keymaster*`, `secretkeeper*`, `spuservice*`, `oplus_sec*`, `pdp*`, `soccp*`, `dcp*`, `xbl_ramdump*` (both slots) | the chain that gives fastboot. There is no public emergency-download loader for this tablet, so a broken chain cannot be repaired at home |
| Radio / DSP firmware | `modem*`, `bluetooth*`, `dsp*` | signed and version-locked (anti-rollback); Fedora only reads them |
| Per-device data | `persist`, `cdt`, `ddr`, `dinfo`, `engineering_cdt*`, `ocdt`, `oplusreserve*`, `nonmodemst*`, `qweslicstore*`, `DRIVER`, `ompdt` | calibration and identity of one tablet; they exist nowhere but in its backup |
| Security state | `devinfo`, `keystore`, `frp`, `ssd`, `secdata`, `storsec`, `uefivarstore`, `spunvm`, `connsec`, `tzsc` | a wrong byte can lock the boot loader or the secure world |
| Android system | `super`, `vbmeta*`, `vendor_boot*`, `init_boot*`, `dtbo*`, `recovery*`, `boot_a`, `pvmfw*`, `splash*`, `misc` | not needed by Fedora; left alone so that the return to stock stays small |
| Partition tables | the GPT of all six units | no repartitioning |
| The storage chip's own firmware | the UFS device firmware | Fedora's `fwupd` lists the UFS storage as updatable; a wrong storage-firmware update is the one software path to a dead tablet that does not go through a partition. The device package switches off every `fwupd` plug-in that can write boot code, EFI variables, the UFS firmware or pins (17 plug-ins) |

Further rules that follow from the same reason: never `fastboot set_active` (only the return to stock does it, at its
end); never `fastboot flashing lock` while anything but verified stock is installed; never `erase` / `format` on anything
but `userdata` / `metadata`; never firmware older than 11.A.38. U-Boot is built without fastboot flashing, has no shell
and no FAT / ext4 / GPT writer, does not store EFI variables, and its EFI layer may write only the disk it maps from
`userdata`.

### Seat belts inside the installed Fedora

- A udev rule in `iceland-device` marks every block device of the internal storage read-only except `userdata`. The
  same rule is in the initramfs, so it holds from the first second; udisks ignores those devices.
- The firmware extractor opens every partition read-only.
- `fwupd`: only harmless plug-ins stay enabled.
- No tool in the image changes slots or the boot loader; EFI variables are not persistent (U-Boot keeps them in RAM).
- dnf never installs Fedora's kernels, a rescue initramfs (`dracut-config-rescue`), akmods / dkms, bootupd, sdubby or
  U-Boot images.
- The one storage write outside `userdata` that the installed system makes is the slot marking: `iceland-slot-mark`
  makes the boot unit writable for a single `qbootctl -m` call after a good boot, and logs it (section 5).

## 3. The image

Base: the official **Fedora-Workstation-Disk-44 aarch64** raw image (signature and sha256 checked).

**The official image cannot be written as it is.** It is laid out for 512-byte sectors: a DOS partition table and a FAT16
EFI partition. On the tablet's 4096-byte storage U-Boot refuses such a FAT ("FAT sector size mismatch") and Linux reads
the table in 4 KiB units, so it would not boot. The image is therefore re-laid:

- a GPT in 4 KiB units with the standard partition types;
- the EFI partition rebuilt as FAT32 with 4096-byte sectors (same volume id, the same files, compared by sha256);
- `/boot` (ext4) and the btrfs root copied unchanged and verified.

The GPT also lets the root grow: systemd-repart grows it at the first boot, which works on GPT only (on the original
layout the root would stay at 10.3 GB). The written file is an Android sparse image whose unpacked size equals
`userdata`; only about 13 GB of it are data.

The boot chain of the installed tablet:

1. ABL verifies `boot_b` (its AVB footer; unlocked: orange, continue) and starts U-Boot.
2. U-Boot maps `userdata` as a disk with 4 KiB blocks and starts the EFI boot manager with one explicit boot option for
   `\EFI\fedora\shimaa64.efi` on that disk (no other unit is searched, shim's fallback is not needed).
3. shim, then GRUB from the image's EFI partition; GRUB reads the boot entries and loads `kernel-iceland` and its device
   tree.
4. The initramfs (with the device package's dracut module) puts a partitioned loop device over `userdata`, so Fedora finds
   its root inside it as on any disk; SELinux enforcing.

Package set: Fedora Workstation's defaults (GNOME Software with Flatpak, Snapshot with libcamera, Ptyxis, Firefox, Files,
Settings, the GNOME apps, LibreOffice), plus `gnome-tweaks`, the Extensions app and the on-screen keyboard. Left out:
GNOME Boxes (the CPUs start at EL1, no KVM), virtual-machine guest agents, Fedora's kernels and U-Boot images. Added from
the project: `kernel-iceland`, `iceland-device`, `iceland-firmware`, `hexagonrpc`, `libssc`, `iio-sensor-proxy`, and the
tablet's unit-specific firmware files (owned by no package, so an update cannot replace them). The GPU microcode is
Fedora's `qcom-firmware` (upstream linux-firmware).

## 4. Testing the image from RAM before it is written

The tablet's storage is never written in these tests. The PC keeps the image unchanged and serves it over the USB cable
as a network block device with a copy-on-write overlay. The rehearsal build of U-Boot is RAM-booted with `fastboot
boot`; it receives a small "head" (the EFI partition and `/boot`), keeps it in RAM and starts shim and GRUB from it
exactly as it will from `userdata`. The initramfs makes every UFS device read-only first and then takes the root disk
from the PC. Everything from U-Boot on is the installed chain; only the disk is on the PC.

What it proves: the image, GRUB on a 4 KiB disk, the kernel and initramfs, SELinux, the first-boot growth of the root,
an acceptance list (boot chain and read-only rule, GNOME session, touch, Wi-Fi, Bluetooth, sound, the DSPs with no failed
firmware request, the GPU, battery and charge limit, power modes, rotation, video, both cameras, the default apps,
`rpm -V` of the project's packages), and the update and rollback mechanics (section 6).

What it cannot prove: ABL's verified-boot check of a written `boot_b`; the install build's UFS path; GRUB's environment
write through U-Boot into the real UFS (the "boot once" mechanism); the loop device over the real partition. These are
seen first after the writes. Suspend is not tested this way (the USB gadget's suspend would cut the root disk).

The project's rehearsal tooling is not published.

## 5. Verified boot and the slot counter

**Verified boot.** `vbmeta_b` chains `boot`, so ABL verifies whatever is in `boot_b` with Android's own code. A plain
U-Boot image there gives "invalid metadata", on which ABL does not continue, even unlocked (Qualcomm's open ABL: the
slot is marked unbootable). The written file therefore carries an AVB hash footer signed with the key `vbmeta_b` chains
`boot` with, with the current rollback index. ABL then reports "public key rejected", the same result an unlocked tablet
gives for a custom ROM's boot image, and continues in the orange state. The footer also carries the current OS version and
security patch level, because ABL hands the footer's values to the secure world. This was proven on the PC with
Android's own `avb_slot_verify()` on the tablet's pulled images, and on the tablet itself (Fedora boots from `boot_b`).

**The slot counter.** ABL keeps three flags per slot: *successful*, *unbootable* and a *retry count*.

- A flash of `boot_b` clears slot b's *successful* flag and sets the retry count to the maximum (only partitions named
  `boot*` do this; a `recovery_b` flash does not).
- Every normal power-on of a slot that is not *successful* uses one try. Fastboot (by the keys, or U-Boot's
  `fastboot reboot-bootloader`), recovery and charger starts do not. Measured on the tablet: a normal boot into U-Boot
  from `boot_b` used one try; `reboot-bootloader` used none.
- At zero ABL marks the slot unbootable; it switches to the other slot only if that one is successful and not
  unbootable, else it stops in its fastboot.
- U-Boot never marks a slot. Fedora does: `iceland-slot-mark` runs `qbootctl -m` once after a good boot, only if the slot
  is not yet marked. On the installed layout (the root on a loop device, the boot unit read-only) this works from
  `iceland-device` 0.28-8 on, which accepts a loop root backed by `userdata` and makes the boot unit writable for that one
  call only.
- U-Boot must never reset by itself: an early install build that reset itself after a start from `boot_b` used up all
  tries of the slot in one power-on. The install build holds in a fastboot loop instead (U-Boot patch 0008).

**The alternative that is not used:** U-Boot in `recovery_b`. Recovery starts never use a try and the flash does not
touch slot b's flags, but a plain power-on would still start Android, and making Fedora the default would need a third
write (`misc`). It is not needed, since Fedora marks the slot.

Dual boot (Android next to Fedora) is outside this design: it needs the partition table of unit sda changed. The install
build prefers a partition named `fedora` over `userdata`, so it is possible later, but it is not planned or tested.

## 6. Updates without breaking the tablet

Fedora can only write inside `userdata`. The worst an update can do is make Fedora itself not start; the boot loader and
fastboot are out of its reach, so a RAM rescue boot can always repair it, or the image can be written again.

| Package group | Source | Rule |
|---|---|---|
| Fedora's kernels | never installed | excluded; they have no Pad 4 support |
| `kernel-iceland` | the tablet's local repository (`/var/lib/iceland/repo`, filled by `iceland-repo-sync`) | three versions kept; a new one boots once and becomes the default only after a confirmed boot |
| `iio-sensor-proxy`, `hexagonrpc`, `libssc`, `iceland-device`, `iceland-firmware` | the project's packages | Fedora's repositories never offer `kernel-iceland*` or `iceland-*`; the sensor programs and `alsa-ucm` are held back from Fedora's updates |
| `dracut-config-rescue`, akmods / dkms, bootupd, sdubby, U-Boot images, `fwupd-efi` | never installed | excluded |
| GRUB, shim, Fedora's firmware packages, libcamera, Mesa, GNOME, everything else | Fedora | update normally |
| Fedora 45 | pinned to 44 | the release is pinned in dnf's configuration until the next release has been tested on the tablet |
| `fwupd` firmware updates | harmless plug-ins only | see section 2 |

`iceland-device` and `kernel-iceland` are protected packages: dnf refuses to remove the last of them. A read-only btrfs
snapshot of the root is taken before every transaction (also from GNOME Software and offline updates), each with a "Roll
back to ..." boot entry; the last three are kept.

## 7. Unbrickable, restorable, permanent

**Unbrickable**

1. Keep the write surface at two partitions. A U-Boot update is a new write of `boot_b`, with a footer made from the
   `boot_b` of that day; everything else updates inside `userdata`.
2. Fastboot through Volume Down + Power must work with whatever is in `boot_b`: ABL opens it before it looks at the boot
   partition, and entering it does not use a try.
3. Never lock the boot loader while Fedora is installed, never switch slots, never flash older firmware.
4. No storage-firmware update from Fedora, no EFI program writes outside `userdata`, every other partition read-only
   from the initramfs on.
5. Do not let the battery run flat: Fedora powers off at the critical level, the battery guard keeps stock's shutdown
   temperatures, and the charge limit keeps the battery between 80 and 85 % on a charger.

**Restorable**, from the smallest step to the largest:

| Level | What brings it back | Needs the PC | What is lost |
|---|---|---|---|
| L0 trial boot | a new kernel that never reaches a confirmed boot is skipped on the next power-on | no | nothing |
| L1 previous kernel | GRUB's menu (3 s, volume keys): one of the three kept kernels | no | nothing |
| L2 snapshot | "Roll back to ..." entry: the root as before the last update (three kept) | no | system changes since then, not your home folder |
| L3 RAM rescue | `fastboot boot` of a rescue image: mount, check, roll back, replace the kernel | yes | nothing |
| L4 the image | write the install image again | yes | everything in Fedora (copy your home folder first) |
| L5 stock | the return to stock with the backup and the stock images | yes | Fedora |

L0 to L2 were tested on the image before the install. L5 has been dry-run only, never executed. Keep the install image,
its checksum, the U-Boot files, the saved `boot_b`, the backup and the stock images together, and on a second disk.

**Permanent**

1. One source for the kernel: the project's repository, each version tested from RAM before it reaches the tablet, then
   a trial boot on the tablet itself.
2. Fedora updates normally; boot code does not move by itself, and the release stays pinned until the next one is tested.
3. Every new U-Boot and every Fedora release upgrade is tested from RAM first.
4. Every limit in the device package is stock's or lower.
