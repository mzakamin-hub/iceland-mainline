# Arch Linux ARM packaging

PKGBUILDs for the OnePlus Pad 4 port on Arch Linux ARM (aarch64). The project's tablet runs Arch Linux ARM with
KDE Plasma 6.8 on Wayland and Plasma Login Manager with these packages.

Device and boot:

- `iceland-device/`: one PKGBUILD, three packages. `iceland-device` holds the device settings (battery guard,
  thermal policy, sound profile, sensors, boot and kernel command line, power-key and bypass handling, nftables,
  the DroidLoom launcher); `iceland-device-kde` the KDE Plasma integration (PowerDevil and
  KWallet defaults, KWin with plasma-keyboard as the input method, the Plasma Login Manager settings and its greeter
  network block, the bypass-charging plasmoid, the Discover hook); `iceland-device-hypr` the Hyprland integration
  (not used on the project's tablet).
- `iceland-ppd/`: the tablet's power profiles for power-profiles-daemon (Power Saver, Balanced, Performance, all
  within stock's limits).
- `iceland-coexist/`: the kernel-install plugins and pacman hooks that put each `linux-iceland` kernel, its
  initramfs and device tree into `/bootfs/<system>/` with its own GRUB (BLS) entry, without changing the default
  entry; `iceland-oneshot` boots a new entry once.
- `qbootctl/`: the A/B slot tool (`iceland-slot-mark` uses it to mark the boot slot successful).

Graphics, sensors, camera, power, network (each replaces the Arch Linux ARM package of the same base name through
`provides` / `conflicts`):

- `mesa-iceland/`: Mesa 26.3.1 (git 6cd33b7) with the Adreno 840 turnip / ir3 / freedreno patches 9101-9142;
  packages `mesa-iceland`, `vulkan-freedreno-iceland`, `vulkan-swrast-iceland`, `vulkan-virtio-iceland`,
  `opencl-mesa-iceland`.
- `hexagonrpc/`, `libssc/`, `iio-sensor-proxy-iceland/`: the sensor-hub stack (FastRPC daemon, the SSC client
  library with the hall sensor, iio-sensor-proxy with the ssc patches).
- `libcamera-iceland/`: libcamera 0.7.2 with the autofocus patches and the GPU soft ISP.
- `upower-iceland/`: UPower 1.91.5 with every lid switch and the time-to-full to the charge limit.
- `networkmanager-p2p/`: NetworkManager 1.58.1 with an opt-in option that keeps Wi-Fi P2P groups other clients
  started (used by DexHid) and two nm-1-58 scan backports.

Sources that are archives or release tarballs are not in the repository: each package's `SOURCES-NOT-STAGED.txt`
lists them with size and sha256 (for `iceland-device`, `MAKE-TARS.txt` says how to make its three tar files).

Not here: the firmware package (repository
[iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware)), the kernel (repository
[iceland-linux](https://github.com/mzakamin-hub/iceland-linux)), the VM packages
([iceland-gvm](https://github.com/mzakamin-hub/iceland-gvm), [iceland-vms](https://github.com/mzakamin-hub/iceland-vms))
and DroidLoom (its upstream pacman repository). The `linux-iceland` PKGBUILD is not published yet.

Build them in an Arch Linux ARM aarch64 environment (a container under qemu-user on a PC works) with `makepkg`, sign
the packages and the repository database with your own key (`makepkg --sign`, `repo-add -s`), and serve them as a
local pacman repository; the top-level README's guide has the steps.
