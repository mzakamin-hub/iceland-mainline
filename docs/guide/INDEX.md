# Index: where to find what

Status (14 Oct 2026): the kernel queue head is `q89g` (Linux 7.3-rc7). Fedora 44 GNOME was installed on the owner's
tablet on 13 Oct 2026 (install build v3 in `boot_b`, the Fedora disk image in `userdata`). The device package is
`iceland-device` 0.28-8 and the firmware package is `iceland-firmware` 11.A.38-3. The feature matrix is page v62
(104 rows: 83 ok, 13 part, 5 todo, 3 out). The chapters 04 and 05, this index and the glossary describe this state.
The other files are dated; their dates are in their titles and first lines.

## The guide

| File | Content |
|---|---|
| `01-OVERVIEW.md` | the project, what works, what does not, the safety principles |
| `02-HARDWARE.md` | SoC and board block by block with driver source and proof; PMICs, rails, thermal design; RAM / UFS; the partition layout; firmware sources; `efisp`; built-in vs modules |
| `03-BOOT-AND-PARTITIONS.md` | stock boot chain, A/B, AVB; the RAM boot; the install chain as installed; the rehearsal; unbrickable / restorable |
| `04-BUILD-YOUR-OWN.md` | step-by-step: the four repositories, `prepare.sh` and `build.sh` for the kernel and for U-Boot, firmware (read-only), the sensor and device packages, logs |
| `05-PORTING-TO-OTHER-DISTROS.md` | Debian in detail, Arch and postmarketOS-style in brief, what is Fedora-specific |
| `06-PROCESS-HISTORY.md` | timeline, method, key findings, lessons, evidence map |
| `07-INSTALL-REVIEW.md` | independent review of the install: findings, consistency, recovery gaps, questions |
| `GLOSSARY.md` | terms (A/B slots, boot_b, AVB footer, qbootctl, loop root, golden, rehearsal, queue, q89g, and others) |
| `PLAN.md` | the plan of the document set (audiences, outlines, sources), dated |
| `RESUME-2026-10-02.md` | the resume page of 2 Oct 2026 22:30 (historic; the team plan `docs/TEAM-PLAN.md` and the ledger took over on 3 Oct) |
| `RC1-NOTES.md` | release candidate 1 (3 Oct 2026): what each run proved, the known issues (F43 Wi-Fi, F44 Camera app) and the owner's checks |
| `LOOP3-NOTES.md`, `LOOP4-NOTES.md`, `LOOP5-NOTES.md` | the notes of the three development loops (3-13 Oct 2026); dated |
| `FINAL-REPORT.md` | a dated report of the earlier build work (read its first lines for its date and scope) |

## Tools (generators of the RC1 documents)

| File | Content |
|---|---|
| `tools/known_issues.py` | builds the known-issues tables (F1-F24 and the fixes of the night of 2-3 Oct) from the team's records; the records are in private build folders, so it prints the built-in tables only here |
| `tools/mk-release-notes.py` | writes the RC1 release notes (`RELEASE-NOTES.md` is the published copy) |
| `tools/mk-final-docs.py` | writes the final-build editions of the install documents from the install workflow's texts (private inputs) |

These scripts read private build folders and cannot run from this repository. They are kept as the record of how the
RC1 documents were made.

## Other repositories

| Repository | Holds |
|---|---|
| `iceland-linux` | the kernel patch queue (tag `q89g`; `patches/0001-infiniti` 132, `patches/0002-iceland` 294), `kernel.pin`, `scripts/prepare.sh` and `scripts/build.sh`, `packaging/fedora/` (`kernel-iceland`) |
| `iceland-u-boot` | the U-Boot patch series (`patches/0001-infiniti` 14, `patches/0002-iceland` 10, the install build v3 in 0004-0010), `uboot.pin`, `scripts/prepare.sh` and `scripts/build.sh`, `tools/install/` (the build record and checksums of the install build) |
| `iceland-mainline` | this documentation, `docs/FEATURES.md` and `docs/features/` (the matrix), `packaging/iceland-device/`, `packaging/sensors/`, `phase4/` (the Fedora images and the RAM root), `audio/`, `firmware/` (the manifest and the NT36536 converter), `tools/dualboot/` |
| `iceland-firmware` | the generic firmware package (11.A.38-3), `MANIFEST.tsv` (path, sha256, source), `EXCLUDED.tsv` (unit data, never packaged), the notices |

## Quick answers

| Question | Look at |
|---|---|
| Does feature X work, and how was it proven? | `docs/FEATURES.md` (the matrix; row notes name the run) |
| Which patch does Y? | `iceland-linux/patches/0002-iceland/`, and `docs/guide/RC1-NOTES.md` or `docs/Q89G-QUEUE.md` in `iceland-linux` |
| What is the state of the install? | this index's status line, `07-INSTALL-REVIEW.md`, and `docs/INSTALL-GUIDE.md` |
| How do I build it myself? | `04-BUILD-YOUR-OWN.md` |
| How do I get back to stock? | the return-to-stock plan in `docs/INSTALL-GUIDE.md` (not run) |
| Which partitions may be written? | `docs/INSTALL-PLAN.md` section 2; `02-HARDWARE.md` section 6 |
| What is the risk of a step? | `01-OVERVIEW.md` and `03-BOOT-AND-PARTITIONS.md` |
