# Changelog

Mainline Linux for the OnePlus Pad 4 (`iceland`). Newest first. Only released or committed states are listed; the
entries before 26 Nov 2026 (the Fedora releases from 29 Sep to 14 Nov 2026) are in the git history of this file and
on the releases page.

## 2026-11-27 - kernel q92d released with its Arch package

- Kernel q92d (`7.4.0-rc4-iceland-00827`, iceland-linux branch `iceland-7.4-rc4`, tag `q92d`): the kernel the tablet
  runs, released with the signed Arch package `linux-iceland-q92d`, the project's public key, the device tree
  variants and the source ([release](https://github.com/mzakamin-hub/iceland-linux/releases/tag/q92d)); its PKGBUILD is `packaging/arch/linux-iceland` in iceland-linux.
- Charging: the USB-PD 9 V mode was dropped; SuperVOOC (dappermint's driver) is being integrated, not released yet.

## 2026-11-26 - Arch Linux ARM + KDE Plasma 6.8; repository cleanup

- The project's tablet runs Arch Linux ARM with KDE Plasma 6.8 on Wayland, Plasma Login Manager and plasma-keyboard,
  booted ABL -> U-Boot v7 (`boot_b`) -> GRUB -> kernel.
- `packaging/arch`: iceland-device / iceland-device-kde 0.28.53-22 (the cover detector keeps one lid device, so
  closing the cover suspends under KDE; the DroidLoom pacman guard hook is gone, `iceland-droidloom-pacman` stays as
  an optional check), iceland-ppd 1.0-5 (Power Saver, Balanced and Performance on Arch's power-profiles-daemon, all
  within stock's limits), and the PKGBUILDs of the tablet's own builds: iceland-coexist 1.0.9-3, mesa-iceland 26.3.1,
  hexagonrpc, libssc, iio-sensor-proxy-iceland 3.9-14, libcamera-iceland 0.7.2-5, upower-iceland 1.91.5-2,
  networkmanager-p2p 1.58.1-3, qbootctl 0.2.2-1.
- Removed from `main` (kept in the history and the old releases): the Fedora image build, the RPM packaging and its
  CI, the Fedora install guides, the dual-boot guide and tools, the Windows installer, the out-of-tree Gunyah
  modules (the kernel has the drivers), the October status pages and guide set, the finished diagnostics.
- Feature matrix r193: the public list follows Arch Linux ARM + KDE Plasma (105 working features).
- Kernel: q91n (`7.4.0-rc1-iceland-00743`) was the newest release on this date.
