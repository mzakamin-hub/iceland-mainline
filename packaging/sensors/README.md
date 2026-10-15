# The sensor programs for the OnePlus Pad 4

The Pad 4's accelerometer (auto-rotate), light, proximity and compass sensors sit behind the ADSP's sensor hub
(Qualcomm SSC). Three programs reach them. None of them is packaged by Fedora 44 as it is, so they are built here and
held from Fedora's updates:

| Package | Upstream | Fedora 44 | What is packaged here |
|---|---|---|---|
| `hexagonrpc` | github.com/linux-msm/hexagonrpc `598b591` (v0.5.0 + 19) | not packaged | + `docs/sensors/patches/hexagonrpc/0001` (serves `/odm/etc/sensor`) and `0002` (answers an unsupported call with its error and keeps serving; the sensors PD's apps_std method 36 ended the daemon once per boot), units in the systemd unit directory, user `fastrpc`, a udev rule for the nodes |
| `libssc` (+ `-devel`) | codeberg.org/DylanVanAssche/libssc `54dd13e` (v0.4.4 + 8) | not packaged | as upstream, without the test and mocking subdirectories; `ssccli` in the main package |
| `iio-sensor-proxy` | gitlab.freedesktop.org/hadess/iio-sensor-proxy `3.9` | 3.8, no SSC support | built with `-Dssc-support=enabled`, + `docs/sensors/patches/iio-sensor-proxy/0001` (poll sensors claimed during discovery) and `0002` (HasAccelerometer is held back until a client has claimed it, or for 2 s after it looked; works around mutter 50 not claiming the sensor after a boot in touch mode, and keeps auto-rotate across a daemon restart) |

The device side (the udev rule with the mount matrix, the unit drop-ins, the readiness wait, and the restart after a
suspend) is in [`packaging/iceland-device`](../iceland-device/), which requires these three packages.

## Build

`build-rpm.sh` in this directory builds the RPMs from the pinned upstream commits and the patches above. The build
runs on Fedora 44 aarch64:

    dnf install rpm-build gcc meson ninja-build glib2-devel libqmi-devel protobuf-c-devel protobuf-c-compiler \
        protobuf-compiler gobject-introspection-devel libgudev-devel polkit-devel systemd-devel systemd-rpm-macros
    bash build-rpm.sh <source tree> <output folder>

The order matters: `libssc` and `libssc-devel` are installed before `iio-sensor-proxy` is built.

## Status and open points

- On the installed system the three programs run and the accelerometer feeds auto-rotate. The sensor stream stops across
  a suspend; a resume unit restarts the programs (added in iceland-device 0.28-3, tested 3 of 3 in a RAM kit).
- SELinux runs in enforcing mode on the installed system. A small policy module, `iceland_sensors`, lets iio-sensor-proxy
  use the QRTR socket of the sensor hub.
- hexagonrpcd runs as root on the Pad 4 (the drop-in in the device package): the sensor hub writes below its registry
  directory, and the ownership for the `fastrpc` user is still open.
- The tablet's own DSP file tree (`/usr/share/qcom/kaanapali/OnePlus/iceland`) is unit data. It is extracted from the
  tablet at install time and is not published.
- Patch 0002 is a workaround for a mutter bug (`update_panel_orientation_managed()` uninhibits the orientation tracking
  before anything inhibited it). It can go once mutter is fixed.
