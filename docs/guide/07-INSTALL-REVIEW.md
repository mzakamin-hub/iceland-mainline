# 07 - Install review: the risks and how the design handles them

This chapter is an independent review of the install (`docs/INSTALL-PLAN.md`, `docs/INSTALL-GUIDE.md`): what could go
wrong when Fedora is written to the tablet, what the design does about it, and what is still open. It is meant for
anyone who wants to follow the install or adapt it.

## 1. Verdict in short

The write surface is two partitions (`userdata` and the active slot's `boot` partition), and every write has an undo.
The boot firmware, ABL and its fastboot are never written, so Volume Down + Power always reaches a fastboot that can put
everything back. The image is tested from RAM before it is written, with a test chain that cannot touch the storage.
None of the points below is a brick risk on its own; the high ones can end in "only the full return to stock helps",
which is why each has a safeguard.

## 2. The findings and their safeguards

Severity: **High** = can stop the install or force the full return to stock; **Medium** = a wrong or missing
instruction, or an unattended failure mode; **Low** = small points.

### R-1 (High) - `boot_b` needs an AVB footer

- **Risk.** `vbmeta_b` chains `boot`, so ABL verifies whatever is in `boot_b` with Android's verified-boot code
  (libavb). A plain U-Boot image has no footer; libavb then reads the boot header as vbmeta and returns
  "invalid metadata". Qualcomm's open ABL continues on an unlocked device only after "verification", "rollback index"
  or "public key rejected" results; on invalid metadata it stops or marks the slot unbootable.
- **Safeguard.** The image written to `boot_b` carries an AVB hash footer signed with the key `vbmeta_b` chains `boot`
  with, with the current rollback index, OS version and security patch level (ABL hands the last two to the secure
  world). ABL then reports "public key rejected", as for any custom boot image on an unlocked tablet, and continues in
  the orange state. Check it on the PC before the write by running `avb_slot_verify()` on the pulled `vbmeta_b` and the
  candidate image: the result must be one that continues, never `ERROR_INVALID_METADATA` or `ERROR_IO`.
- **State.** Proven on the PC and on the tablet: ABL starts the footered U-Boot from `boot_b`.
- `fastboot boot` (a RAM boot) does not verify the boot image it is sent, so no RAM test can show this; only a write can.

### R-2 (High) - the undo file of the `boot_b` write must come from today's system

- **Risk.** A backup taken before a custom ROM was installed holds another `boot_b` (another header, key and rollback
  index). Writing it back as the "undo" gives an Android slot that does not boot.
- **Safeguard.** Save `boot_b` from the system that runs on the day (read only, with `adb root`), and make the footer
  from that same file. Compare the two headers before the write.

### R-3 (High) - the order of the writes, and the slot counter

- **Risk.** Write 1 (`userdata`) ends Android's data. If write 2 (`boot_b`) then fails, the tablet is between two
  systems. Flashing `boot_b` also resets slot b: *successful* is cleared and the retry count set to its maximum, and
  each normal power-on of a slot that is not successful uses one try; at zero ABL marks the slot unbootable.
- **Safeguard.**
  - Boot Fedora tethered after write 1 (`fastboot boot` of the plain install build) before write 2, so write 2 is made
    only for an image that is known to start.
  - Fedora marks the slot successful after a good boot (`iceland-slot-mark`, `qbootctl -m`, from `iceland-device`
    0.28-8 on).
  - The install build of U-Boot never resets by itself: an early build that reset itself used up all tries of the slot
    in one power-on.
- **Measured on the tablet:** a normal boot into U-Boot from `boot_b` uses one try; `fastboot reboot-bootloader` from
  U-Boot uses none. Entering ABL's fastboot with the keys and charger starts do not count.
- **Optional probe for a new starting state.** Before write 1, the footered U-Boot can be written into `boot_b` while
  Android's data is still intact, booted, and undone the same day with the saved `boot_b`. This shows ABL's verified-boot
  result and the slot counter on your tablet before anything is lost. Hard stop at a retry count of 3 or less.

### R-4 (High) - the rehearsal build is not the install build

- **Risk.** The image is tested with a rehearsal build of U-Boot that has no SCSI / UFS support (so the test cannot
  touch the storage). The install build's own storage path is therefore not covered by those tests. Writing the
  rehearsal build into `boot_b` by mistake would give a U-Boot that only waits for fastboot.
- **Safeguard.** Check the file's header and environment before the write (the install build carries the UFS lines);
  RAM-boot the exact install build once before write 1: on an Android tablet it maps the encrypted `userdata`, finds no
  Fedora and waits in its fastboot, reading only.

### R-5 (High) - no dual boot, no way back to LineageOS

- **Risk.** Write 1 replaces all of `userdata`: Android keeps its system partitions but loses its data and no longer
  starts. Dual boot would need the partition table of unit sda changed, which the design never writes.
- **State.** The install is Fedora-only. The way back is the return to stock OxygenOS 11.A.38 (section 8 of the guide);
  a way back to LineageOS is not written down.

### R-6 (Medium) - an unattended U-Boot that finds no Fedora

- **Risk.** If Fedora cannot be found (a damaged EFI partition, a bad GRUB update), U-Boot waits in its fastboot with
  the screen on. Unattended, that drains the battery; a flat battery is the most common "looks bricked" state. GRUB's own
  `grub>` prompt behaves the same way.
- **State.** The install build never resets or powers off by itself (a reset would be another try of the slot); it
  holds in a fastboot loop and shows its boot menu at power-on. Recovery is Volume Down + Power and a RAM rescue boot.
  Keep the tablet charged.

### R-7 (Medium) - the boot order over the vendor LUNs

- **Risk.** Without stored EFI variables, U-Boot's boot manager tries the default path `\EFI\BOOT\BOOTAA64.EFI` on every
  UFS unit before the Fedora disk, which makes the boot depend on vendor partitions (the firmware's `efisp`, 3 MiB) and
  runs U-Boot's parsers over about 150 vendor partitions.
- **Safeguard.** The install environment creates one explicit boot option for `\EFI\fedora\shimaa64.efi` on the Fedora
  disk before `bootefi bootmgr`. It also avoids shim's fallback path, which would loop when its boot entry is lost at
  every reset (EFI variables are not stored).

### R-8 (Medium) - the image size

- The sparse image's unpacked size must **equal** `userdata` (the root grows into the whole partition at the first boot).
  Read `fastboot getvar partition-size:userdata` and compare before write 1. The PC's fastboot client splits the image
  into pieces of at most ABL's `max-download-size` (805,306,368 bytes).

### R-9 (Medium) - Android's boot command in `misc`

- **Risk.** An Android boot that cannot use its data (between write 1 and write 2) can leave `boot-recovery` in `misc`.
  ABL then starts recovery instead of `boot_b`.
- **Safeguard.** Check `misc` before the writes; keep the time between the writes short and do not let Android boot in
  between. If LineageOS recovery appears after write 2, choose "Reboot system now" (it clears the command), never
  "Factory data reset". `bootonce-bootloader`, which Android writes at `adb reboot bootloader`, is ignored by ABL.

### R-10 (Medium) - how the device tree reaches Linux

- Two paths exist: U-Boot loads the EFI partition's copy of the device tree and applies ABL's memory map, or GRUB loads
  the per-kernel tree and hands it through U-Boot's EFI device-tree fix-up protocol. Whichever is used, Linux must see
  ABL's real memory map (`/proc/device-tree/memory*`): never boot a device tree without it. See
  `03-BOOT-AND-PARTITIONS.md` section 5.

### R-11 (Medium) - firmware timing in the initramfs

- **Risk.** The DSP remoteproc driver loads from the initramfs before the root (with the tablet's firmware) is mounted,
  and its auto-boot does not retry: the ADSP and CDSP would stay off, and with them sound and the sensors.
- **Safeguard.** The initramfs carries the SoCCP / ADSP / CDSP stack with the tablet's DSP firmware, so the charger
  co-processor and USB-C are up early; Wi-Fi, Bluetooth and video are left out of the initramfs and load from the root.
  "ADSP and CDSP running, no failed firmware request" and "battery guard active with live battery data" are acceptance
  checks of the image.

### R-12 (Low) - smaller points

- The return to stock has been written and dry-run, never executed. Its `super` restore is a 14.6 GB raw image sent
  through ABL's fastboot; a dry run proves the inputs, not the flash. It leaves the tablet on slot a.
- `adb root` on LineageOS needs a userdebug build and "Rooted debugging" in the developer options.
- The boot header OS version and patch level of the U-Boot image, and the footer's values, must match the slot's
  current `boot` image (anti-rollback).

### N-1 (High) - guards written for the test layout

- **What happened.** The installed root is a loop device over `userdata`, and the boot LUN is read-only to the running
  system. The slot-marking service's guard had been written for the RAM-test layout and refused the installed one, so
  the slot was not marked and the retry count went down at every power-on.
- **Fix.** `iceland-device` 0.28-8 accepts a loop root backed by `userdata` and makes the boot LUN writable for the one
  `qbootctl -m` call only, logging both.
- **Lesson.** Every guard in the installed path needs a check on the real layout, not only on the test layout. After an
  install, confirm the marking (`journalctl -u iceland-slot-mark`, `qbootctl`) before switching the tablet on and off
  repeatedly.

## 3. What the design does well

- **Two partitions,** and a "never written" list that is complete against the 151-partition layout, including the UFS
  device firmware (the `fwupd` plug-ins are switched off).
- **Defence in depth inside Fedora:** the read-only rule for the other partitions is already in the initramfs; EFI
  programs can write only blkmap disks (U-Boot patch 0005); no FAT / ext4 / GPT writer is linked into U-Boot; EFI
  variables are not stored; dnf excludes, the release pin and protected packages.
- **A test chain that cannot write:** a U-Boot build without UFS, a network-disk-only root, and a relay that admits only
  the tablet's USB network address.
- **Recorded checksums** of exactly the tested files, checked again right before each write, and the rule "stop, do not
  improvise" when anything differs.
