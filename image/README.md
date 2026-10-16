# The generic install image

This folder builds the generic install image for the OnePlus Pad 4 ("Fedora Remix for OnePlus Pad 4"). The image
is Fedora 44 Workstation (aarch64) with the project's kernel, device package, firmware and sensor packages. It holds
no data of any one tablet. At its first boot it grows to fill the `userdata` partition, and the setup wizard creates
the first user. Install it with the Windows installer (`tools/installer/`, see `docs/INSTALL-SIMPLE.md`).

## How it is built

The workflow `.github/workflows/build-image.yml` runs only when started by hand, on GitHub's arm64 runner in a privileged
`fedora:44` container. Its inputs are three release tags:

| Input | Release | Files used |
|---|---|---|
| `linux_tag` | [iceland-linux](https://github.com/mzakamin-hub/iceland-linux/releases) | `kernel-iceland-*.aarch64.rpm` |
| `firmware_tag` | [iceland-firmware](https://github.com/mzakamin-hub/iceland-firmware/releases) | `iceland-firmware-*.noarch.rpm` |
| `mainline_tag` | [iceland-mainline](https://github.com/mzakamin-hub/iceland-mainline/releases) | the `iceland-device`, `hexagonrpc`, `libssc`, `iio-sensor-proxy` source rpms |

Every input file must match its line in `kiwi/ci/inputs.sha256`. A file that is not pinned is removed, and a missing or
different file stops the build. To build from new releases, change the pins and `OURS` in `kiwi/mk-kiwi.py` in the same
commit.

`kiwi/build.sh` does the steps in this order. Each step prints one `build:` line, and any FAIL stops the build.

1. `kiwi/tools/build-local-repo.sh`: a local rpm repository with the kernel and firmware as published. The four source
   rpms are rebuilt here.
2. `kiwi-ng system build` with `kiwi/desc/`. `config.kiwi` lists Fedora's packages and ours, plus the layout: ESP,
   `/boot` ext4, and btrfs with the `root`, `home` and `var` subvolumes. `config.sh` holds the distribution settings,
   and `edit_boot_install.sh` fixes up the boot entries.
3. `kiwi/tools/kiwi2golden.py`: converts the disk to the project's image format (partition names, ESP as FAT32 with
   4096-byte blocks).
4. `tools/mk-small.py`: shrinks the disk to its minimum size.
5. `kiwi/tools/image-check.sh` (required): layout, boot entry, device tree, initramfs, package versions, the
   generic-image invariants (no users, keys, machine id, network or Bluetooth state, provisioning stamps), and the
   package set against the reference list `kiwi/desc/b149-packages.json`.
6. `tools/mk-sparse.py`: the Android sparse image that the installer writes to `userdata`.
7. `tools/split-parts.py`: parts below 2 GiB, `SHA256SUMS` and `image-manifest.json`.
8. `tools/privscan.py` (required): the privacy scan of the finished image. In CI it runs the structural checks. The
   byte search for one unit's values (serial, Bluetooth address, network names) needs private reference files. It
   runs on the maintainer's PC before any image is published.

The artifact holds the parts, `image-manifest.json`, `SHA256SUMS`, the check and privacy reports and the build log.
It is kept for 7 days. A release is made from it by hand, after the full privacy scan and a RAM-boot test of that exact
image on a tablet.

## Building on a PC

On an aarch64 Fedora 44 host (or an aarch64 `fedora:44` container under qemu-user, which is slow), as root:

    ICELAND_TOOLS_DIR=$PWD/image/tools ICELAND_IMAGE_TOOLS=$PWD/image/tools \
      bash image/kiwi/build.sh INPUT_DIR OUT_DIR

`INPUT_DIR` holds the release files and `SHA256SUMS.pins` (a copy of `kiwi/ci/inputs.sha256`).

`kiwi/mk-kiwi.py` regenerates `kiwi/desc/config.kiwi`, `packages-b149.txt`, `ours.tsv` and `b149-packages.json` from a
reference install's package manifest (names and versions only). `python3 -I kiwi/mk-kiwi.py --check` compares them.

## The sensor registry

The image's sensor hub registry comes from `iceland-firmware` (11.A.38-4 and later). The project's owner decided it is
generic, the same on every unit. Its files are `%config(noreplace)`, so a registry taken from a tablet's own persist
partition stays in place.
