# Phase 4: Fedora 44 GNOME on the OnePlus Pad 4

Target OS: **Fedora 44 with GNOME**, aarch64. Fedora 44's Mesa (26.x) carries the
freedreno (OpenGL) support for the Adreno 840 of Kaanapali; Fedora 43's Mesa (25.2.4) did not.

Phase 4 is done: Fedora 44 GNOME was installed on the tablet on 13 Oct 2026 (see [../docs/INSTALL-GUIDE.md](../docs/INSTALL-GUIDE.md)).
This directory keeps the scripts that built the Fedora image and its rootfs for the RAM rehearsals and the install.

## Scripts

- `fetch-fedora.sh [base|workstation|all]`: downloads the official Fedora images and verifies them against Fedora's
  CHECKSUM files. The Workstation raw disk image is the install base (a DOS label, a 500 MB ESP, a 2 GB boot partition and
  a btrfs root); the Container Base OCI image is used for the early rootfs builds.
- `make-rootfs.sh IMG OUT MODSTAGE KVER FWDIR MODLIST BUSYBOX LINUX_RAM_DIR`: unpacks a base under fakeroot, adds the
  Pad 4 modules and firmware, and packs a rootfs image. It takes a rootfs tarball from an earlier run as the next base.
- `rootfs-post-wayland.sh`: a test script for the Wayland session (seatd, cage, glmark2-es2-wayland) used in the early
  RAM sessions.

## Lessons from the RAM sessions

- A rootfs grown from the Container Base image lacks `systemd-pam` and `dbus-daemon`. Without them logind opens no
  session, and gdm fails with "Session never registered". Install both before gdm.
- The lean GNOME set that worked: `gdm gnome-shell gnome-session-wayland-session gnome-settings-daemon
  xorg-x11-server-Xwayland ptyxis nautilus gnome-backgrounds dejavu-sans-fonts google-noto-sans-fonts systemd-pam
  dbus-daemon`, a user in `wheel,video,render,input`, and automatic login for the test user in the rehearsal image only.
- The GPU needs the Kaanapali gen8 firmware set from linux-firmware, plus the Pad 4's own signed zap shader. The zap
  shader comes from the tablet's own firmware and is never published (it is part of the firmware manifest, see
  [../firmware/README.md](../firmware/README.md)).
- Anything that watches stdin (kmscube, cage) needs a silent stdin, not a closed one.

## The install

The install image is the Fedora Workstation disk image, re-laid for the tablet's 4 KiB storage blocks, with the Pad 4
packages added (`kernel-iceland`, `iceland-device`, `iceland-firmware`, the sensor programs and Fedora's libcamera).
It is written into `userdata` after its RAM tests (see [../docs/INSTALL-GUIDE.md](../docs/INSTALL-GUIDE.md)). No image is
published: each one carries its tablet's own firmware extraction and Bluetooth address.
