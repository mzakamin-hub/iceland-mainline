# Dual boot: BlissROM + Fedora on the OnePlus Pad 4

At power-on, U-Boot shows a menu: **Fedora / BlissROM / Boot loader (fastboot)**. Volume Up / Down move, Power selects,
and after 5 s Fedora starts. Both systems live on slot b. Fedora runs from its own `fedora` partition, and BlissROM keeps
its encrypted data in a smaller `userdata`. Tested with BlissROM v20.1 (iceland, OFFICIAL, GApps, build 20261016),
Fedora 44 and the U-Boot install build v7.

This guide starts from the Fedora install of [INSTALL-GUIDE.md](INSTALL-GUIDE.md): U-Boot in `boot_b`, Fedora as a disk
image in `userdata`, an unlocked bootloader. Every step below writes to the tablet and erases Android's data. Do it only
after the backups of [Backups first](#backups-first), and keep them off the tablet. The U-Boot side (the menu, the gate,
how BlissROM is started, building and writing v7) is described in
[iceland-u-boot/docs/DUAL-BOOT.md](https://github.com/mzakamin-hub/iceland-u-boot/blob/main/docs/DUAL-BOOT.md).

Run one write at a time: check the command, the partition, the file and its sha256 before you type it, and the step's
check after it, before the next one.

## How it works

- **Partitions (LUN 0).** The Fedora disk image stays where its bytes are now (the first part of the old `userdata`),
  behind a new GPT entry `fedora`. `userdata` keeps its name, type, unique GUID and attributes but starts later and is
  smaller. The last 1 MiB of LUN 0 stays outside every partition: ABL writes a few bytes near the end of LUN 0 when it
  updates the slot flags, and they must not land in Android's data. Fedora is not copied: one table change does the
  split.
- **Start.** ABL starts `boot_b`, which holds U-Boot. ABL treats that image as an Android boot image, so before it jumps
  to U-Boot it has already loaded the slot's `vendor_boot_b` and `init_boot_b` ramdisks with their bootconfig, built the
  device tree from `vendor_boot_b` + `dtbo_b`, and set the verified-boot state. The BlissROM entry
  (`qcom_android_chain scsi boot_a`, [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot) patch 0015)
  loads the kernel of BlissROM's `boot.img` from `boot_a` and boots it with exactly that ramdisk and device tree.
  Android sees a normal start of slot b. The Fedora entry starts Fedora from the `fedora` partition.
- **Why not `recovery_b` or `boot_b`.** BlissROM's `boot.img` must never go into `boot_b`: it would replace U-Boot.
  The OnePlus ABL starts `recovery_b` only when the image there has no kernel, and then with `boot_b`'s kernel (that is,
  U-Boot), so a kernel in `recovery_b` cannot start Android. `boot_a`, on the unused slot a, holds the kernel instead.
- **The gate.** U-Boot shows the BlissROM entry only when it is safe: a `fedora` partition sits next to `userdata` on
  the same LUN without overlap, `userdata` does not start with the Fedora disk (no GPT header, no btrfs superblock),
  and `boot_a` holds an Android boot image with an arm64 kernel. Before the split, the menu shows Fedora / Boot loader
  only.
- **Slots.** Everything stays on slot b. In BlissROM, Android's boot control marks slot b good after a start. In Fedora,
  `iceland-slot-mark` (iceland-device 0.28-24 or newer) marks it, with a check that nothing outside the partition
  tables changed. Slot a is not a working slot (it has no system in `super`); never make it active.

## What you need

