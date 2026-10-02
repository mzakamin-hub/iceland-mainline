# The sensor programs for the OnePlus Pad 4

The Pad 4's accelerometer (auto-rotate), light, proximity and compass sensors sit behind the ADSP's sensor hub
(Qualcomm SSC). Three programs reach them; none of them is usable from Fedora 44 as it is:

| Package | Upstream | Fedora 44 | What is packaged here |
|---|---|---|---|
| `hexagonrpc` | github.com/linux-msm/hexagonrpc `598b591` (v0.5.0 + 19) | not packaged | + `docs/sensors/patches/hexagonrpc/0001` (serves `/odm/etc/sensor`), units in the systemd unit directory, user `fastrpc`, a udev rule for the nodes |
| `libssc` (+ `-devel`) | codeberg.org/DylanVanAssche/libssc `54dd13e` (v0.4.4 + 8) | not packaged | as upstream, without the test / mocking subdirectories; `ssccli` in the main package |
| `iio-sensor-proxy` | gitlab.freedesktop.org/hadess/iio-sensor-proxy `3.9` | 3.8, no SSC support | built with `-Dssc-support=enabled` + `docs/sensors/patches/iio-sensor-proxy/0001` (poll sensors claimed during discovery) and `0002` (HasAccelerometer is held back until the client has claimed, or for 2 s after it looked: works around mutter 50 never claiming after a boot in touch mode, and keeps auto-rotate across a daemon restart) |

The device side (udev rule with the mount matrix, unit drop-ins, readiness wait, restart after a suspend) is in
`packaging/iceland-device` (0.15 and later), which requires these three.

## Build

`build/mk-sensor-pkg.sh` (PC) makes the source tarballs from the pinned upstream commits and bundles them with the
specs and patches as `sensors-pkg.tgz`. On Fedora 44 aarch64 (the tablet's RAM session):

    dnf install rpm-build gcc meson ninja-build glib2-devel libqmi-devel protobuf-c-devel protobuf-c-compiler \
        protobuf-compiler gobject-introspection-devel libgudev-devel polkit-devel systemd-devel systemd-rpm-macros
    tar -xzf sensors-pkg.tgz && bash sensors-pkg/build-rpm.sh sensors-pkg OUT

The order matters: `libssc` and `libssc-devel` are installed before `iio-sensor-proxy` is built.

## Open

- hexagonrpcd still runs as root on the Pad 4 (drop-in in iceland-device): the sensor hub writes below its
  registry directory; the `fastrpc` user needs that directory's ownership settled at install time.
- The tablet's own DSP file tree (`/usr/share/qcom/kaanapali/OnePlus/iceland`) is private and is extracted at
  install time; the extractor is not written yet.
- Patch 0002 is a workaround for a mutter bug (`update_panel_orientation_managed()` uninhibits the orientation
  tracking before anything inhibited it); it should go once mutter is fixed.
- SELinux: not tested in enforcing mode (the RAM sessions run permissive).
