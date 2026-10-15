# Index: where to find what

The kernel is Linux 7.3-rc7 with the Pad 4 patch queue (current versions in `docs/RELEASE-NOTES.md`). Fedora 44 GNOME
installs on the tablet with two writes: U-Boot's install build in `boot_b`, the Fedora disk image in `userdata`
(`docs/INSTALL-GUIDE.md`). The working features are listed in `docs/FEATURES.md`.

## The guide

| File | Content |
|---|---|
| `01-OVERVIEW.md` | the project, what works, the safety principles |
| `02-HARDWARE.md` | SoC and board block by block with driver source and proof; PMICs, rails, thermal design; RAM / UFS; the partition layout; firmware sources; `efisp`; built-in vs modules |
| `03-BOOT-AND-PARTITIONS.md` | stock boot chain, A/B, AVB; the RAM boot; the installed chain; testing the image from RAM; unbrickable / restorable |
| `04-BUILD-YOUR-OWN.md` | step-by-step: the four repositories, `prepare.sh` and `build.sh` for the kernel and for U-Boot, firmware (read-only), the sensor and device packages, logs |
| `05-PORTING-TO-OTHER-DISTROS.md` | Debian in detail, Arch and postmarketOS-style in brief, what is Fedora-specific |
| `07-INSTALL-REVIEW.md` | the install's risks and how the design handles them |
| `GLOSSARY.md` | terms (A/B slots, boot_b, AVB footer, qbootctl, loop root, golden, rehearsal, queue, and others) |

## The install

| File | Content |
|---|---|
| `docs/INSTALL-GUIDE.md` | what the install consists of, the requirements, the steps, what works afterwards, the way back |
| `docs/INSTALL-PLAN.md` | the design: partitions, image layout, verified boot and the slot counter, seat belts, updates, ways back |

## Other repositories

| Repository | Holds |
|---|---|
| `iceland-linux` | the kernel patch queue (`patches/0001-infiniti`, `patches/0002-iceland`), `kernel.pin`, `scripts/prepare.sh` and `scripts/build.sh`, `packaging/fedora/` (`kernel-iceland`), one note per queue in `docs/` |
| `iceland-u-boot` | the U-Boot patch series (`patches/0001-infiniti` 14, `patches/0002-iceland` 12, the install build in 0004-0012), `uboot.pin`, `scripts/prepare.sh` and `scripts/build.sh`, `tools/install/` (the build record and checksums of the install build v3) |
| `iceland-mainline` | this documentation, `docs/FEATURES.md` and `docs/features/` (the matrix), `packaging/iceland-device/`, `packaging/sensors/`, `phase4/` (the Fedora images and the RAM root), `audio/`, `firmware/` (the manifest and the NT36536 converter), `tools/dualboot/` |
| `iceland-firmware` | the generic firmware package (11.A.38-3), `MANIFEST.tsv` (path, sha256, source), `EXCLUDED.tsv` (unit data, never packaged), the notices |

## Quick answers

| Question | Look at |
|---|---|
| Does feature X work? | `docs/FEATURES.md` |
| Which patch does Y? | `iceland-linux/patches/0002-iceland/`, and the queue notes in `iceland-linux/docs/` |
| How do I install Fedora? | `docs/INSTALL-GUIDE.md` |
| How do I build it myself? | `04-BUILD-YOUR-OWN.md` |
| How do I get back to stock? | `docs/INSTALL-GUIDE.md` section 8 (dry-run only, never executed) |
| Which partitions may be written? | `docs/INSTALL-PLAN.md` section 2; `02-HARDWARE.md` section 6 |
| What is the risk of a step? | `07-INSTALL-REVIEW.md`, `01-OVERVIEW.md` and `03-BOOT-AND-PARTITIONS.md` |
