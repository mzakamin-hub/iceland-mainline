# 03 - Boot chain, partitions, and what the install changes

State: 2 Oct 2026, about 23:00. Sources: `iceland-mainline/docs/reference/pad4-hardware-boot-partitions.md` sections 2-4,
`docs/KNOWLEDGE.md` sections 4, 9, 12, `docs/tests/README.md` (U-Boot and Linux tests 1-7), `docs/INSTALL-PLAN.md`,
`~/mainline/build/wf/install/REPORT.md` and `NEXT.md`, `iceland-u-boot` (`uboot.pin`, `tools/diag/`,
`scripts/build.sh`), `tools/linux-ram/`. For the partition list see `02-HARDWARE.md` section 6.

> **Safety.** This document explains; it is not a procedure. The only write procedure is `docs/INSTALL-GUIDE.md`,
> and it runs only with the owner's OK, one write at a time. Nothing in the project has written to the tablet so far.

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
- **Keys:** Volume Down + Power from off enters ABL's fastboot. Power + Volume Up starts `recovery_<slot>` in Qualcomm's open ABL; not yet seen on this tablet (the dual-boot probe DB-P1 confirms it).
- **A reboot from Linux is a PS_HOLD hard reset** (DDR is re-initialised), so pstore / ramoops do not survive.
  Android's `/proc/bootloader_log` shows the reset reason afterwards.

