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
   - `ROOTFS_MODE=pid1` (**the mode to use**): bind-mounts `/rootfs` on itself and `exec chroot`s the rootfs's
     systemd as PID 1; the initramfs stays the real root, so the shim's pages (80), live stream, watchdog and
     auto-reboot keep working; the rootfs units run the report pages on 8080 and telnet on 2323 (pc-024 Y7);
   - `ROOTFS_MODE=chroot` (default): runs the rootfs's `init.sh` in a chroot beside the shim (no systemd);
   - `ROOTFS_MODE=switch`: `switch_root` - **never**: the shim's safety jobs lose their tools and the tablet
     resets ~45 s later (pc-024 Y1/Y5).
4. Packages: `PROXY=http://172.16.42.2:3128` points at `tools/relay/usb-proxy.py` on the PC (a tiny CONNECT proxy
   on the USB link); `DNF_PACKAGES="..."` makes `iceland-dnf.service` (or `init.sh`) run `dnf5 install` through
   it, in RAM (`KIT_TIME` sets the clock: the PMIC RTC reads 1970 and TLS needs a sane date). systemd +
   NetworkManager + openssh-server took 15 s; sshd answers `an/fedora-ssh.sh` (key `~/.ssh/iceland`, never
   committed) ~45 s after the boot. The unit then runs a kmscube check on the MSM DRM device and, when the kit
   carries one (`build.sh EXTRA_ETC rootfs-post.sh`, `make-kit24.sh POST_SCRIPT=`), the test script
   `/iceland/post.sh` (`rootfs-post-wayland.sh`: seatd + cage + glmark2-es2-wayland). Anything that watches
   stdin (kmscube, cage) needs a silent stdin from a process substitution (`< <(sleep 600)`), not a closed one
   and not a pipeline.
5. The kit's page `rootfstar` streams the installed rootfs back to the PC as a tarball; `make-rootfs.sh` takes that
   tarball as the next base, so the installed state persists across RAM boots without touching the tablet.
6. GPU: the kit's DTB must keep `gpu@3d00000` enabled (`make-kit24.sh` `SOC` list) and the initramfs must carry
   `qcom/gen80200_{sqe.fw,gmu.bin,aqe.fw}` from linux-firmware (the Kaanapali gen8 set) plus the tablet's own
   signed `qcom/kaanapali/iceland/gen80200_zap.mbn` (read from its `/vendor/firmware`; never committed). Then
   Mesa's freedreno drives the Adreno 840: GLES 3.2, 120 fps vsync-locked in kmscube (pc-024 Y8/Y9).
7. Big rootfs (a desktop): `ROOTFS_URL=http://172.16.42.2:8000/<file>.tar.gz` makes the shim fetch the tarball at
   boot from `python -m http.server 8000 --directory C:\platform-tools\rootfs-serve` on the PC (U-Boot's 256 MiB
   fastboot buffer caps the boot image); a tarball handed back by `rootfstar` already contains `/iceland`, the
   modules and the units, so it boots as it is.
8. The relay runner's `-Wait N` ends the session (late pages, then the reboot), not the kit's `AUTOREBOOT_AT`:
   use `-Wait 1700` with `AUTOREBOOT_AT=1800` for a long session driven over ssh.
9. GNOME (pc-024 Y9): a rootfs grown from the Container Base image lacks **`systemd-pam`** (pam_systemd) and
   `dbus-daemon`; without them logind opens no session, no `user@UID` manager and no session bus exist, and gdm
   fails with "Unable to run session message bus" / "Session never registered". Install both before gdm. The
   lean GNOME set that works: `gdm gnome-shell gnome-session-wayland-session gnome-settings-daemon
   xorg-x11-server-Xwayland ptyxis nautilus gnome-backgrounds dejavu-sans-fonts google-noto-sans-fonts
   systemd-pam dbus-daemon` (~460 packages, 360 MiB), a user in `wheel,video,render,input` and
   `/etc/gdm/custom.conf` with `AutomaticLoginEnable=True` / `AutomaticLogin=<user>`; `rootfs-gnome.tar.gz` on
   the PC is that tree.

## The install (later; needs the user's explicit OK)

The Workstation image goes into userdata as a whole-disk image (KNOWLEDGE §6: U-Boot `userdata_blkmap` → EFI boot
manager → shim/GRUB from the ESP), with our kernel, DTB and firmware added to the XBOOTLDR/root partitions (a BLS
entry or a kernel package). Before that: the file-level copy of `/data/vendor` and persist (KNOWLEDGE §13 item 12).
