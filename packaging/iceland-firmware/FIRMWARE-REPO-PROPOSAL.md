# Proposal: the dedicated firmware repository `iceland-firmware` (NOT created yet)

Status 12 Oct 2026: a proposal only. Nothing was created or pushed. This directory (`packaging/iceland-firmware/`)
holds the package's text parts (spec, manifest, exclusions, notices); the firmware files themselves never enter
iceland-mainline (its blob guards stay). Creating the repository and choosing its visibility is the owner's step.

## Why a separate repository

The owner's rule (11 Oct 2026): the Pad 4's GENERIC firmware files (ADSP / CDSP / SOCCP .mbn, GPU, Wi-Fi / BT, touch,
camera / sensor, VPU) may be committed and published, but only in a dedicated firmware repository / package, with each
file's source and sha256 recorded and the vendor notices kept. Unit-specific data stays private (partition backups,
persist / modem / EFS carves, calibration and key material, serial, MAC / BD addresses, SSIDs, camera traces, test media).

## Proposed layout (`mzakamin-hub/iceland-firmware`)

    iceland-firmware.spec          this directory's spec (11.A.38-2: noarch, no scriptlets, sensor tree root:fastrpc)
    MANIFEST.tsv                   path, sha256, bytes, class, stock source (partition:path in 11.A.38), transformation,
                                   notice, comparison with SuperTurtleDev/iceland-mainline-kernel-firmware d0c0f18
    EXCLUDED.tsv                   the unit-specific data that is never packaged
    NOTICE.md, Notice-qca-atheros.txt   vendor notices and the documented byte-exact transformations
    README.md                      this directory's README.md
    root/usr/lib/firmware/updates/...                 the generic firmware files (about 130 MB; largest adsp.mbn ~41 MB,
    root/usr/share/qcom/kaanapali/OnePlus/iceland/... below GitHub's 100 MB file limit: no LFS needed)

Source of `root/`: `~/mainline/build/wf/next-items/priv/a9-src/iceland-firmware-11.A.38/root` (made by
`wf/next-items/a9-firmware/build-rpm.sh` from the owner's read-only partition backup with `iceland-fw-extract`).
Built and tested package: `iceland-firmware-11.A.38-2.fc44.noarch.rpm`, sha256 `14833f719be4...` (pinned in golden
B145; r145 / r145b and r141 FP1-FP4 PASS).

## Checks before the first push (PC, scripted)

1. `sha256sum -c` of every `root/` file against MANIFEST.tsv; file count = manifest lines (the spec's `%check`).
2. `privcheck.py` (wf/next-items/a9-firmware): no sensor registry (`sensors/registry`), no `.iceland-extracted`, no
   bdaddr / MAC / serial / SSID strings, no persist / EFS file names.
3. `owner-wifi-guard.sh` over every file; the serial and BD-address greps of the project guards over every file.
4. Re-run `fwcmp.py` against the SuperTurtleDev copy and keep the comparison column (3 equal, 12 older releases /
   modem copies as of d0c0f18).
5. The repository is created by the owner (visibility: their decision; public is allowed by the 11 Oct rule for these
   generic files). Then one commit (`mzak <mzak.amin@gmail.com>`, Signed-off-by, the Co-Authored-By trailer), tag
   `11.A.38-2`, and the rpm + srpm as release assets.

## After it exists

- iceland-device / the installer may then fetch the package from that repository's releases instead of the local
  repository; until then the PC's local repository (`iceland-repo-sync`) carries it, as in golden B145.
- A later stock release (e.g. 11.A.40) = a new MANIFEST + a release bump; if `gen80200_zap.mbn` or
  `novatek_nt36536_fw.bin` change, the spec must add a posttrans `dracut -f --regenerate-all` (see the spec header).
