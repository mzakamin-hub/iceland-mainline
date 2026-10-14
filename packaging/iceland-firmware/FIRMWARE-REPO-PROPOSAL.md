# The dedicated firmware repository `iceland-firmware`: record of its creation

Status 14 Oct 2026: the repository exists and is public: https://github.com/mzakamin-hub/iceland-firmware. Its first
release was 11.A.38-2 (12 Oct 2026, commit c40c33e, tag and release with the noarch RPM and the source RPM; the RPM's
sha256 begins `14833f71`, the package pinned in golden B145). The second, 11.A.38-3 (commit 70ea8f1, RPM sha256 begins
`297669a0`), adds the decoded thermal model. The package's text parts are in this directory (`packaging/iceland-firmware/`)
and in the repository's README.

This document is the record of the decision and of the checks made before the first push. The text below is the
original proposal, kept as the record of the layout.

## Why a separate repository

The owner's rule (11 Oct 2026): the Pad 4's GENERIC firmware files (ADSP, CDSP and SOCCP `.mbn`, GPU, Wi-Fi and Bluetooth,
touch, camera and sensor, VPU) may be published, but only in a dedicated firmware repository or package. Each file's source
and sha256 are recorded, and the vendor notices are kept. Unit-specific data stays private: partition backups, the persist,
modem and EFS carves, calibration and key material, the serial, the MAC and Bluetooth addresses, network names, camera
traces and test media.

The kernel and project repositories keep their blob guards; the firmware files never enter iceland-mainline.

## Layout

    iceland-firmware.spec          the spec (11.A.38-2 onwards: noarch, no scriptlets, sensor tree root:fastrpc)
    MANIFEST.tsv                   path, sha256, bytes, class, stock source (partition:path in 11.A.38), transformation,
                                   notice, comparison with SuperTurtleDev/iceland-mainline-kernel-firmware
    EXCLUDED.tsv                   the unit-specific data that is never packaged
    NOTICE.md, Notice-qca-atheros.txt   vendor notices and the documented byte-exact transformations
    README.md                      the repository's README
    root/usr/lib/firmware/updates/...                 the generic firmware files (about 130 MB; the largest, adsp.mbn,
    root/usr/share/qcom/kaanapali/OnePlus/iceland/... about 41 MB, is below GitHub's 100 MB file limit: no LFS needed)

The files in `root/` were made from the owner's read-only partition backup with the extraction helper, and then checked
against the manifest.

## Checks before the first push

1. `sha256sum -c` of every `root/` file against MANIFEST.tsv; the file count equals the manifest's lines (the spec's
   `%check`).
2. A privacy scan over every file: no sensor registry, no unit-data file names, no MAC-like, Bluetooth or serial strings,
   no network names.
3. The project's serial and Bluetooth-address greps over every file, and a scan for the owner's network names.
4. The comparison with the SuperTurtleDev copy kept as a column (3 equal, 12 older releases or modem copies as of
   d0c0f18 at the time of the proposal).
5. The repository was created by the owner. Then one commit (Signed-off-by), tag `11.A.38-2`, and the RPM and SRPM as
   release assets.

## After it exists

- The device package fetches the package from the repository's releases with an sha256 pin (`iceland-firmware-fetch`,
  pins in `/usr/share/iceland/firmware-pins.tsv`), and fails closed on a mismatch. The local repository
  (`iceland-repo-sync`) carries the package as well.
- A later stock release (for example 11.A.40) needs a new manifest and a release bump. If `gen80200_zap.mbn` or
  `novatek_nt36536_fw.bin` change, the spec must add a posttrans `dracut -f --regenerate-all` (see the spec header).
