# Fedora 44 install plan for the OnePlus Pad 4 (draft; nothing here runs without the user's explicit OK)

Status: the RAM side is proven (kit pc-024: Fedora 44 userland on our kernel, packages installed through the PC,
the installed rootfs handed back, systemd as PID 1 being tested). This is the plan for the real install.

## What goes where

- **userdata (sda15, ~235 GB)** becomes the disk of the Fedora system: a whole-disk image written with `fastboot`
  through U-Boot (the only write the plan needs; U-Boot's fastboot can `flash userdata` in chunks) or with `dd`
  from a RAM-booted Linux. Android's userdata is gone after that (the user decides when; a full backup first).
- Nothing else on the UFS changes: the boot chain stays ABL → **U-Boot in `boot_a`?** No: U-Boot is only RAM-booted
  today. For an installed system U-Boot must live in a boot partition (`boot_a`/`boot_b`, ~100 MB), which is the
  second write. Until then a Fedora install is only reachable through `fastboot boot` of U-Boot from the PC.
- The image layout (the official `Fedora-Workstation-Disk-44-1.7.aarch64.raw.xz`, DOS label):
  1. 500 MB FAT16 ESP (shim + GRUB),
  2. 2 GB "Linux extended boot" (XBOOTLDR: `/boot`, kernels, BLS entries),
  3. 10.3 GB btrfs root (grows to the partition on first boot: `growpart`/Fedora's `systemd-growfs` handle it).

## Boot chain

ABL → U-Boot (`bootcmd=run userdata_blkmap; bootefi bootmgr`, KNOWLEDGE §8) → the EFI boot manager finds the ESP
on the blkmap device → `shimaa64.efi`/`grubaa64.efi` → GRUB reads the BLS entries from XBOOTLDR → our kernel.
U-Boot passes the DTB it loaded (`fdtfile=qcom/kaanapali-oneplus-iceland.dtb`) as the EFI DTB configuration table.

## What the image needs before it boots on the Pad 4

1. **Our kernel** (7.3-rc4 + the iceland queue) in XBOOTLDR: `vmlinuz-<kver>`, `initramfs-<kver>.img` (dracut,
   built on the tablet from RAM or with `dracut --no-hostonly` on the PC), the BLS entry in
   `/boot/loader/entries/`, and the modules in `/usr/lib/modules/<kver>/`. Cleanest: `make binrpm-pkg` → a
   `kernel-*.rpm` installed with dnf (the RAM-boot dnf path already works); simplest first step: files copied in.
2. **Firmware** in `/usr/lib/firmware/`: the manifest files from the tablet's own partitions (`fw-extract.sh`
   covers modem_a/bluetooth_a; the super contents come from the OTA on the PC until super is mapped) plus the
   audio topology and the converted touch firmware (repo `firmware/`).
3. **Fedora-side config**: the kernel command line (`clk_ignore_unused pd_ignore_unused regulator_ignore_unused`
   until the DT/drivers are complete; `console=tty0`), `local-bd-address` or a `btmgmt` unit for the BT address,
   the ALSA UCM volume cap (no speaker playback before the TFA9865 protection), `ath12k` loaded late.
4. **GPU**: Mesa 26.0.3 (Fedora 44) has the freedreno a840 support; GNOME falls back to llvmpipe if it fails.

## Before any write (user's OK required, then in this order)

1. File-level copy of Android's `/data/vendor` and persist (TEE files, calibration) from LineageOS with adb root
   (read-only; KNOWLEDGE §12).
2. A raw backup of userdata? Pointless (FBE-encrypted); the file-level copy above is what matters.
3. Write the image to userdata (U-Boot fastboot `flash userdata` from the PC, chunked), never touching the other
   partitions.
4. Boot it through `fastboot boot` of U-Boot first; only when it works, consider putting U-Boot into `boot_b`
   (slot b currently runs LineageOS) or `boot_a`.

## Open questions

- Chunked `fastboot flash` of a 12 GB (sparse) image through U-Boot: U-Boot's fastboot supports sparse images;
  the 256 MiB buffer means many chunks; test on the PC's image tooling first.
- Does the Fedora ESP's shim/GRUB boot from U-Boot's EFI? (OnePlus 15/pmOS used systemd-boot; GRUB should work.)
- The btrfs root: first-boot growth and `fstab` UUIDs are the image's own, unchanged.