**Fastboot facts** (`fastboot getvar`, read only): `product: canoe`, `secure: yes`, `unlocked: yes`,
`is-userspace: no` (ABL; Android's fastbootd is a different mode), `max-download-size: 805306368`. Larger images are
split by the PC's fastboot client into sparse pieces.

**Emergency download (EDL, Qualcomm 9008)** is not a recovery path for this tablet: no signed loader ("firehose") is
public. Fastboot in ABL is the floor. That is why the boot firmware is never written.

## 2. A/B slots and anti-rollback

- Every firmware and boot partition exists twice (`_a`, `_b`). ABL boots the **active** slot. Per slot it keeps
  `slot-successful`, `slot-retry-count` (6 read on this tablet on 2 Oct, Part A) and `slot-unbootable`.
- **How the flags move.** This is from Qualcomm's open ABL source (CodeLinaro edk2, read in the install workflow's
  round 6). OnePlus's build is closed: the write-2 probe C0 measures whether it behaves the same.
  - **Flashing a slot's boot partition resets that slot's flags.** In ABL's fastboot, `HandleRawImgFlash` calls
    `FastbootUpdateAttr("_b")`: *successful* and *unbootable* are cleared, *priority* and *retry count* are set to
    their maximum. The undo flash does the same. Only names starting with "boot" trigger this, on flash and on
    erase (`FastbootCmds.c`); a `recovery_b` flash leaves slot b's flags alone.
  - **Every normal boot of a slot that is not "successful" counts its retry count down by one.** Recovery,
    fastboot and charger boots do not count (`LinuxLoader.c` `IsABRetryCountUpdateRequired`,
    `PartitionTableUpdate.c` `FindBootableSlot`).
  - **At 0, `HandleActiveSlotUnbootable` marks the slot unbootable.** If the other slot is bootable and successful,
    ABL switches to it and resets. On this tablet slot a has no Android system, so the next boot fails there
    ("case B"). Otherwise ABL stops in its fastboot ("case A").
  - **Only Android marks a slot successful** (its boot-control HAL / update_verifier, which writes the flags into the
    boot partitions' GPT entries). U-Boot and Fedora never do; writing those GPT attributes from Linux would be a
    partition-table write, which the plan forbids.
  - **Consequence:** a permanent U-Boot in `boot_b` would run out after the maximum number of normal power-ons,
    unless OnePlus's ABL differs. C0 measures exactly that, with a hard stop at a retry count of 3 or less (guide Part C0.6). Part A on 2 Oct read slot b's retry count as 6 and slot a as successful but UNBOOTABLE, so today an exhausted slot b ends in ABL's fastboot (case A), not on slot a.
  - **The fallback** (not decided; the owner decides after C0): U-Boot in `recovery_b`. Recovery boots never count
    down, and writing it does not reset the slot. `adb reboot recovery`, LineageOS's "Restart to recovery" and
    `fastboot reboot recovery` reach it. Power + Volume Up would too in the open ABL, but that key is unverified on
    this tablet. Optionally, the boot-control block in `misc` ("boot-recovery") could
    make Fedora the default, which would be a third write (`misc` is on today's never-write list).
- The test tablet runs **LineageOS on slot b**. The LineageOS install on 28 Sep flashed its boot images to slot a,
  sideloaded the OTA to slot b and switched to it. Its `copy-partitions` step made both slots' firmware identical
  (11.A.38). Slot a's Android system was removed from `super` by that sideload.
- **Anti-rollback:** never flash or boot firmware older than 11.A.38. The factory slot b held 11.A.32 until
  `copy-partitions`. The project never switches slots (`set_active` appears only in the owner's return-to-stock
  script).

## 3. Verified boot (AVB) and the unlocked state

- The top-level `vbmeta_<slot>` describes or chains the other images. On this tablet `boot` is a **chained**
  partition: it carries its own small vbmeta in an AVB footer at the end of the partition.
- On a **locked** tablet any change stops the boot. On an **unlocked** tablet ABL shows the "orange" warning and
  continues after *verification* errors (a wrong hash, a key that does not match, a rollback index).
- ABL does not continue after *invalid metadata*, such as an image without the footer a chained partition needs.
- **Proven on the PC (2 Oct, install round 6, `AVB-PROOF: PASS`, 12 cases):** a libavb harness modelled on
  Qualcomm's public ABL source (`VerifiedBoot.c`).
  - A plain U-Boot image in `boot_b` gives `INVALID_METADATA`. ABL stops, marks slot b unbootable and switches slots.
  - The same image with an AVB hash footer (AOSP test key, today's rollback index) gives `PUBLIC_KEY_REJECTED`, and
    ABL continues. That is exactly how today's LineageOS boots: its vbmeta is signed with test keys that ABL's stored
    key does not match.
  - So the image written to `boot_b` **must carry the footer** (`07-INSTALL-REVIEW.md` R-1).
  - The proof ran on the LineageOS build's images. It is repeated on today's pulled images by `parta-check.sh`.
  - OnePlus's ABL build itself is closed. The write-2 probe (section 8) is its real test.
- **The footer also feeds the TEE.** ABL's `GetOsVerAndSecPactchLevel` hands the trusted environment the
  `os_version` **and** `security_patch` of the boot image's AVB footer, or the boot header's values when the footer
  has none. Round 6's first footer carried only `os_version`, so the TEE would have been given U-Boot's header values
  (16.0.0 / 2026-08) instead of LineageOS's (17 / 2026-09-01). Fixed: `mk-footer.sh` copies both from today's
  `boot_b` and refuses to work without both; `avb-proof.sh` has a check that the values handed to the TEE are equal.
- `fastboot boot` (a RAM boot) does not verify the **boot image** it is sent. It still verifies `dtbo`,
  `vendor_boot` and `init_boot` from the slot. That is why every test so far works without touching `vbmeta`, and
  why no RAM boot can prove how ABL treats a written `boot_b`.
- **Never relock** the boot loader while anything but verified stock is installed.

## 4. How the project boots Linux today: RAM boot, nothing written

```
PC: fastboot boot diag-L-efi.img        -> ABL loads it into RAM (no write, no verification)
    U-Boot (iceland-u-boot "diag L")    shows its text on ABL's framebuffer, waits in its OWN fastboot
                                         (USB product id 0xd00d, the same as ABL's, so drivers bind)
PC: fastboot boot linux-<kit>.img       -> U-Boot finds kernel, initramfs and device tree in the image
    bootefi                              starts the kernel's EFI stub (earlycon=efifb: output from the first line)
    Linux 7.3-rc4 + queue                our device tree; U-Boot applies ABL's memory map
    busybox shim (/init)                 USB NCM network 172.16.42.1, live kernel-log stream to the PC,
                                         watchdog, auto reboot, report pages; loads modules
    Fedora 44 root (in RAM)              fetched over USB or carried as a cpio; systemd as PID 1, GNOME
reboot                                   PS_HOLD reset -> ABL -> Android (slot b), untouched
```

Details:
- **U-Boot** (`iceland-u-boot`, v2026.10-rc5 + 14 infiniti + 3 Pad 4 patches).
  - It is packed as an Android boot image, header v4, with `kernel = gzip(u-boot.bin)`. U-Boot's own device tree sits
    inside the gzip stream; ABL drops a tree appended after it (diagnostic run 3, 28 Sep).
  - It is built **without fastboot flashing** (`CONFIG_FASTBOOT_FLASH` off), so it cannot write the storage.
  - Linux is started through EFI (`bootefi`). An earlier `bootm` path ran the kernel in place from an unaligned buffer
    and failed (Linux test 1).
- **The kit image.** `tools/linux-ram/build.sh` builds a header-v2 image: kernel `Image`, initramfs (busybox shim +
  optional Fedora root), and a debug device tree. That tree forces USB to peripheral mode; other nodes are switched
  on per kit with `ENABLE=`.
- **The runner** (`run-linux.ps1` / `relay-run-kit-early.ps1` on Windows) allows only these fastboot commands:
  `devices`, `getvar`, `boot`, `reboot` and `oem console`. On adb it allows only reading commands and
  `reboot bootloader`.
- **Ways back to Android.** The kit reboots by itself after `AUTOREBOOT_AT` seconds. A watchdog daemon runs, and an
  RTC alarm wakes a sleeping kit. Holding Power about 15 s always restarts into Android.

## 5. The planned install chain (Fedora installed; not done yet)

Design: `docs/INSTALL-PLAN.md` sections 0-3, `wf/install/REPORT.md` section 1.

```
ABL
 -> boot_b = the INSTALL build of U-Boot (u-boot-iceland.img)
      scsi scan; a GPT partition named "fedora" wins (dual boot), else "userdata"
      blkmap: map that partition as a disk with the UFS's 4096-byte blocks (read through U-Boot, no copy)
      one explicit boot option Boot0001 = blkmap partition 1, /EFI/fedora/shimaa64.efi (efidebug, RAM only)
      bootefi bootmgr  (EFI variables are kept in RAM only: nothing is stored; no vendor LUN is tried)
      if nothing boots: U-Boot's fastboot; 600 s without a PC command -> power off (U-Boot patch 0007)
      (boot_b vs recovery_b as the permanent place: an open owner decision pending C0, see section 2)
 -> shim  (EFI/fedora/shimaa64.efi on the image's EFI System Partition; shim's fallback is not used)
 -> GRUB 2.12  (Fedora's; reads the BLS entries in /boot/loader/entries)
 -> kernel-iceland (our rpm) + its device tree
      (U-Boot loads <ESP>/dtb/qcom/kaanapali-oneplus-iceland.dtb and applies ABL's memory map; with the
       per-kernel option GRUB loads /boot/dtb-<version>/... and hands it through U-Boot's EFI DT fixup protocol)
 -> dracut initramfs with the module "90iceland":
      sets every UFS block device read-only except userdata (and its LUN as a whole),
      attaches a partitioned loop device over userdata (direct I/O, 4 KiB blocks) -> loop0p1..p3;
      carries the GPU microcode and the SoCCP / ADSP / CDSP stack with the tablet's DSP firmware (since R1c: the charger
      co-processor and USB-C must be up before the root is used); Wi-Fi, BT and video stay out (omit_drivers) and load
      after switch_root when /lib/firmware is reachable
 -> Fedora root: btrfs subvolume "root" on loop0p3, /boot (ext4) loop0p2, ESP (FAT32) loop0p1; SELinux enforcing
 -> first boot: systemd-repart grows the root partition to the whole userdata, growfs grows btrfs
```

Why the disk image looks like this (install REPORT findings 1, 2):
- **Every UFS LUN has 4096-byte logical blocks.** The official `Fedora-Workstation-Disk-44` aarch64 image is laid out
  for 512-byte sectors: a DOS partition table and a FAT16 ESP with 512-byte sectors.
  - U-Boot's blkmap takes the target's 4 KiB block size and refuses that FAT ("FAT sector size mismatch").
  - Linux reads the table in 4 KiB units.
  - Written as it is, the image would not boot.
- **The image builder (`mk-golden.py`)** re-lays it: a GPT in 4 KiB units with the standard partition types, the ESP
  rebuilt as FAT32 with 4096-byte sectors (the same 419 files, compared by hash), `/boot` and the btrfs root copied
  unchanged.
- **The GPT also lets the root grow:** systemd-repart works only on GPT. On the original layout the root would have
  stayed at 10.3 GB.
- **The written file is an Android sparse image** whose unpacked size equals `userdata` exactly (237,159,641,088
  bytes). Only about 12.8 GB of it is data.

**`efisp` vs our ESP.** The tablet's `efisp` partition (3 MiB, firmware side) is not used. Our ESP lives inside the
Fedora disk in `userdata` (see `02-HARDWARE.md` section 6).

**Seat belts inside the installed system** (INSTALL-PLAN section 2):
- the read-only udev rule for every other UFS partition (also in the initramfs);
- U-Boot's EFI layer may write only blkmap disks (U-Boot patch 0005);
- no FAT / ext4 / GPT writer linked into U-Boot;
- EFI variables are not stored;
- fwupd's plug-ins that could write boot code, EFI variables or the UFS device firmware are switched off (17
  plug-ins);
- dnf never installs Fedora's kernels, a rescue initramfs, akmods / dkms, bootupd, sdubby or U-Boot images;
- GRUB, shim and firmware packages are held; Fedora is pinned to release 44 until the next release is rehearsed.

**Updates after the install** (INSTALL-PLAN section 6):
- New kernels come only from our repository. Each is RAM-tested first and synced to the tablet's local repository
  (`iceland-repo-sync`).
- A new kernel boots once as a trial (GRUB `next_entry`). It becomes the default only after the desktop has been up
  for 30 s.
- A btrfs snapshot of the root is taken before every dnf transaction (three kept), each with a "Roll back to ..." boot
  entry.

## 6. The rehearsal from RAM (the install's proof without writing)

```
PC: fastboot boot u-boot-iceland-rehearsal.img   (the install build's code WITHOUT SCSI / UFS support,
                                                    bootcmd = fastboot loop; it cannot see the storage)
PC: fastboot boot head.boot.img                   ("iceland-head": gzip of the image's ESP + /boot with a
                                                    small GPT) -> unzip into RAM, blkmap of RAM, bootefi bootmgr
 -> shim -> GRUB -> kernel-iceland               (the same chain as installed)
 -> initramfs: every UFS device read-only FIRST; USB gadget up; root disk = NBD from the PC over USB
               (PC: golden image + copy-on-write overlay; a relay admits only 172.16.42.1)
 -> Fedora as installed; the acceptance list runs; a guard returns the tablet to Android on any stall
```

- **What it proves:** the image, GRUB on a 4 KiB disk, shim's fallback under U-Boot, our kernel and initramfs,
  SELinux, the first-boot growth, the acceptance list, and the update / rollback mechanics.
- **What it cannot prove:**
  - ABL's verified-boot check of a written `boot_b`;
  - the install U-Boot's UFS path (SCSI scan, the `userdata` map);
  - GRUB's environment write through U-Boot into the real UFS (the "boot once" mechanism);
  - the loop-over-userdata carrier on the real partition.
  The plan sees these first after write 1, in the tethered boots. `07-INSTALL-REVIEW.md` R-3 / R-4 propose seeing
  some of them earlier.
- **State on 2 Oct, 22:30.**
  - Rehearsal tooling built and checked on the PC (selfcheck clean, check-all 14 PASS).
  - The B run (the image built on the tablet over the network disk) passed in area-combo-93, and again with device
    package 0.18 in area-combo-94. Run 94's image still lacks three round-6 fixes (B1 omit_drivers, B2 no SELinux
    load into the kit, B4 GPU microcode), so the B run is repeated before R1.
  - The R1 U-Boot fix (blkmap `create` takes 3 words; every failure prints a FAILED line and returns to fastboot) is
    verified 15 / 15 in an independent U-Boot sandbox (`wf/r1debug/REPORT.md`).
  - The first tablet step is an 8 KiB "not gzip" test head. It proves the return to fastboot and the PC's recovery
    within seconds.
  - The exact command list is `docs/INSTALL-RERUN-COMMANDS.md`. The first rehearsal boot R1 stopped in the rehearsal U-Boot: its
  `blkmap create` subcommand table still accepted only 2 words. Fixed in round 5: every failure now returns to
  fastboot or resets, and never stops at a prompt. Re-run pending.

## 7. Why the install stays unbrickable and restorable (INSTALL-PLAN section 11)

**Unbrickable**
1. Only two partitions are ever written: `userdata` and one boot partition of the active slot (`boot_b`, or
   `recovery_b` as the alternative). XBL, ABL, all firmware, the per-device data (`persist`, `cdt`, `ddr`,
   `oplusreserve*`, ...), the security state (`devinfo`, `keystore`, `frp`, ...), Android's `super`, `vbmeta*`,
   `vendor_boot*`, `dtbo*` and every partition table stay untouched. So ABL's fastboot always answers to Volume
   Down + Power.
2. Never `set_active`, never lock the boot loader, never older firmware, never a storage-firmware update (fwupd
   plug-ins off).
3. Inside Fedora the other partitions are read-only from the first second (initramfs), and U-Boot cannot write them.
4. Do not let the battery run flat: UPower powers off at the critical level, the guard keeps its shutdown
   temperatures, and the charge limit keeps the cell between 80 and 85 % on a charger.

**Restorable**, from the smallest step to the largest:

| Level | Brings back | Needs the PC | Loses |
|---|---|---|---|
| L0 trial boot | a new kernel that never reached the desktop is skipped on the next start | no | nothing |
| L1 previous kernel | GRUB's menu (3 s, volume keys): one of three kept kernels | no | nothing |
| L2 snapshot | "Roll back to ..." entry: the root before the last update | no | system changes since then |
| L2b day-0 snapshot (suggested) | the root as installed | no | system changes since the install |
| L3 rescue kit | `fastboot boot` of the RAM kit: mount, check, roll back, replace the kernel | yes | nothing |
| L4 the recorded image | write the rehearsed sparse image again (a write, owner's OK) | yes | everything in Fedora unless `/home` was copied |
| L5 stock | the owner's return-to-stock script: the stock boot set on both slots, `super` from the backup, `userdata` / `metadata` erased; never firmware | yes | Fedora |

"Back to LineageOS" is not written down yet (`07-INSTALL-REVIEW.md` R-5). The return-to-stock script has been
written and dry-run, never executed.

**Permanent**
- One source for the kernel (RAM-tested, then a trial boot).
- Boot code and firmware never update by themselves.
- Every Fedora version upgrade and every new U-Boot goes through the network-disk rehearsal first.
- The stock-values audit runs after every queue change.

## 8. The two writes, in one paragraph each (for orientation only)

- **Write 1:** the rehearsed sparse image into `userdata`, from ABL's fastboot. It erases Android's data. Until
  write 2, a plain power-on still starts Android, which reports damaged data: never confirm its factory reset.
  Undo: write it again, or return to stock.
- **Write 2:** the install U-Boot into `boot_b` (or `recovery_b`, if C0 shows that ABL counts down boots of
  `boot_b`: an open owner decision). A plain power-on then starts Fedora (with `recovery_b`: Power + Volume Up). Undo: write back the `boot_b`
  image saved from the tablet in Part A of the guide. **Not** the backup's `boot_b`: the backup predates LineageOS.

Both are described with their checks in `docs/INSTALL-GUIDE.md`. Both run only with the owner's OK. See the review
before either.

**Order decided on 2 Oct.** The owner accepted the review's proposal (R-3): a **write-2 probe first** (guide part
"C0", text being written by the install workflow). **The owner runs every write themselves.**
1. **Part A read.** `parta-read.ps1` pulls today's `boot_b`, `vbmeta_b`, slot flags and `misc` read-only (needs
   "Rooted debugging").
   - `parta-check.sh` makes `boot_b-before-install.img` (the undo file) and the footered
     `u-boot-iceland-footered.img`.
   - It reruns the AVB proof on today's images.
   - It stops if `misc` holds `boot-recovery` / `boot-fastboot`.
   - Its last line is `PARTA: READY FOR C0`.
