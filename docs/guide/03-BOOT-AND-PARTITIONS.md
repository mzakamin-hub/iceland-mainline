# 03 - Boot chain, partitions, and what the install changes

The installed boot chain is: ABL -> `boot_b` (the U-Boot install build, with an AVB footer) -> the EFI boot manager on
`userdata` -> Fedora's shim and GRUB -> `kernel-iceland`. This chapter explains the stock chain, the A/B slots, verified
boot, the RAM boot used for testing, and the installed chain. For the partition list see `02-HARDWARE.md` section 6.

> **Safety.** This document explains; it is not a procedure. The write procedure is `docs/INSTALL-GUIDE.md`, and every
> write in it is the user's own step. The project's tools never write the tablet.

## 1. The stock boot chain

```
PBL (boot ROM)
 -> XBL + xbl_config        (LUN sdb for slot a, sdc for slot b)
 -> TZ, Gunyah hypervisor (hyp), AOP, CPUCP, TME firmware; the SoCCP (charger co-processor) is started here
 -> UEFI (uefi_a/_b)        Qualcomm's UEFI core
 -> ABL (abl_a/_b)          the OnePlus-built Android boot loader; fastboot lives here
 -> boot_<slot>             kernel (header v4; stock: Google GKI 6.12.58)
    + vendor_boot_<slot>    14 base device trees + vendor ramdisk + bootconfig
    + init_boot_<slot>      generic ramdisk
    + dtbo_<slot>           device-tree overlays (this tablet uses the "iceland-O IN" entry)
 -> Android
```

What ABL does that matters for Linux:
- It picks the base device tree from `vendor_boot` by `qcom,msm-id` / `qcom,board-id` and applies the `dtbo` entry.
  It adds the **memory map** (20 segments; one has size 0), the command line and the bootconfig. A device tree booted
  straight from ABL must carry `qcom,msm-id = <0x295 0x20000 ...>` and `qcom,board-id = <8 0>`, and must never lack
  the real memory map: on the OnePlus 15 a zero-size memory node led to the emergency-download mode.
- It leaves the display running (a 3392x2400 framebuffer at 0xfc800000, MDP at 650 MHz) and some rails and power
  domains on. Linux must hold them until its own display driver takes over (queue 0022, 0026-0027).
- **Keys:** Volume Down + Power from off enters ABL's fastboot. Power + Volume Up starts `recovery_<slot>` in Qualcomm's
  open ABL; this key has not been checked on the Pad 4.
- **A reboot from Linux is a PS_HOLD hard reset** (DDR is re-initialised), so pstore / ramoops do not survive.
  Android's `/proc/bootloader_log` shows the reset reason afterwards.

