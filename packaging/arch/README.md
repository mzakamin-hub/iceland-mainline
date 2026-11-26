# Arch Linux ARM packaging

PKGBUILDs for the OnePlus Pad 4 port on Arch Linux ARM (aarch64). The project's tablet runs Arch Linux ARM with
KDE Plasma 6.8 on Wayland and Plasma Login Manager with these packages.

- `iceland-device/`: one PKGBUILD, three packages. `iceland-device` holds the device settings (battery guard,
  thermal policy, sound profile, sensors, boot and kernel command line, power-key and bypass handling, nftables,
  the DroidLoom launcher); `iceland-device-kde` the KDE Plasma integration (PowerDevil and
  KWallet defaults, KWin with plasma-keyboard as the input method, the Plasma Login Manager settings and its greeter
  network block, the bypass-charging plasmoid, the Discover hook); `iceland-device-hypr` the Hyprland integration
  (not used on the project's tablet).
- `iceland-ppd/`: the tablet's four tuned power profiles for power-profiles-daemon.
- Archives that the PKGBUILDs build from (the common/, hypr/ and kde/ trees packed as tar files) are not in the
  repository: `SOURCES-NOT-STAGED.txt` lists them with size and sha256, `MAKE-TARS.txt` says how to make them.
- The firmware package lives in the iceland-firmware repository, not here. The kernel, Mesa and sensor-stack
  PKGBUILDs are not published yet.
