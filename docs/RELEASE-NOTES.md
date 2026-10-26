# OnePlus Pad 4 - Fedora 44 GNOME: release notes

The working features, one by one, are listed in [FEATURES.md](FEATURES.md); the install is described in
[INSTALL-GUIDE.md](INSTALL-GUIDE.md). The dated history is in [../CHANGELOG.md](../CHANGELOG.md).

## 1. Current versions (25 Oct 2026)

| Piece | Version |
|---|---|
| Kernel | `7.3.0-next-20261020-iceland-00548` (queue q90u): linux-next `next-20261020` (Linux 7.3 plus the trees queued for 7.4) plus the Pad 4 patch queue, iceland-linux branch `iceland-7.3-rc7-next`, tag `q90u`; package `kernel-iceland`, updated with dnf (release download: q90u) |
| Device package | `iceland-device` 0.28-40 with `iceland-device-kde` (KDE Plasma integration); `iceland-coexist` 1.0-7 (kernel-install for the shared `/boot`, one-shot boot entries) |
| Multimedia and GPU builds | Mesa 26.3.0-rc1 snapshot with seven A840 patches; libcamera 0.7.1 with autofocus; ffmpeg-free 8.1.3 with V4L2 decoding; gst-plugins-good 1.28.8 with the V4L2 colorimetry fix (specs and patches in `packaging/`) |
| Virtual machines | `iceland-gvm` 0.3-49 (crosvm for Gunyah, the guest kernel, `gvm.sh`) and `iceland-vms` 0.2-17 (the Virtual Machines app), released with RPMs; sources in [iceland-gvm](https://github.com/mzakamin-hub/iceland-gvm) and [iceland-vms](https://github.com/mzakamin-hub/iceland-vms) |
| Android apps | DroidLoom (Android 17 in a container): host packages 0.1.0-23.git9789467.iceland3, image iceland4, `iceland-droidloom` 1.0-3 (packaging in [iceland-droidloom](https://github.com/mzakamin-hub/iceland-droidloom)) |
| Power service | `upower` 1.91.5-1.fc44.iceland1 (time to full to the charge limit) |
| Sensor programs | `iio-sensor-proxy` 3.9-11.iceland1, `hexagonrpc`, `libssc` |
| Firmware | `iceland-firmware` 11.A.38-6 (the generic stock firmware, sha256-pinned, with the decoded thermal model, the sensor hub registry and two GPU firmware pairs: stock's and the vendor's) |
| libcamera | Fedora's 0.7.1-2 |
| U-Boot | install build v7 (patches 0001-0015), with the power-on boot menu (BlissROM as well on the dual-boot layout); written to `boot_b` with an AVB footer |
| Fedora | release 44 with the stable updates; GNOME Shell 50 (the install image) or KDE Plasma 6.7 (the project's tablet since 24 Oct); Mesa 26.3 (a build for the tablet) |

## 2. The install image (13 Oct 2026)

The first install image was built from Fedora-Workstation-Disk-44 (aarch64), re-laid for the tablet's 4 KiB storage
blocks, with 1,727 packages: kernel q89g (`7.3.0-rc7-iceland-00426`), `iceland-device` 0.28-7, `iceland-firmware`
11.A.38-3, Fedora's libcamera 0.7.1-2, and the U-Boot install build v3. It passed its RAM tests (the acceptance list and
the update and rollback paths) and an offline content check of the image before it was written.

Since then the tablet is updated with dnf (kernel, device package, sensor programs), and U-Boot v4 replaced v3.

**Slot marking:** `iceland-device` 0.28-7 does not mark the boot slot on the installed layout (its guard refused the
root on a loop device); ABL's retry count then goes down at every power-on. 0.28-8 and newer fix this. An install image
should carry 0.28-8 or newer (see the install guide, section 6).

## 3. What changed since release candidate 1 (3 Oct 2026)

- **Kernel:** rebased on Linux v7.3-rc7 (the iris colour fix is in); the panel's brightness limit through the kernel
  (the backlight driver's cooling device, one state per stock gear; GNOME's slider keeps the user's value); the UFS
  scheduler change no longer fails on the busy tag set; the rear lens held at stock's start position while the camera
  streams; the USB controller and the Wi-Fi root port are no longer wake sources; the idle refresh compiled in, off by
  default. Later queues (q89h to q89k) describe the charge pumps, keep the GPU's GMU alive, register the pogo keyboard
  backlight and carry upstream display, Wi-Fi and USB-C fixes.
- **Sound:** the speakers run through a protection chain (150 Hz high-pass, compressor with +9 dB make-up, limiter at
  -1 dBFS). The microphones: an echo canceller, then a +14 dB limiter, with stock's decimator setting (84); the raw
  source is named "(raw)".
- **Wi-Fi:** the firmware's 802.11d scan is off by default, which fixes the drops after a reconnect.
- **Bluetooth:** the address helper v2, and the firmware baud-change fix in the kernel: no more "Frame reassembly
  failed" at power-on.
- **Thermal:** stock's skin-temperature policy (60 / 61 / 70 C); the brightness limit through the kernel; stock's
  screen-off table and input boost ceiling (0.28-8).
- **Camera:** libcamera 0.7.1-2 from Fedora stops the camera stream without the WirePlumber abort (40 of 40 cycles).
- **Updates and firmware:** minimal Fedora holds (GRUB, shim, Fedora's firmware and libcamera update from Fedora; the
  sensor programs and `alsa-ucm` are held); `iceland-firmware-fetch` with sha256 pins; the firmware repository is
  public.
- **Slot marking:** the Fedora-side marking works on the installed layout (0.28-8).
- **Since 15 Oct** (kernels q89l to q89w, `iceland-device` 0.28-17 to 0.28-29; details in
  [../CHANGELOG.md](../CHANGELOG.md)): the battery energy at the cell's nominal voltage; the vendor GPU firmware with
  GPU preemption; the dual boot BlissROM + Fedora (U-Boot v7); the own Bluetooth address at every start; a change
  between 120 and 60 Hz without a modeset and a screen off without an underrun; suspend-to-idle as the kernel's
  default; the refresh switch acting only on real power changes; the memory-latency governor loaded at boot.
- **Since 20 Oct** (kernels q89x to q90i, `iceland-device` 0.28-30 to 0.28-32; details in
  [../CHANGELOG.md](../CHANGELOG.md)): the patch queue on the 7.4 base (linux-next `next-20261020`); no display
  glitches with auto-rotate on; a GPU hang recovers without hanging the system; the GPU's current limiter (CLX) on;
  idle refresh at 30 Hz on a static screen; automatic brightness on by default; TRIM through device-mapper; right
  battery time estimates (kernel power at the nominal voltage, upower's time to full to the charge limit); the memlat
  poll off; a kernel config round (VA_BITS 48, HZ 250, PREEMPT_DYNAMIC).
- **Since 22 Oct** (kernels q90j to q90r): protected virtual machines on Gunyah with 3D in the guest and the
  Virtual Machines app (iceland-gvm 0.3-27, iceland-vms 0.2-5); Android apps through DroidLoom (the C binder driver
  is back in the kernel); KDE Plasma 6 as the desktop of the project's tablet; the board's command line as built-in
  kernel defaults; drm/msm's October fixes and other upstream fixes.
- **Since 25 Oct** (kernels q90s to q90u): USB-C cable changes during sleep are seen on resume; Gunyah guest memory
  is never freed while it may still be lent; UFS and inline-crypto runtime-PM fixes. The VM release iceland-gvm
  0.3-49 / iceland-vms 0.2-17: Windows 11 ARM guests in the app (Remote Desktop, ssh), touch input modes,
  fullscreen, a VNC display, vhost-net networking on by default, 2 MiB guest pages and io_uring disks.

## 4. Known limits

- The camera into the hardware H.264 encoder (`pipewiresrc` -> `v4l2h264enc`) does not negotiate; screen recording on
  the hardware encoder works.
- Chromium / Electron apps do not use the GPU path yet.
- No fast charging (SuperVOOC is not supported); USB-PD charging and the normal charger types work.
- Windows guests are shut down from inside Windows or with Force Off (the app's clean Shut Down is not supported
  yet); ISO installs are not supported yet; no camera
  autofocus, no DSP protection inside the amplifiers (a PipeWire speaker-protection chain is used).
- Fedora 45 stays blocked until it has been tested on the tablet.