**Fastboot facts** (`fastboot getvar`, read only): `product: canoe`, `secure: yes`, `unlocked: yes`,
`is-userspace: no` (ABL; Android's fastbootd is a different mode), `max-download-size: 805306368`. Larger images are
split by the PC's fastboot client into sparse pieces.

**Emergency download (EDL, Qualcomm 9008)** is not a recovery path for this tablet: no signed loader ("firehose") is
public. Fastboot in ABL is the floor. That is why the boot firmware is never written.

## 2. A/B slots and anti-rollback

- Every firmware and boot partition exists twice (`_a`, `_b`). ABL boots the **active** slot. Per slot it keeps
  `slot-successful`, `slot-retry-count` and `slot-unbootable`.
- **How the flags move.** From Qualcomm's open ABL source (CodeLinaro edk2); OnePlus's build is closed, and the points
  marked *measured* were checked on the tablet.
  - **Flashing a slot's boot partition resets that slot's flags.** In ABL's fastboot, `HandleRawImgFlash` calls
    `FastbootUpdateAttr`: *successful* and *unbootable* are cleared, *priority* and *retry count* are set to their
    maximum. Only names starting with "boot" trigger this, on flash and on erase (`FastbootCmds.c`); a `recovery_b`
    flash leaves slot b's flags alone.
  - **Every normal boot of a slot that is not "successful" counts its retry count down by one** (*measured*: one boot
    into U-Boot from `boot_b` used one try). Recovery, fastboot and charger boots do not count (*measured* for U-Boot's
    `fastboot reboot-bootloader`, which uses none) (`LinuxLoader.c` `IsABRetryCountUpdateRequired`,
    `PartitionTableUpdate.c` `FindBootableSlot`).
  - **At 0, `HandleActiveSlotUnbootable` marks the slot unbootable.** If the other slot is bootable and successful,
    ABL switches to it and resets; otherwise it stops in its fastboot.
  - **Marking a slot successful** writes the flags into the boot partitions' GPT entries. Android does it after a good
    boot (its boot-control HAL / update_verifier). U-Boot never does. On the installed system Fedora does it:
    `iceland-slot-mark` runs `qbootctl -m` once after a good boot, if the slot is not yet marked (`iceland-device`
    0.28-8 and newer; see section 5).
  - **Consequence:** without the marking, a U-Boot in `boot_b` would run out of tries after the maximum number of
    normal power-ons. The install build therefore never resets by itself (a reset is another boot of the slot).
- **Anti-rollback:** never flash or boot firmware older than 11.A.38. The factory slot b of the project's tablet held
  11.A.32 until LineageOS's `copy-partitions` step made both slots' firmware identical (11.A.38). The project never
  switches slots; `set_active` belongs only to the return to stock.

## 3. Verified boot (AVB) and the unlocked state

- The top-level `vbmeta_<slot>` describes or chains the other images. On this tablet `boot` is a **chained** partition:
  it carries its own small vbmeta in an AVB footer at the end of the partition.
- On a **locked** tablet any change stops the boot. On an **unlocked** tablet ABL shows the "orange" warning and
  continues after *verification* errors (a wrong hash, a key that does not match, a rollback index).
- ABL does not continue after *invalid metadata*, such as an image without the footer a chained partition needs.
- **Proven on the PC** with a libavb harness modelled on Qualcomm's public ABL source (`VerifiedBoot.c`), and then on
  the tablet:
  - a plain U-Boot image in `boot_b` gives `INVALID_METADATA`: ABL stops, marks slot b unbootable and switches slots;
  - the same image with an AVB hash footer (the key `vbmeta_b` chains `boot` with, the current rollback index) gives
    `PUBLIC_KEY_REJECTED`, and ABL continues, as it does for a custom ROM's boot image;
  - so the image written to `boot_b` **must carry the footer** (`07-INSTALL-REVIEW.md` R-1). On the tablet, ABL starts
    the footered U-Boot from `boot_b` and Fedora boots.
- **The footer also feeds the TEE.** ABL's `GetOsVerAndSecPactchLevel` hands the trusted environment the
  `os_version` **and** `security_patch` of the boot image's AVB footer, or the boot header's values when the footer
  has none. The footer must therefore carry both, copied from the slot's current `boot` image.
- `fastboot boot` (a RAM boot) does not verify the **boot image** it is sent. It still verifies `dtbo`, `vendor_boot`
  and `init_boot` from the slot. That is why RAM boots work without touching `vbmeta`, and why no RAM boot can prove how
  ABL treats a written `boot_b`.
- **Never relock** the boot loader while anything but verified stock is installed.

## 4. Booting Linux from RAM: nothing written

Before the install every test ran from RAM, and RAM boots remain the rescue path: `fastboot boot` loads an image into
RAM, and a reboot returns to whatever the tablet boots normally. The project's RAM test images and their runner are not
published.

```
PC: fastboot boot <u-boot image>        -> ABL loads it into RAM (no write, no verification)
    U-Boot (iceland-u-boot)             shows its text on ABL's framebuffer, waits in its OWN fastboot
                                         (USB product id 0xd00d, the same as ABL's, so drivers bind)
PC: fastboot boot <linux image>         -> U-Boot finds kernel, initramfs and device tree in the image
    bootefi                              starts the kernel's EFI stub (earlycon=efifb: output from the first line)
    Linux 7.3 + queue                    our device tree; U-Boot applies ABL's memory map
    initramfs / root                     a small init with USB networking to the PC, or a full Fedora root
reboot                                   PS_HOLD reset -> ABL -> the tablet's normal boot, untouched
```

Details:
- **U-Boot** (`iceland-u-boot`, v2026.10-rc5 + 14 infiniti + 12 Pad 4 patches; the install build is the patch set
  0004-0012 on top of the board patches 0001-0003).
  - It is packed as an Android boot image, header v4, with `kernel = gzip(u-boot.bin)`. U-Boot's own device tree sits
    inside the gzip stream; ABL drops a tree appended after it.
  - It is built **without fastboot flashing** (`CONFIG_FASTBOOT_FLASH` off), so it cannot write the storage.
  - Linux is started through EFI (`bootefi`). An earlier `bootm` path ran the kernel in place from an unaligned buffer
    and failed.
- **Safe test habits:** a test runner that only uses `fastboot devices`, `getvar`, `boot`, `reboot` and `oem console`
  can never write; holding Power about 15 s always restarts the tablet.

## 5. The installed chain

Design: `docs/INSTALL-PLAN.md` sections 2-3.

```
ABL
 -> boot_b = the INSTALL build of U-Boot (with an AVB footer for the slot's current boot image)
      power-on boot menu, 5 s: Fedora (default) or the boot loader's fastboot
      scsi scan; a GPT partition named "fedora" wins (possible dual boot), else "userdata"
      blkmap: map that partition as a disk with the UFS's 4096-byte blocks (read through U-Boot, no copy)
      one explicit boot option = blkmap partition 1, /EFI/fedora/shimaa64.efi (efidebug, RAM only)
      bootefi bootmgr  (EFI variables are kept in RAM only: nothing is stored; no vendor LUN is tried)
      if nothing boots: U-Boot's fastboot loop; it never resets or powers off by itself
 -> shim  (EFI/fedora/shimaa64.efi on the image's EFI System Partition; shim's fallback is not used)
 -> GRUB 2.12  (Fedora's; reads the BLS entries in /boot/loader/entries)
 -> kernel-iceland (the project's rpm) + its device tree
      (U-Boot loads <ESP>/dtb/qcom/kaanapali-oneplus-iceland.dtb and applies ABL's memory map; with the
       per-kernel option GRUB loads /boot/dtb-<version>/... and hands it through U-Boot's EFI DT fixup protocol)
 -> dracut initramfs with the module "90iceland":
      sets every UFS block device read-only except userdata (and its LUN as a whole),
      attaches a partitioned loop device over userdata (direct I/O, 4 KiB blocks) -> loop0p1..p3;
      carries the GPU microcode and the SoCCP / ADSP / CDSP stack with the tablet's DSP firmware (the charger
      co-processor and USB-C must be up early); Wi-Fi, BT and video stay out (omit_drivers) and load after
      switch_root when /lib/firmware is reachable
 -> Fedora root: btrfs subvolume "root" on loop0p3, /boot (ext4) loop0p2, ESP (FAT32) loop0p1; SELinux enforcing
 -> first boot: systemd-repart grows the root partition to the whole userdata, growfs grows btrfs
 -> after a good boot: iceland-slot-mark marks the slot successful (qbootctl -m; the boot LUN is made writable for
    that one call only)
```

Why the disk image looks like this:
- **Every UFS LUN has 4096-byte logical blocks.** The official `Fedora-Workstation-Disk-44` aarch64 image is laid out
  for 512-byte sectors: a DOS partition table and a FAT16 ESP with 512-byte sectors. U-Boot's blkmap takes the target's
  4 KiB block size and refuses that FAT ("FAT sector size mismatch"), and Linux reads the table in 4 KiB units: written
  as it is, the image would not boot.
- The image is therefore re-laid: a GPT in 4 KiB units with the standard partition types, the ESP rebuilt as FAT32 with
  4096-byte sectors (the same files, compared by hash), `/boot` and the btrfs root copied unchanged.
- **The GPT also lets the root grow:** systemd-repart works only on GPT. On the original layout the root would have
  stayed at 10.3 GB.
- **The written file is an Android sparse image** whose unpacked size equals `userdata` exactly (237,159,641,088
  bytes on the tablet it was done on). Only about 13 GB of it is data.

**`efisp` vs our ESP.** The tablet's `efisp` partition (3 MiB, firmware side) is not used. Our ESP lives inside the
Fedora disk in `userdata` (see `02-HARDWARE.md` section 6).

**Seat belts inside the installed system** (`INSTALL-PLAN.md` section 2):
- the read-only udev rule for every other UFS partition (also in the initramfs);
- U-Boot's EFI layer may write only blkmap disks (U-Boot patch 0005);
- no FAT / ext4 / GPT writer linked into U-Boot;
- EFI variables are not stored;
- fwupd's plug-ins that could write boot code, EFI variables or the UFS device firmware are switched off (17
  plug-ins);