| Item | Where |
|---|---|
| The Fedora install with iceland-device **0.28-25 or newer** (0.28-24: storage rule, `fedora` writable and `userdata` read-only once `fedora` exists, guarded slot marking; 0.28-25: the initramfs picks the `fedora` partition even when udev names `userdata` first). With 0.28-24, set `iceland.carrier=fedora` as in step W2b until 0.28-25 is installed | [INSTALL-GUIDE.md](INSTALL-GUIDE.md), [packaging/iceland-device/](../packaging/iceland-device/) (`build-rpm.sh`) |
| U-Boot install build **v7** (0001-0015), plain image for a RAM test and AVB-footered for `boot_b` | [iceland-u-boot](https://github.com/mzakamin-hub/iceland-u-boot): `scripts/prepare.sh` + `scripts/build.sh`; footer as for v4 ([README-INSTALLER.md](../tools/installer/README-INSTALLER.md)) |
| BlissROM v20.1 for `iceland` (the OTA zip) and a `payload.bin` extractor | BlissROM's download page |
| The tools of [tools/dualboot/](../tools/dualboot/) | this repository |
| A Linux system running in RAM (`fastboot boot` of a kernel + initramfs with `dd`, `cmp`, `sha256sum`, `blockdev`), in which no partition of LUN 0 is mounted | for step W3 only |
| `fastboot` on the PC, a good USB cable, battery above 60 % | |

The images extracted from the BlissROM v20.1 OTA that were tested (sha256):

| Image | sha256 | Goes to |
|---|---|---|
| `boot.img` | `0aea33037cc37e9433c2b32d498e3eb6f78da87b6f479d6780c53a9e630f3447` | `boot_a` (the kernel only) |
| `vendor_boot.img` | `12336079bdca50d0359cad625b568a0203fd20ba00b0c303d072ead4fb78532a` | `vendor_boot_b` |
| `init_boot.img` | `7263096465f109c3ae933a0618092797f85e8120aab8a7f786d8ec1faccc3568` | `init_boot_b` |
| `dtbo.img` | `6ff58abc30a005c173b349cd4ddf01b0130e06f682328ab23f0c4df257a764ac` | `dtbo_b` |
| `vbmeta.img` | `fc0f32556b41aa5b35a752c4b3ad76fff117d04ffe9562178e434125ccab16f8` | `vbmeta_b` |
| `vbmeta_system.img` | `c32ee9365d1c59aaa9e67a94a1060de6d24b6673f87b29b4af9262239bd7b8b3` | `vbmeta_system_b` |
| `vbmeta_vendor.img` | `370aebb66e094304a4b3ecdba9dadd537e14d43954c8b254aa2a52c6ca79658c` | `vbmeta_vendor_b` |
| `system.img` | `8b437ff1dd9f944153dab8dd45e1de3cfbb394f0a61dd068a7309bbee111e1b7` | `super` (slot b) |
| `system_ext.img` | `fdbbe450e1d776e33b2c216568c9e045a5d93fa496b7426a1b6a65fb30b958c0` | `super` |
| `product.img` | `e6736cce3bfe111773ec16b7810f0801f64678dc7c154ba57e852d8747fbc433` | `super` |
| `odm.img` | `8616ae88a30d7e703a2ffd1372f7068416fcd6b67f56c0df0549a2a640093bc2` | `super` |
| `vendor.img` | `e1f66f0d58e629eb5911a576dae6cacc274b40b5d9d0c404753224765cb2bb62` | `super` |
| `system_dlkm.img` | `6710d58a8b29ababaef64926892c01188d943164e26b4bbb97c25a583f04403b` | `super` |
| `vendor_dlkm.img` | `796778ddfa1182f49179a272dc8286e6fbe9819b244189d57e641fa70b35b9d7` | `super` |

The OTA's firmware images are not flashed: the tested tablet already ran a matching firmware set. `recovery_b` is not
used and is left as it is.

## Backups first

Nothing below is safe without these, and each step's undo uses them.

1. **The full backup** of [INSTALL-GUIDE.md](INSTALL-GUIDE.md) step 1 (every partition except `userdata`), still on
   the PC with its sums checked.
2. **The dual-boot backup**, read only, on the installed Fedora:
   `sudo bash tools/dualboot/dualboot-backup.sh` (default output `/var/tmp/dualboot-backup-<date-time>`). It reads the
   partition tables of every UFS LUN (first and last 1 MiB, and LUN 0's first 6 / last 5 blocks), Fedora's own table
   (the loop disk's first 6 / last 5 blocks), the small Android partitions of both slots (`boot`, `recovery`,
   `vendor_boot`, `init_boot`, `dtbo`, the three `vbmeta`, plus `misc` and `metadata`), the first and last 1 MiB of
   `super`, the slot flags, and compares the firmware partitions with BlissROM v20.1's firmware images
   (`firmware-compare.txt`). It never opens a device for writing. Copy the folder to the PC and run
   `sha256sum -c SHA256SUMS` there.
3. Your own files in Fedora: the steps keep Fedora's data in place, but a copy elsewhere costs little.

The dual-boot backup holds your tablet's partition GUIDs and tables: keep it private, never in a repository.
If `firmware-compare.txt` lists `DIFF` for firmware partitions, your firmware is not the tested set; this guide does
not cover flashing firmware.

## Sizes (the tested split, a 256 GB tablet)

These are the numbers of the tested tablet (256 GB storage): LUN 0 has 61,853,696 blocks of 4096 bytes, and the old
`userdata` ran from block 3,953,388 to 61,853,690. Another storage size gives other numbers: compute the plans with
`gpt-plan.py` from your own backup and change the constants in `dualboot-w2.sh` and `w3-gpt.sh` (they refuse a disk
of another size).

| Partition | First block | Last block | Size |
|---|---|---|---|
| `fedora` (new entry) | 3,953,388 | 36,683,775 | 124.86 GiB |
| `userdata` (BlissROM) | 36,683,776 (16 MiB aligned) | 61,853,434 | 96.01 GiB |
| unpartitioned | 61,853,435 | 61,853,690 | 1 MiB |

Inside `fedora`, Fedora's own disk shrinks to 32,730,388 blocks, its root partition (p3) ends at block 32,730,382, and
its btrfs is first shrunk to 120 GiB.

## Steps

Each step keeps Fedora working. The scripts refuse (and write nothing) when the tablet is not in the state the step
expects, and each write has an undo. `HEAD` / `TAIL` are the table copies of the dual-boot backup: `fedora/inner-head6.bin`
/ `fedora/inner-tail5.bin` for W2, `gpt/sda-head6.bin` / `gpt/sda-tail5.bin` for W3. `gpt-plan.py` runs on the PC and
writes `plan/`; copy `plan/` next to the script that uses it. Battery above 60 % for every write.

| Step | Where | What | Check | Undo |
|---|---|---|---|---|
| B | Fedora, PC | [Backups first](#backups-first) | `sha256sum -c SHA256SUMS` on the PC | - |
| W0a | Fedora | iceland-device 0.28-25 or newer installed; `qbootctl.service` stays disabled | the package's `--check` rows pass | the previous package again (`sudo rpm -Uvh --oldpackage ...`) |
| W0b | Fedora | `sudo systemctl mask systemd-repart.service` (repart would grow Fedora's disk back over the new end) | `systemctl is-enabled systemd-repart` = masked | `sudo systemctl unmask systemd-repart.service` |
| W1 | Fedora | `sudo btrfs filesystem resize 120g /`, then `sudo btrfs scrub start -B /` | scrub: no errors | `sudo btrfs filesystem resize max /` |
| W2 | Fedora | Fedora's own partition table for the smaller disk: `gpt-plan.py shrink HEAD TAIL 57900303 32730388 plan/ --trust-primary`, then `sudo bash dualboot-w2.sh --dry-run` and `--write --confirm CODE` (CODE printed by the dry run) | two reboots: Fedora starts normally; `sfdisk -d` on the loop disk shows p3 ending at 32,730,382 | `sudo bash dualboot-w2.sh --restore --confirm CODE` |
| W2b | Fedora | **only with iceland-device 0.28-24** (not needed with 0.28-25), right before W3: `sudo grub2-editenv - list`; if there is no `iceland_args` line, `sudo grub2-editenv - set iceland_args=iceland.carrier=fedora` (otherwise add ` iceland.carrier=fedora` to its value) | `grub2-editenv - list` shows it | `sudo grub2-editenv - unset iceland_args` (or the old value). If W3 is not done or is undone, Fedora would wait for a `fedora` partition: at the GRUB menu press `e`, remove `$iceland_args` from the `linux` line for that start, then unset it |
| W3 | Linux in RAM | LUN 0's table: `gpt-plan.py split HEAD TAIL 61853696 36683776 plan/ --userdata-last 61853434`, then `w3-gpt.sh --dry-run`, `--write --confirm CODE` | `RESULT PASS`; in ABL, `fastboot getvar partition-size:userdata` = `0x1800EFB000`, `partition-size:fedora` = `0x1F36D14000`; U-Boot prints "booting Fedora from the fedora partition" and Fedora starts | `w3-gpt.sh --restore --confirm CODE` (from the same RAM system) |
| W5b | ABL fastboot | `fastboot flash vendor_boot_b vendor_boot.img`, then the same for `init_boot_b`, `dtbo_b`, `vbmeta_system_b`, `vbmeta_vendor_b`, `vbmeta_b` | slot b flags unchanged; U-Boot + Fedora still start | flash the backup's `parts/<name>.img` back |
| W5k | ABL fastboot | `fastboot flash boot_a boot.img` (BlissROM's) | slot b stays current | flash the backup's `parts/boot_a.img` back |
| W5c | PC, then ABL fastboot | `mk-super.py SUPER_HEAD IMG_DIR super-bliss.img` (SUPER_HEAD = the backup's `parts/super-head1M.bin`, IMG_DIR = the seven raw system images), `check-super.py super-bliss.img IMG_DIR`, then `fastboot flash super super-bliss.img` | `SUPER-CHECK: 0 failure(s)`; all chunks OKAY | none needed for Fedora (it does not use `super`) |
| W4 | ABL fastboot | `fastboot erase userdata`, then `fastboot erase metadata`: only after W3's sizes are confirmed | both OKAY | none (Android's data; Fedora is outside this range) |
| M | ABL fastboot | RAM test, writes nothing: `fastboot boot u-boot-iceland-v7.img` (plain image), choose BlissROM | BlissROM starts its setup | - |
| W6 | ABL fastboot | `fastboot flash boot_b u-boot-iceland-v7-footered.img` (U-Boot updated in place) | power-on menu Fedora / BlissROM / Boot loader; both systems start | flash the backup's `parts/boot_b.img` back |
| A | ABL fastboot | after one start of each system: power on with Volume Down held, then `fastboot getvar current-slot` and `fastboot getvar slot-successful:b` (reads only) | `b`, `yes` | - |

The tested v7 images (sha256): plain `58414017ec3e2b496905b078d2bd1db8ca9bea9a171bdaf44797dcf0671eb784`, footered for
`boot_b` (AOSP test key, the footer values of the iceland-u-boot v4 release)
`8ef94a08d7eabac35c8bc97173fa818f13c2d1e53ff14375bcf1207c614f68a3`. A local build has a different hash (U-Boot embeds
its build time) and a footer must match the tablet's `boot_b` values.

The `super` image keeps the tablet's LP geometry and block device and holds BlissROM's seven partitions for slot b
only (read-only, 1 MiB aligned), with the Virtual A/B flag as on stock; ABL writes it in one go, so no fastbootd is
needed. On the first BlissROM start Android creates new encryption keys in `metadata` and formats `userdata`.

## Keep in mind

- **Turn off BlissROM's automatic updates, and install no update from its Updater.** The updater installs into slot a
  and switches to it, which skips U-Boot. A BlissROM update is the same set of writes with the new images (W5b, W5k,
  W5c; never W4, which erases BlissROM's data), after a new dual-boot backup. It has not been run on the tested
  tablet yet: back up BlissROM's own data first.
- **Never** flash a BlissROM image into `boot_b`, and never use Settings > "Erase all data" in BlissROM (it writes a
  wipe command into `misc` that the menu does not handle).
- **Reboot to the boot loader from Fedora lands in Fedora**: ABL ignores Linux's `systemctl reboot bootloader`
  (unsolved). To reach ABL's fastboot, hold Volume Down at power-on, or choose
  "Boot loader (fastboot)" in the menu.
- Writing `boot_a` resets slot a's flags in ABL, so slot a counts as bootable again although it has no system. Slot b
  stays the active slot; never `fastboot set_active a`. Let each start finish (Fedora's desktop, or BlissROM's home
  screen), so that slot b is marked good and keeps its tries.
- If the tablet ever stops in ABL's fastboot instead of the menu (slot b out of tries), start the plain U-Boot from
  RAM, `fastboot boot u-boot-iceland-v7.img`, and choose a system: a good start marks slot b again.
- `w3-gpt.sh` and `dualboot-w2.sh` each have a `--restore` mode that writes the saved table back: the undo of that
  one write, right after it.
