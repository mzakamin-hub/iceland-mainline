# Phase 4: Fedora (GNOME) on the OnePlus Pad 4

Target OS (user's decision, 2026-09-28): **Fedora with GNOME**, aarch64. Fedora 44 is the release to use: its
Mesa 26.0.3 carries the first freedreno (OpenGL) support for the Adreno gen8 / a840 of Kaanapali (43 ships 25.2.4).

Everything here runs **from RAM** like the debug kits: nothing is written to the tablet until the user OKs the
install into userdata.

## The RAM workflow (proven in kit pc-024, 2026-09-28)

1. `fetch-fedora.sh [base|workstation|all]` - the official images, verified against Fedora's CHECKSUM files:
   the Container Base Generic OCI image (66 MB; bash, dnf5, curl, no systemd) and the Workstation raw disk image
   (2.9 GB; the install image: DOS label, 500 MB ESP, 2 GB XBOOTLDR, 10.3 GB btrfs root).
2. `make-rootfs.sh IMG OUT MODSTAGE KVER FWDIR MODLIST BUSYBOX LINUX_RAM_DIR` - unpacks the base under fakeroot
   (the OCI layers, or a rootfs tarball handed back by a previous boot), adds `/iceland/` (busybox, the kit's
   report pages, a telnet shell, `init.sh`), our firmware and a stripped subset of our modules (depmod), plus the
   systemd bits used once systemd is in (report/telnet units, NetworkManager keyfile for usb0 at 172.16.42.1,
   sshd enabled with the PC's `~/.ssh/iceland.pub`), and packs `rootfs.cpio.gz` (paths `rootfs/...`).
3. The kit (`tools/linux-ram/build.sh ... ROOTFS_CPIO=rootfs.cpio.gz`) appends it to the busybox initramfs. The
   shim boots as usual (USB NCM network, live kmsg stream, modules, SoCCP) and at `ROOTFS_AT` either
   - `ROOTFS_MODE=chroot` (default): runs the rootfs's `init.sh` in a chroot beside itself (pages on 8080, telnet
     2323, every step logged to the kernel log), or
   - `ROOTFS_MODE=switch`: `switch_root`s into it (systemd as PID 1 when present; the rootfs units restart the
     pages on 80 and telnet on 23).
4. Packages: `PROXY=http://172.16.42.2:3128` points at `tools/relay/usb-proxy.py` on the PC (a tiny CONNECT proxy
   on the USB link); `DNF_PACKAGES="..."` makes `init.sh` run `dnf5 install` through it, in RAM. `KIT_TIME` sets
   the clock (no RTC driver in the kits; TLS needs a sane date). systemd + NetworkManager + openssh-server took 15 s.
5. The kit's page `rootfstar` streams the installed rootfs back to the PC as a tarball; `make-rootfs.sh` takes that
   tarball as the next base, so the installed state persists across RAM boots without touching the tablet.

## The install (later; needs the user's explicit OK)

The Workstation image goes into userdata as a whole-disk image (KNOWLEDGE §6: U-Boot `userdata_blkmap` → EFI boot
manager → shim/GRUB from the ESP), with our kernel, DTB and firmware added to the XBOOTLDR/root partitions (a BLS
entry or a kernel package). Before that: the file-level copy of `/data/vendor` and persist (KNOWLEDGE §13 item 12).