- dnf never installs Fedora's kernels, a rescue initramfs, akmods / dkms, bootupd, sdubby or U-Boot images;
- Fedora is pinned to release 44 until the next release has been tested on the tablet.

**Updates after the install** (`INSTALL-PLAN.md` section 6):
- New kernels come only from the project's repository, synced to the tablet's local repository (`iceland-repo-sync`).
- A new kernel boots once as a trial (GRUB `next_entry`). It becomes the default only after a confirmed boot.
- A btrfs snapshot of the root is taken before every dnf transaction (three kept), each with a "Roll back to ..." boot
  entry.

## 6. Testing the install image from RAM

```
PC: fastboot boot u-boot-iceland-rehearsal.img   (the install build's code WITHOUT SCSI / UFS support;
                                                    it cannot see the storage)
PC: fastboot boot head.boot.img                   (a gzip of the image's ESP + /boot with a small GPT)
                                                    -> unzip into RAM, blkmap of RAM, bootefi bootmgr
 -> shim -> GRUB -> kernel-iceland               (the same chain as installed)
 -> initramfs: every UFS device read-only FIRST; USB gadget up; root disk = NBD from the PC over USB
               (PC: the image + a copy-on-write overlay; the relay admits only the tablet's USB network address)
 -> Fedora as installed; the acceptance checks run; a guard returns the tablet to its normal boot on any stall
```