2. **C0.** In ABL's fastboot the owner writes the footered install U-Boot into `boot_b`, then reads the slot flags
   before any reboot.
   - Expected right after the flash (from the open ABL source, section 2): b **not** successful, not unbootable,
     retry count at its maximum, current slot b.
   - Each power-on shows ABL's orange warning, then U-Boot. U-Boot maps Android's encrypted `userdata`, finds no
     Fedora, waits in fastboot, and powers off after 10 minutes.
   - Three untethered cold boots, each followed by a read of the slot flags in ABL. The retry count is expected to
     go down by one per normal boot. **Hard stop at a retry count of 2 or less:** undo at once.
   - If the count does not move, OnePlus's ABL differs from the open source and `boot_b` can stay. If it counts down,
     the permanent place becomes `recovery_b` (owner's decision).
3. **Undo.** The owner writes `boot_b-before-install.img` back. The flash resets slot b's flags again; LineageOS
   boots and marks the slot successful itself. LineageOS returns **with its data**. If `current-slot` reads `a`,
   nothing else is written; ask first.
4. **Then** write 1 and write 2 again **in the same ABL session**, with no Android boot between them (Android would
   set `boot-recovery` in `misc` when it cannot mount `userdata`).

**Dual boot:** not now (owner, 2 Oct). A plan with the best safety precautions is to be written
(`wf/install/DUALBOOT-PLAN.md`, not started).
