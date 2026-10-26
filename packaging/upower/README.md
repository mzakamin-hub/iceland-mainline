# upower (time to full to the charge limit)

Fedora 44's `upower` 1.91.5-1 with two patches, built as `upower-1.91.5-1.fc44.iceland2` (and `upower-libs`). Current
version on the reference tablet: **1.91.5-1.fc44.iceland2**. iceland2 adds
[`upower-iceland-multi-lid.patch`](upower-iceland-multi-lid.patch): UPower watches every lid switch, not only the first
one it finds (the Pad 4 has the hall sensor's lid and the keyboard cover detector's lid of iceland-device 0.28-42 and
later).

The Pad 4 stops charging at its charge end threshold (85 % by default). UPower 1.91.5 counted the time to full to
100 % (`FIXME: Use charge-stop-threshold here`), so GNOME showed about twice the real time while charging to the limit.
[`upower-iceland-ttf-threshold.patch`](upower-iceland-ttf-threshold.patch) counts it to the end threshold while the
threshold is enabled, gives no time once the threshold is reached, and lets the DisplayDevice keep a single charging
battery's own time to full. UPower's own test suite passes with the patch (97 tests). The patch is written to be sent
upstream as it is.

The time-to-empty side needs no UPower change: kernel q90i reports the battery power at the same nominal voltage as
its energy values (`qcom_battmgr.oplus_power_nominal`), so energy / power equals charge / current.

## Build

On Fedora 44 aarch64: `sudo dnf builddep packaging/upower/upower.spec`, then `packaging/upower/build-rpm.sh OUT`. It
downloads the upstream v1.91.5 tarball (the spec's `Source0`), checks it against `upower-v1.91.5.tar.bz2.sha256` and
builds the RPMs. The spec is Fedora's (rpmautospec-expanded) with the patch line added; its changelog is shortened to
our entry.

## Install

Install `upower` and `upower-libs` together with dnf, then hold them, so that Fedora's updates do not replace them
until a fixed upower reaches Fedora, for example with a file `/etc/dnf/repos.override.d/53-iceland-upower-hold.repo`
that excludes `upower` and `upower-libs` from the Fedora repositories. Restart UPower (`systemctl restart upower`) or
the tablet.