- **What it proves:** the image, GRUB on a 4 KiB disk, the kernel and initramfs, SELinux, the first-boot growth, the
  acceptance list, and the update / rollback mechanics.
- **What it cannot prove:** ABL's verified-boot check of a written `boot_b`; the install U-Boot's UFS path (SCSI scan,
  the `userdata` map); GRUB's environment write through U-Boot into the real UFS (the "boot once" mechanism); the loop
  device over the real partition. These are seen first in the tethered boot after write 1 and after write 2.
- Suspend is not tested this way: the USB gadget's suspend would cut the root disk.
- The project's tooling for this test is not published.

## 7. Why the install stays unbrickable and restorable (`INSTALL-PLAN.md` section 7)

**Unbrickable**
1. Only two partitions are ever written: `userdata` and the boot partition of the active slot (`boot_b`). XBL, ABL, all
   firmware, the per-device data (`persist`, `cdt`, `ddr`, `oplusreserve*`, ...), the security state (`devinfo`,
   `keystore`, `frp`, ...), Android's `super`, `vbmeta*`, `vendor_boot*`, `dtbo*` and every partition table stay
   untouched. So ABL's fastboot always answers to Volume Down + Power.
2. Never `set_active`, never lock the boot loader, never older firmware, never a storage-firmware update (fwupd
   plug-ins off).
3. Inside Fedora the other partitions are read-only from the first second (initramfs), and U-Boot cannot write them.
4. Do not let the battery run flat: UPower powers off at the critical level, the guard keeps its shutdown
   temperatures, and the charge limit keeps the cell between 80 and 85 % on a charger.

**Restorable**, from the smallest step to the largest:

| Level | Brings back | Needs the PC | Loses |
|---|---|---|---|
| L0 trial boot | a new kernel that never reached a confirmed boot is skipped on the next start | no | nothing |
| L1 previous kernel | GRUB's menu (3 s, volume keys): one of three kept kernels | no | nothing |
| L2 snapshot | "Roll back to ..." entry: the root before the last update | no | system changes since then |
| L3 RAM rescue | `fastboot boot` of a rescue image: mount, check, roll back, replace the kernel | yes | nothing |
| L4 the image | write the install image again | yes | everything in Fedora unless `/home` was copied |
| L5 stock | the stock boot set on both slots, `super` from the backup, `userdata` / `metadata` erased; never firmware | yes | Fedora |

A way back to LineageOS is not written down. The return to stock has been dry-run, never executed.

**Permanent**
- One source for the kernel (tested from RAM, then a trial boot).
- Boot code and firmware never update by themselves.
- Every Fedora version upgrade and every new U-Boot is tested from RAM first.
- Every limit in the device package is stock's or lower.

## 8. The two writes, in one paragraph each (for orientation only)

- **Write 1:** the tested sparse image into `userdata`, from ABL's fastboot. It erases Android's data. Until write 2, a
  plain power-on still starts Android, which reports damaged data: never confirm its factory reset. Then boot Fedora
  tethered (`fastboot boot` of the plain install build) and create the user account in the first-boot setup. Undo: write
  it again, or return to stock.
- **Write 2:** the footered install U-Boot into `boot_b`. A plain power-on then starts Fedora through the boot menu,
  and Fedora marks the slot successful after its first good boot. Undo: write back the `boot_b` image saved from the
  running system before the install. **Not** an older backup's `boot_b`: its header, key and rollback index may differ.

Both are described with their checks in `docs/INSTALL-GUIDE.md`; read `07-INSTALL-REVIEW.md` before either.
