# iceland-device

Fedora settings package for the OnePlus Pad 4 (PLAN v4 Phase 4b). Configuration and scripts only: no firmware, no
binaries. `./build-rpm.sh OUT` builds `iceland-device-*.noarch.rpm` (rpmbuild; tested with rpm 4.18).

| File | Installed as | Why |
|---|---|---|
| `80-iceland-kernel.conf` | `/usr/share/dnf5/libdnf.conf.d/` | exclude Fedora's kernels (no Pad 4 support) |
| `sleep-iceland.conf` | `/usr/lib/systemd/sleep.conf.d/60-iceland.conf` | s2idle, the SoC's only sleep state |
| `journald-iceland.conf` | `/usr/lib/systemd/journald.conf.d/60-iceland.conf` | cap the journal at 200 MB |
| `49-iceland-no-system-upgrade.rules` | `/usr/share/polkit-1/rules.d/` | block Fedora version upgrades until tested |
| `iceland-bdaddr(.service)` | `/usr/libexec/iceland/`, systemd unit | apply the tablet's own BT address from `/etc/iceland/bdaddr` (written at install time, never shipped) |
| `iceland-cmdline` | `/usr/libexec/iceland/` | add `clk_ignore_unused pd_ignore_unused regulator_ignore_unused` to all boot entries |
| `90-iceland-dracut.conf` | `/usr/lib/dracut/dracut.conf.d/` | display/touch/GPU drivers + firmware in the initramfs |
| `60-iceland-wifi-powersave.conf` | `/usr/lib/NetworkManager/conf.d/` | Wi-Fi power saving |
| (%posttrans) | `/etc/sysconfig/kernel` | `DEFAULTKERNEL=kernel-iceland`, `UPDATEDEFAULT=yes` |
| (%triggerin fwupd) | `/etc/fwupd/fwupd.conf` | `DisabledPlugins=uefi_capsule` |

Still to add as the hardware work lands: ALSA UCM with volume caps (no speaker playback before TFA9865 protection),
60 Hz on battery, charge limit, lid/keyboard wake tweaks.
